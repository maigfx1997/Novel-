from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from ebooklib import epub
import os
import re
import uuid
from urllib.parse import urljoin
import concurrent.futures

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
CORS(app)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8'
}

def clean_text(text):
    if not text: return ""
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text).strip()

def fetch_resource(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=5)
        if res.status_code == 200:
            return res.content
    except:
        pass
    return None

def scrape_universal_metadata(url):
    res = requests.get(url, headers=HEADERS, timeout=10)
    if res.status_code != 200:
        raise Exception(f"فشل الاتصال، الرمز: {res.status_code}")
    soup = BeautifulSoup(res.content, 'html.parser')
    
    title = "رواية_مجهولة"
    title_tag = soup.find('meta', property='og:title')
    if title_tag:
        title = title_tag.get('content')
    else:
        t_tag = soup.find('h1') or soup.find('title')
        if t_tag: title = t_tag.text
    title = clean_text(title.split('|')[0].split('-')[0])
    
    desc = ""
    desc_tag = soup.find('meta', property='og:description') or soup.find('meta', attrs={'name': 'description'})
    if desc_tag:
        desc = clean_text(desc_tag.get('content'))
    
    cover_url = None
    cover_tag = soup.find('meta', property='og:image')
    if cover_tag:
        cover_url = cover_tag.get('content')
    elif soup.find('img', class_=lambda x: x and ('cover' in x or 'thumb' in x or 'poster' in x)):
        img_tag = soup.find('img', class_=lambda x: x and ('cover' in x or 'thumb' in x or 'poster' in x))
        cover_url = img_tag.get('src')
    
    if cover_url:
        cover_url = urljoin(url, cover_url)

    chapters_data = []
    seen_links = set()
    
    for a in soup.find_all('a', href=True):
        href = a.get('href', '')
        text = clean_text(a.get_text())
        if any(k in href.lower() for k in ['chapter', 'part', 'ch-', 'story', 'read', 'episode']) or any(k in text for k in ['الفصل', 'الحلقة', 'جزء']):
            full_link = urljoin(url, href)
            if full_link not in seen_links and full_link != url and '#' not in href:
                seen_links.add(full_link)
                chapters_data.append((text or f"فصل", full_link))
                
    if not chapters_data:
        chapters_data = [(title, url)]
        
    return title, desc, cover_url, chapters_data[:40]

def process_single_chapter(ch_data):
    idx, ch_title, ch_url = ch_data
    try:
        res = requests.get(ch_url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.content, 'html.parser')
            content_div = soup.find('div', class_=lambda x: x and ('reading-content' in x or 'chapter-inner' in x or 'story-text' in x or 'entry-content' in x))
            if not content_div:
                content_div = soup.find('pre', class_=lambda x: x and 'story' in x)
            if not content_div:
                content_div = soup
            
            html_parts = []
            text_parts = []
            for el in content_div.find_all(['p', 'img']):
                if el.name == 'img':
                    src = el.get('src') or el.get('data-src')
                    if src:
                        html_parts.append(f'<img src="{urljoin(ch_url, src)}" />')
                elif el.name == 'p' and len(el.get_text().strip()) > 0:
                    clean_p = clean_text(el.get_text())
                    html_parts.append(f'<p>{clean_p}</p>')
                    text_parts.append(clean_p)
            
            return idx, ch_title, "\n".join(html_parts), "\n\n".join(text_parts)
    except:
        pass
    return idx, ch_title, "", ""

def generate_ultimate_epub(title, desc, cover_url, chapters_data, output_filename):
    book = epub.EpubBook()
    book.set_identifier(f'id_{uuid.uuid4().hex}')
    book.set_title(title)
    book.set_language('ar')
    book.add_author('Maissa Graphics | Auto Converter')

    spine_items = ['nav']

    if cover_url:
        cover_bytes = fetch_resource(cover_url)
        if cover_bytes:
            book.set_cover("cover.jpg", cover_bytes)
            spine_items.append('cover')

    if desc:
        desc_item = epub.EpubHtml(title='وصف الرواية', file_name='desc.xhtml', lang='ar')
        desc_item.content = f'<div dir="rtl" style="font-family: Arial, sans-serif;"><h2>وصف الرواية</h2><p>{desc}</p></div>'
        book.add_item(desc_item)
        spine_items.append(desc_item)

    toc_links = []
    indexed_chapters = [(i, ch_title, ch_url) for i, (ch_title, ch_url) in enumerate(chapters_data, start=1)]
    scraped_results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        results = executor.map(process_single_chapter, indexed_chapters)
        for res in results:
            scraped_results.append(res)
            
    for idx, ch_title, ch_html, _ in scraped_results:
        if len(ch_html) < 20: continue
            
        ch_soup = BeautifulSoup(ch_html, 'html.parser')
        for img in ch_soup.find_all('img'):
            src = img.get('src')
            if src:
                img_bytes = fetch_resource(src)
                if img_bytes:
                    img_name = f"img_{uuid.uuid4().hex[:6]}.jpg"
                    epub_img = epub.EpubItem(uid=img_name, file_name=f"images/{img_name}", media_type="image/jpeg", content=img_bytes)
                    book.add_item(epub_img)
                    img['src'] = f"images/{img_name}"
                    img['style'] = "max-width: 100%; height: auto; display: block; margin: 10px auto;"
                else:
                    img.decompose()

        file_name = f'chap_{idx:03d}.xhtml'
        c = epub.EpubHtml(title=ch_title, file_name=file_name, lang='ar')
        c.content = f'<div dir="rtl" style="font-family: Arial, sans-serif;"><h2>{ch_title}</h2>{str(ch_soup)}</div>'
        
        book.add_item(c)
        spine_items.append(c)
        toc_links.append(epub.Link(file_name, ch_title, f'ch_{idx}'))

    book.toc = tuple(toc_links)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    style = 'BODY {direction: rtl; text-align: right; line-height: 1.6;} img {max-width: 100%; height: auto;}'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)
    book.spine = spine_items

    epub.write_epub(output_filename, book, {})

