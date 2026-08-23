from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from ebooklib import epub
import os

app = Flask(__name__)
CORS(app)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8'
}

def scrape_full_novel(url):
    """دالة ذكية لسحب الفهرس وكل الفصول الخاصة بالرواية"""
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"فشل الاتصال بالرابط، رمز الاستجابة: {response.status_code}")
        
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # 1. استخراج عنوان الرواية
    title_tag = soup.find('h1') or soup.find('h2', class_='story-title') or soup.find('title')
    title = title_tag.text.strip() if title_tag else "رواية_كاملة"
    
    # 2. البحث عن روابط الفصول في الصفحة (فهرس الرواية)
    chapter_links = []
    # البحث عن الروابط التي قد تمثل فصولاً داخل صفحة الفهرس
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.get_text().strip()
        # فلترة الروابط لتجنب الروابط الخارجية أو الإعلانية
        if ('chapter' in href or 'part' in href or 'الفصل' in text or 'الحلقة' in text) and len(text) < 100:
            full_link = href if href.startswith('http') else requests.compat.urljoin(url, href)
            if full_link not in chapter_links:
                chapter_links.append((text or f"فصل", full_link))
                
    # إذا لم يجد روابط فهارس، فهذا يعني أن المستخدم أدخل رابط فصل واحد
    if not chapter_links:
        # نسحب المحتوى كفصل منفرد
        paragraphs = soup.find_all('p')
        content = "\n\n".join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 20])
        return title, [(title, content)]
        
    # 3. سحب محتوى كل فصل تم العثور عليه في الفهرس (نأخذ أول 30-50 فصل كحد أقصى لمنع تأخر السيرفر)
    chapters_data = []
    for ch_title, ch_url in chapter_links[:40]: 
        try:
            ch_res = requests.get(ch_url, headers=HEADERS)
            if ch_res.status_code == 200:
                ch_soup = BeautifulSoup(ch_res.content, 'html.parser')
                paragraphs = ch_soup.find_all('p')
                ch_content = "\n\n".join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 20])
                if len(ch_content) > 100:
                    chapters_data.append((ch_title, ch_content))
        except Exception:
            continue
            
    if not chapters_data:
        raise Exception("عذراً، لم نتمكن من سحب محتوى الفصول تلقائياً من هذا الرابط.")
        
    return title, chapters_data

def generate_full_epub(title, chapters_data, output_filename):
    book = epub.EpubBook()
    book.set_identifier('id_full_novel')
    book.set_title(title)
    book.set_language('ar')
    book.add_author('Novel Converter')

    epub_chapters = []
    spine_items = ['nav']
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
        epub_chapters.append(c)
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
        
    url = data.get('url', '').strip()
    format_type = data.get('format')

    if not url:
        return jsonify({"error": "رابط الرواية مفقود"}), 400

    try:
        title, chapters_data = scrape_full_novel(url)

        if format_type == 'epub':
            safe_title = "".join([c for c in title if c.isalnum() or c.isspace()]).strip()
            output_filename = f"{safe_title or 'novel'}_full.epub"
            
            generate_full_epub(title, chapters_data, output_filename)
            
            return send_file(output_filename, as_attachment=True)
        else:
            return jsonify({"error": "صيغة PDF قيد التطوير، يرجى اختيار EPUB"}), 501

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return "Full Novel Converter Backend is Running!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

