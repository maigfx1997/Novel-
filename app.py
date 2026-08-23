from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from ebooklib import epub
import os
import re
import uuid
from urllib.parse import urljoin

app = Flask(__name__)
CORS(app)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8'
}

def clean_text(text):
    if not text: return ""
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text).strip()

def fetch_resource(url):
    """دالة لتحميل الصور (الغلاف وصور الفصول)"""
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            return res.content
    except Exception:
        pass
    return None

def scrape_universal_metadata(url):
    """خوارزمية ذكية لاستخراج الغلاف، الوصف، والعنوان من أي موقع"""
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        raise Exception(f"فشل الاتصال، الرمز: {res.status_code}")
    soup = BeautifulSoup(res.content, 'html.parser')
    
    # --- استخراج العنوان ---
    title = "رواية_مجهولة"
    title_tag = soup.find('meta', property='og:title')
    if title_tag:
        title = title_tag.get('content')
    else:
        t_tag = soup.find('h1') or soup.find('title')
        if t_tag: title = t_tag.text
    title = clean_text(title.split('|')[0].split('-')[0])
    
    # --- استخراج الوصف ---
    desc = ""
    desc_tag = soup.find('meta', property='og:description') or soup.find('meta', attrs={'name': 'description'})
    if desc_tag:
        desc = clean_text(desc_tag.get('content'))
    
    # --- استخراج الغلاف ---
    cover_url = None
    cover_tag = soup.find('meta', property='og:image')
    if cover_tag:
        cover_url = cover_tag.get('content')
    elif soup.find('img', class_=lambda x: x and ('cover' in x or 'thumb' in x or 'poster' in x)):
        cover_url = soup.find('img', class_=lambda x: x and ('cover' in x or 'thumb' in x or 'poster' in x)).get('src')
    
    if cover_url:
        cover_url = urljoin(url, cover_url)

    # --- استخراج روابط الفصول ---
    chapters_data = []
    seen_links = set()
    
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = clean_text(a.get_text())
        # كلمات مفتاحية عالمية للفصول في كل المواقع
        if any(k in href.lower() for k in ['chapter', 'part', 'ch-', 'story', 'read', 'episode']) or any(k in text for k in ['الفصل', 'الحلقة', 'جزء', 'chapter', 'part']):
            full_link = urljoin(url, href)
            # تجنب روابط التعليقات أو الروابط المكررة
            if full_link not in seen_links and full_link != url and '#' not in href:
                seen_links.add(full_link)
                chapters_data.append((text or f"فصل", full_link))
                
    if not chapters_data:
        chapters_data = [(title, url)] # إذا كانت الصفحة فصل واحد فقط
        
    # سحب أول 50 فصل كحد أقصى لتجنب توقف السيرفر (TimeOut)
    return title, desc, cover_url, chapters_data[:50]

def extract_chapter_html(ch_url):
    """دالة لاستخراج نصوص الفصل والصور الموجودة بداخله"""
    try:
        res = requests.get(ch_url, headers=HEADERS, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.content, 'html.parser')
            
            # محاولة إيجاد الحاوية الرئيسية للنص
            content_div = soup.find('div', class_=lambda x: x and ('reading-content' in x or 'chapter-inner' in x or 'story-text' in x or 'entry-content' in x))
            if not content_div:
                content_div = soup.find('pre', class_=lambda x: x and 'story' in x)
            if not content_div:
                content_div = soup # في حال لم يجد حاوية واضحة
            
            # جمع الفقرات والصور فقط
            html_parts = []
            for el in content_div.find_all(['p', 'img']):
                if el.name == 'img':
                    src = el.get('src') or el.get('data-src')
                    if src:
                        html_parts.append(f'<img src="{urljoin(ch_url, src)}" />')
                elif el.name == 'p' and len(el.get_text().strip()) > 0:
                    html_parts.append(f'<p>{clean_text(el.get_text())}</p>')
            
            return "\n".join(html_parts)
    except Exception:
        pass
    return ""

def generate_ultimate_epub(title, desc, cover_url, chapters_data, output_filename):
    book = epub.EpubBook()
    book.set_identifier(f'id_{uuid.uuid4().hex}')
    book.set_title(title)
    book.set_language('ar')
    book.add_author('Maissa Graphics | Auto Converter')

    spine_items = ['nav']

    # 1. إضافة الغلاف
    if cover_url:
        cover_bytes = fetch_resource(cover_url)
        if cover_bytes:
            book.set_cover("cover.jpg", cover_bytes)
            spine_items.append('cover')

    # 2. إضافة صفحة الوصف
    if desc:
        desc_item = epub.EpubHtml(title='وصف الرواية', file_name='desc.xhtml', lang='ar')
        desc_item.content = f'<div dir="rtl" style="font-family: Arial, sans-serif;"><h2>وصف الرواية</h2><p>{desc}</p></div>'
        book.add_item(desc_item)
        spine_items.append(desc_item)

    # 3. معالجة الفصول والصور الداخلية
    toc_links = []
    for idx, (ch_title, ch_url) in enumerate(chapters_data, start=1):
        ch_html = extract_chapter_html(ch_url)
        if len(ch_html) < 20: 
            continue # تجاهل الفصول الفارغة
            
        ch_soup = BeautifulSoup(ch_html, 'html.parser')
        
        # معالجة الصور الداخلية في الفصل وتحميلها
        for img in ch_soup.find_all('img'):
            src = img.get('src')
            if src:
                img_bytes = fetch_resource(src)
                if img_bytes:
                    img_name = f"img_{uuid.uuid4().hex[:6]}.jpg"
                    epub_img = epub.EpubItem(uid=img_name, file_name=f"images/{img_name}", media_type="image/jpeg", content=img_bytes)
                    book.add_item(epub_img)
                    
                    # استبدال رابط الصورة في HTML بالرابط المحلي داخل الكتاب
                    img['src'] = f"images/{img_name}"
                    img['style'] = "max-width: 100%; height: auto; display: block; margin: 10px auto;"
                else:
                    img.decompose() # حذف الصورة إذا فشل تحميلها

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

@app.route('/convert', methods=['POST'])
def convert_novel():
    data = request.json
    if not data or not data.get('url'):
        return jsonify({"error": "البيانات أو الرابط مفقود"}), 400
        
    url = data.get('url').strip()

    try:
        # لم نعد نقيد الروابط بمواقع محددة، سيعمل مع أي موقع!
        title, desc, cover_url, chapters_data = scrape_universal_metadata(url)

        safe_title = "".join([c for c in title if c.isalnum() or c.isspace()]).strip()
        output_filename = f"{safe_title or 'novel'}_ultimate.epub"
        
        generate_ultimate_epub(title, desc, cover_url, chapters_data, output_filename)
        
        return send_file(output_filename, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return "Universal Novel & Fanfic Converter is Running Perfectly!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


