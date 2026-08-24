import os
from flask import Flask, request, send_file, jsonify, render_template_string
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from ebooklib import epub
import re
import uuid
from urllib.parse import urljoin
import concurrent.futures

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
CORS(app)

# ترويسات متعددة لتخطي الحمايات من مختلف المواقع
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
    'Referer': 'https://www.google.com/'
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Universal Novel Converter - Maissa Graphics</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #0f172a; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); width: 100%; max-width: 400px; text-align: center; }
        h1 { color: #60a5fa; margin-bottom: 5px; }
        .subtitle { color: #94a3b8; font-size: 14px; margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; text-align: left; }
        label { display: block; margin-bottom: 5px; font-size: 14px; }
        input, select { width: 100%; padding: 10px; border-radius: 6px; border: 1px solid #475569; background: #0f172a; color: #fff; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #2563eb; border: none; border-radius: 6px; color: #fff; font-size: 16px; cursor: pointer; font-weight: bold; margin-top: 10px; }
        button:hover { background: #1d4ed8; }
        #statusMessage { margin-top: 15px; padding: 10px; border-radius: 6px; display: none; font-size: 14px; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Novel Converter</h1>
        <p class="subtitle">Paste the link to your novel or fanfic</p>
        
        <div class="form-group">
            <label for="novelUrl">Novel URL:</label>
            <input type="url" id="novelUrl" placeholder="https://...">
        </div>
        
        <div class="form-group">
            <label for="outputFormat">Output Format:</label>
            <select id="outputFormat">
                <option value="epub">EPUB (E-Book for Apple Books)</option>
                <option value="mobi">MOBI (Kindle)</option>
                <option value="pdf">PDF (Document)</option>
                <option value="txt">TXT (Text)</option>
                <option value="html">HTML (Web)</option>
            </select>
        </div>
        
        <button onclick="startConversion()">Start Conversion</button>
        <div id="statusMessage"></div>
    </div>

    <script>
        async function startConversion() {
            let url = document.getElementById('novelUrl').value.trim();
            const format = document.getElementById('outputFormat').value;
            const statusDiv = document.getElementById('statusMessage');

            if (!url) {
                alert('Please enter the novel URL first!');
                return;
            }

            if (url.includes('?')) {
                url = url.split('?')[0];
            }

            statusDiv.style.display = 'block';
            statusDiv.style.background = '#3b82f6';
            statusDiv.innerText = 'Scraping chapters and generating file, please wait...';

            try {
                const response = await fetch('/convert', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url, format })
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Conversion failed. The site might be blocking the server.');
                }

                const blob = await response.blob();
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = downloadUrl;
                a.download = "novel_converted." + format;
                document.body.appendChild(a);
                a.click();
                a.remove();

                statusDiv.style.background = '#064e3b';
                statusDiv.style.color = '#34d399';
                statusDiv.innerText = 'Downloaded successfully!';
            } catch (error) {
                statusDiv.style.background = '#7f1d1d';
                statusDiv.style.color = '#fca5a5';
                statusDiv.innerText = 'Error: ' + error.message;
            }
        }
    </script>
</body>
</html>"""

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
    if not url.startswith('http'):
        raise Exception("Invalid URL, must start with https://")
        
    clean_url = url.split('?')[0]
    session = requests.Session()
    
    res = session.get(clean_url, headers=HEADERS, timeout=15)
    
    if res.status_code != 200:
        fallback_headers = {'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}
        res = session.get(clean_url, headers=fallback_headers, timeout=15)
        if res.status_code != 200:
            raise Exception(f"Connection blocked by the site (Status: {res.status_code}).")
        
    soup = BeautifulSoup(res.content, 'html.parser')
    
    title = "Novel_Converted"
    title_tag = soup.find('meta', property='og:title') or soup.find('h1') or soup.find('title')
    if title_tag:
        title = clean_text(title_tag.get('content') if title_tag.get('content') else title_tag.text)
    
    desc = ""
    desc_tag = soup.find('meta', property='og:description')
    if desc_tag:
        desc = clean_text(desc_tag.get('content'))
    
    cover_url = None
    cover_tag = soup.find('meta', property='og:image')
    if cover_tag:
        cover_url = cover_tag.get('content')
    if cover_url:
        cover_url = urljoin(clean_url, cover_url)

    chapters_data = []
    seen_links = set()
    
    # بحث ذكي عن الفصول باللغتين العربية والإنجليزية
    chapter_keywords = ['ch-', 'part', 'chapter', 'works', 'story', 'فصل', 'جزء', 'رواية']
    
    for a in soup.find_all('a', href=True):
        href = a.get('href', '')
        text = clean_text(a.get_text())
        
        is_chapter = any(k in href.lower() for k in chapter_keywords) or re.search(r'ch(apter)?-?\d+', href, re.I)
        
        if is_chapter:
            full_link = urljoin(clean_url, href)
            if full_link not in seen_links and full_link != clean_url and '#' not in href:
                seen_links.add(full_link)
                chapters_data.append((text or f"Chapter {len(chapters_data)+1}", full_link))
                
    if not chapters_data:
        # إذا لم يجد فصول، يعتبر الرابط نفسه هو الفصل الوحيد (للقصص القصيرة)
        chapters_data = [(title, clean_url)]
        
    return title, desc, cover_url, chapters_data[:50] # سحب حتى 50 فصل

def process_single_chapter(ch_data):
    idx, ch_title, ch_url = ch_data
    try:
        session = requests.Session()
        res = session.get(ch_url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.content, 'html.parser')
            
            # محاولة إيجاد حاوية النص بدقة
            content_div = soup.find('div', class_=re.compile(r'part-text|reading-content|story-text|entry-content|userstuff|content|chapter-content', re.I))
            
            # إذا لم يجد حاوية مخصصة، يبحث في كل الفقرات داخل الصفحة
            if not content_div:
                content_div = soup.find('article') or soup.find('main') or soup
            
            html_parts = []
            text_parts = []
            
            paragraphs = content_div.find_all('p')
            
            for el in paragraphs:
                txt = clean_text(el.get_text())
                if len(txt) > 10 and not any(k in txt.lower() for k in ['ranks', 'completed', 'starting date', 'all rights reserved']):
                    html_parts.append(f'<p>{txt}</p>')
                    text_parts.append(txt)
            
            return idx, ch_title, "\n".join(html_parts), "\n\n".join(text_parts)
    except:
        pass
    return idx, ch_title, "", ""

def generate_ultimate_epub(title, desc, cover_url, chapters_data, output_filename):
    scraped_results = []
    indexed_chapters = [(i, ch_title, ch_url) for i, (ch_title, ch_url) in enumerate(chapters_data, start=1)]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        results = executor.map(process_single_chapter, indexed_chapters)
        for res in results:
            scraped_results.append(res)
            
    # التحقق من وجود نصوص لتجنب خطأ Document is empty
    valid_chapters = [res for res in scraped_results if len(res[2]) > 20]
    
    if not valid_chapters:
        raise Exception("No readable text found. The site might be protected or the content is hidden.")

    book = epub.EpubBook()
    book.set_identifier(f'id_{uuid.uuid4().hex}')
    book.set_title(title)
    book.set_language('ar')
    book.add_author('Maissa Graphics')

    spine_items = ['nav']

    if cover_url:
        cover_bytes = fetch_resource(cover_url)
        if cover_bytes:
            book.set_cover("cover.jpg", cover_bytes)
            spine_items.append('cover')

    if desc:
        desc_item = epub.EpubHtml(title='Description', file_name='desc.xhtml', lang='ar')
        desc_item.content = f'<?xml version="1.0" encoding="utf-8"?>\n<html xmlns="http://www.w3.org/1999/xhtml" lang="ar" dir="rtl">\n<head><title>Description</title></head>\n<body><div dir="rtl"><h2>Description</h2><p>{desc}</p></div></body>\n</html>'
        book.add_item(desc_item)
        spine_items.append(desc_item)

    toc_links = []
    
    for idx, ch_title, ch_html, _ in valid_chapters:
        file_name = f'chap_{idx:03d}.xhtml'
        c = epub.EpubHtml(title=ch_title, file_name=file_name, lang='ar')
        c.content = f'<?xml version="1.0" encoding="utf-8"?>\n<html xmlns="http://www.w3.org/1999/xhtml" lang="ar" dir="rtl">\n<head><title>{ch_title}</title></head>\n<body><div dir="rtl"><h2>{ch_title}</h2>{ch_html}</div></body>\n</html>'
        
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

def generate_pdf(title, desc, chapters_data, output_filename):
    c = canvas.Canvas(output_filename, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, title[:50])
    y = height - 90
    c.setFont("Helvetica", 11)
    
    indexed_chapters = [(i, ch_title, ch_url) for i, (ch_title, ch_url) in enumerate(chapters_data, start=1)]
    valid_found = False
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(process_single_chapter, indexed_chapters)
        for _, ch_title, _, ch_text in results:
            if len(ch_text) < 20: continue
            valid_found = True
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
            
    if not valid_found:
        raise Exception("No readable text found. The site might be protected.")
    c.save()

def generate_txt(title, desc, chapters_data, output_filename):
    valid_found = False
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(f"Title: {title}\n\n")
        if desc:
            f.write(f"Description:\n{desc}\n\n")
        f.write("="*50 + "\n\n")
        
        indexed_chapters = [(i, ch_title, ch_url) for i, (ch_title, ch_url) in enumerate(chapters_data, start=1)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            results = executor.map(process_single_chapter, indexed_chapters)
            for idx, ch_title, _, ch_text in results:
                if len(ch_text) > 20:
                    valid_found = True
                    f.write(f"\n\n--- {ch_title} ---\n\n")
                    f.write(ch_text)
                    f.write("\n\n")
                    
    if not valid_found:
        os.remove(output_filename)
        raise Exception("No readable text found. The site might be protected.")

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
        html_content += f"<div class='chapter'><h2>Description</h2><p>{desc}</p></div>"
        
    indexed_chapters = [(i, ch_title, ch_url) for i, (ch_title, ch_url) in enumerate(chapters_data, start=1)]
    valid_found = False
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        results = executor.map(process_single_chapter, indexed_chapters)
        for idx, ch_title, ch_html, _ in results:
            if len(ch_html) > 20:
                valid_found = True
                html_content += f"<div class='chapter'><h2>{ch_title}</h2>{ch_html}</div>"
                
    if not valid_found:
        raise Exception("No readable text found. The site might be protected.")
        
    html_content += "</body></html>"
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/convert', methods=['POST'])
def convert_novel():
    data = request.json
    if not data or not data.get('url'):
        return jsonify({"error": "Data or URL is missing"}), 400
        
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
            output_filename = f"{safe_title or 'novel'}.mobi"
            generate_ultimate_epub(title, desc, cover_url, chapters_data, output_filename)
        else:
            output_filename = f"{safe_title or 'novel'}.epub"
            generate_ultimate_epub(title, desc, cover_url, chapters_data, output_filename)
        
        return send_file(output_filename, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