def generate_pdf(title, desc, chapters_data, output_filename):
    c = canvas.Canvas(output_filename, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, title[:50])
    y = height - 90
    c.setFont("Helvetica", 11)
    
    indexed_chapters = [(i, ch_title, ch_url) for i, (ch_title, ch_url) in enumerate(chapters_data, start=1)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(process_single_chapter, indexed_chapters)
        for _, ch_title, _, ch_text in results:
            if len(ch_text) < 20: continue
            if y < 100:
                c.showPage()
                y = height - 50
            c.setFont("Helvetica-Bold", 13)
            c.drawString(50, y, ch_title[:60])
            y -= 25
            c.setFont("Helvetica", 10)
            for line in ch_text.split('\n'):
                if line.strip():
                    if y < 50:
                        c.showPage()
                        y = height - 50
                    c.drawString(50, y, line[:90])
                    y -= 15
            y -= 20
    c.save()

def generate_txt(title, desc, chapters_data, output_filename):
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(f"عنوان الرواية: {title}\n\n")
        if desc:
            f.write(f"الوصف:\n{desc}\n\n")
        f.write("="*50 + "\n\n")
        
        indexed_chapters = [(i, ch_title, ch_url) for i, (ch_title, ch_url) in enumerate(chapters_data, start=1)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            results = executor.map(process_single_chapter, indexed_chapters)
            for idx, ch_title, _, ch_text in results:
                if len(ch_text) > 20:
                    f.write(f"\n\n--- {ch_title} ---\n\n")
                    f.write(ch_text)
                    f.write("\n\n")

def generate_html_archive(title, desc, chapters_data, output_filename):
    html_content = f"""<!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head><meta charset="UTF-8"><title>{title}</title>
    <style>body{{font-family: Arial, sans-serif; padding: 20px; line-height: 1.6; max-width: 800px; margin: auto; background: #f9f9f9;}} h1, h2{{color: #333;}} .chapter{{background: #fff; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);}}</style>
    </head>
    <body>
    <h1>{title}</h1>
    """
    if desc:
        html_content += f"<div class='chapter'><h2>وصف الرواية</h2><p>{desc}</p></div>"
        
    indexed_chapters = [(i, ch_title, ch_url) for i, (ch_title, ch_url) in enumerate(chapters_data, start=1)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        results = executor.map(process_single_chapter, indexed_chapters)
        for idx, ch_title, ch_html, _ in results:
            if len(ch_html) > 20:
                html_content += f"<div class='chapter'><h2>{ch_title}</h2>{ch_html}</div>"
                
    html_content += "</body></html>"
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)

@app.route('/convert', methods=['POST'])
def convert_novel():
    data = request.json
    if not data or not data.get('url'):
        return jsonify({"error": "البيانات أو الرابط مفقود"}), 400
        
    url = data.get('url').strip()
    format_type = data.get('format', 'epub').lower()

    try:
        title, desc, cover_url, chapters_data = scrape_universal_metadata(url)
        safe_title = "".join([c for c in title if c.isalnum() or c.isspace()]).strip()
        
        if format_type == 'txt':
            output_filename = f"{safe_title or 'novel'}.txt"
            generate_txt(title, desc, chapters_data, output_filename)
        elif format_type == 'pdf':
            output_filename = f"{safe_title or 'novel'}.pdf"
            generate_pdf(title, desc, chapters_data, output_filename)
        elif format_type == 'html':
            output_filename = f"{safe_title or 'novel'}.html"
            generate_html_archive(title, desc, chapters_data, output_filename)
        elif format_type == 'mobi':
            # تنسيق MOBI يعتمد على بنية الـ EPUB القياسية المعتمدة من أمازون
            output_filename = f"{safe_title or 'novel'}.mobi"
            generate_ultimate_epub(title, desc, cover_url, chapters_data, output_filename)
        else:
            output_filename = f"{safe_title or 'novel'}.epub"
            generate_ultimate_epub(title, desc, cover_url, chapters_data, output_filename)
        
        return send_file(output_filename, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return "Universal All-Format Novel Converter with MOBI is Running!"

if __name__ == '__main__':
    app.run(0.0.0.0, port=5000)

