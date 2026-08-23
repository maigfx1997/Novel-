from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from ebooklib import epub
import os
import re

app = Flask(__name__)
CORS(app)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8'
}

def clean_text(text):
    if not text:
        return ""
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    return cleaned.strip()

def fetch_image(url):
    """دالة لجلب صور الغلاف والفقرات وتحويلها لبيانات متوافقة مع EPUB"""
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            return res.content
    except Exception:
        pass
    return None

def scrape_full_novel(url):
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"فشل الاتصال بالرابط، الرمز: {response.status_code}")
        
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # 1. استخراج العنوان والوصف وصورة الغلاف
    title_tag = soup.find('h1') or soup.find('title')
    title = clean_text(title_tag.text) if title_tag else "رواية_مترجمة"
    title = title.split('|')[0].split('-')[0].strip() or "رواية_مترجمة"
    
    # الوصف
    desc_tag = soup.find('div', class_=lambda x: x and ('description' in x or 'summary' in x or 'abstract' in x)) or soup.find('meta', attrs={'name': 'description'})
    description = ""
    if desc_tag:
        description = clean_text(desc_tag.get('content', '') if desc_tag.name == 'meta' else desc_tag.text)
        
    # الغلاف
    cover_bytes = None
    cover_img_tag = soup.find('meta', property='og:image') or soup.find('img', class_=lambda x: x and ('cover' in x or 'poster' in x))
    if cover_img_tag:
        cover_url = cover_img_tag.get('content') if cover_img_tag.name == 'meta' else cover_img_tag.get('src')
        if cover_url:
            cover_url = cover_url if cover_url.startswith('http') else requests.compat.urljoin(url, cover_url)
            cover_bytes = fetch_image(cover_url)

    # 2. استخراج الفصول مع ترتيبها الصحيح
    chapters_data = []
    seen_links = set()
    
    # فلترة مخصصة للروابط
    links = soup.find_all('a', href=True)
    
    # إصلاح خربطة Wattpad عبر ترتيب روابط القائمة حسب ظهورها في شجرة الـ DOM
    if 'wattpad.com' in url:
        story_parts = soup.find_all('a', class_=lambda x: x and 'story-parts' in x) or links
        links = story_parts

    for a in links:
        href = a['href']
        text = clean_text(a.get_text())
        
        if any(keyword in href.lower() for keyword in ['chapter', 'part', 'ch-', 'story', 'read']) or 'الفصل' in text or 'الحلقة' in text:
            full_link = href if href.startswith('http') else requests.compat.urljoin(url, href)
            if full_link not in seen_links and full_link != url:
                seen_links.add(full_link)
                chapters_data.append((text or f"فصل", full_link))

    if not chapters_data:
        paragraphs = soup.find_all('p')
        content = "\n\n".join([clean_text(p.get_text()) for p in paragraphs if len(p.get_text().strip()) > 20])
        return title, description, cover_bytes, [(title, content)]
        
    fully_scraped_chapters = []
    for ch_title, ch_url in chapters_data[:50]:
        try:
            ch_res = requests.get(ch_url, headers=HEADERS)
            if ch_res.status_code == 200:
                ch_soup = BeautifulSoup(ch_res.content, 'html.parser')
                content_container = ch_soup.find('pre', class_='story-text') or ch_soup.find('div', class_='reading-content') or ch_soup.find('div', class_='chapter-inner') or ch_soup
                
                paragraphs = content_container.find_all(['p', 'div'])
                ch_content = "\n\n".join([clean_text(p.get_text()) for p in paragraphs if len(p.get_text().strip()) > 20])
                
                if len(ch_content) > 50:
                    fully_scraped_chapters.append((clean_text(ch_title), ch_content))
        except Exception:
            continue
            
    if not fully_scraped_chapters:
        paragraphs = soup.find_all('p')
        content = "\n\n".join([clean_text(p.get_text()) for p in paragraphs if len(p.get_text().strip()) > 20])
        return title, description, cover_bytes, [(title, content)]
        
    return title, description, cover_bytes, fully_scraped_chapters

def generate_full_epub(title, description, cover_bytes, chapters_data, output_filename):
    book = epub.EpubBook()
    book.set_identifier('id_full_novel')
    book.set_title(title)
    book.set_language('ar')
    book.add_author('Maissa Graphics')

    spine_items = ['nav']

    # إضافة الغلاف إذا وُجد
    if cover_bytes:
        book.set_cover("cover.jpg", cover_bytes)
        spine_items.append('cover')

    # إضافة صفحة الوصف
    if description:
        desc_item = epub.EpubHtml(title='وصف الرواية', file_name='desc.xhtml', lang='ar')
        desc_item.content = f'<div dir="rtl" style="font-family: Arial, sans-serif;"><h2>وصف الرواية</h2><p>{description}</p></div>'
        book.add_item(desc_item)
        spine_items.append(desc_item)

    toc_links = []
    for idx, (ch_title, ch_content) in enumerate(chapters_data, start=1):
        file_name = f'chap_{idx:03d}.xhtml'
        c = epub.EpubHtml(title=ch_title, file_name=file_name, lang='ar')
        
        formatted_content = f'<div dir="rtl" style="font-family: Arial, sans-serif;"><h2>{ch_title}</h2>'
        for paragraph in ch_content.split('\n'):
            if paragraph.strip():
                formatted_content += f'<p>{paragraph.strip()}</p>'
        formatted_content += '</div>'
        
        c.content = formatted_content
        book.add_item(c)
        spine_items.append(c)
        toc_links.append(epub.Link(file_name, ch_title, f'ch_{idx}'))

    book.toc = tuple(toc_links)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    style = 'BODY {direction: rtl; text-align: right; line-height: 1.6;}'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)
    book.spine = spine_items

    epub.write_epub(output_filename, book, {})

@app.route('/convert', methods=['POST'])
def convert_novel():
    data = request.json
    if not data:
        return jsonify({"error": "البيانات المرسلة فارغة"}), 400
        
    url = data.get('url', '').strip().lower()
    format_type = data.get('format')

    if not url:
        return jsonify({"error": "رابط الرواية مفقود"}), 400

    try:
        if any(domain in url for domain in ['wattpad.com', 'novlar', 'uranus']):
            title, description, cover_bytes, chapters_data = scrape_full_novel(url)
        else:
            return jsonify({"error": "عذراً، الموقع غير مدعوم. يدعم النظام Wattpad, Novlar, Uranus"}), 400

        if format_type == 'epub':
            safe_title = "".join([c for c in title if c.isalnum() or c.isspace()]).strip()
            output_filename = f"{safe_title or 'novel'}_full.epub"
            
            generate_full_epub(title, description, cover_bytes, chapters_data, output_filename)
            
            return send_file(output_filename, as_attachment=True)
        else:
            return jsonify({"error": "صيغة PDF قيد التطوير، يرجى اختيار EPUB"}), 501

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return "Cover and Meta Novel Converter Backend is Running!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

