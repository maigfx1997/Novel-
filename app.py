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

def scrape_wattpad(url):
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"فشل الاتصال بـ Wattpad، الرمز: {response.status_code}")
    soup = BeautifulSoup(response.content, 'html.parser')
    title_tag = soup.find('h1', class_='story-title') or soup.find('div', class_='story-info__title')
    title = title_tag.text.strip() if title_tag else "رواية_واتباد"
    
    content_div = soup.find('pre', class_='story-text') or soup.find('div', class_='part-text')
    if not content_div:
        paragraphs = soup.find_all('p')
        content = "\n".join([p.text for p in paragraphs]) if paragraphs else "لم يتم العثور على محتوى."
    else:
        content = content_div.text.strip()
    return title, content

def scrape_novlar(url):
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"فشل الاتصال بـ Novlar، الرمز: {response.status_code}")
    soup = BeautifulSoup(response.content, 'html.parser')
    
    title_tag = soup.find('h1') or soup.find('h2', class_='chapter-title')
    title = title_tag.text.strip() if title_tag else "رواية_نوفلار"
    
    content_container = soup.find('div', class_='reading-content') or soup.find('div', class_='text-left') or soup.find('div', class_='entry-content') or soup.find('div', class_='chapter-content')
    if content_container:
        paragraphs = content_container.find_all(['p', 'div'])
        content = "\n".join([p.text.strip() for p in paragraphs if p.text.strip()])
    else:
        paragraphs = soup.find_all('p')
        content = "\n".join([p.text for p in paragraphs]) if paragraphs else "لم يتم العثور على محتوى."
    
    return title, content

def scrape_uranus(url):
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"فشل الاتصال بـ Uranus، الرمز: {response.status_code}")
    soup = BeautifulSoup(response.content, 'html.parser')
    
    title_tag = soup.find('h1')
    title = title_tag.text.strip() if title_tag else "رواية_أورانوس"
    
    content_container = soup.find('div', class_='chapter-inner') or soup.find('div', class_='read-container') or soup.find('div', class_='entry-content')
    if content_container:
        paragraphs = content_container.find_all(['p'])
        content = "\n".join([p.text.strip() for p in paragraphs if p.text.strip()])
    else:
        paragraphs = soup.find_all('p')
        content = "\n".join([p.text for p in paragraphs]) if paragraphs else "لم يتم العثور على محتوى."
        
    return title, content

def generate_epub(title, content, output_filename):
    book = epub.EpubBook()
    book.set_identifier('id123456')
    book.set_title(title)
    book.set_language('ar')
    book.add_author('Novel Converter')

    c1 = epub.EpubHtml(title='الفصل الأول', file_name='chap_01.xhtml', lang='ar')
    formatted_content = f'<div dir="rtl" style="font-family: Arial, sans-serif;"><h1>{title}</h1>'
    for paragraph in content.split('\n'):
        if paragraph.strip():
            formatted_content += f'<p>{paragraph.strip()}</p>'
    formatted_content += '</div>'
    
    c1.content = formatted_content
    book.add_item(c1)

    book.toc = (epub.Link('chap_01.xhtml', 'الفصل الأول', 'intro'),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    style = 'BODY {direction: rtl; text-align: right;}'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)
    book.spine = ['nav', c1]

    epub.write_epub(output_filename, book, {})

@app.route('/convert', methods=['POST'])
def convert_novel():
    data = request.json
    if not data:
        return jsonify({"error": "البيانات المرسلة فارغة"}), 400
        
    url = data.get('url', '').lower()
    format_type = data.get('format')

    if not url:
        return jsonify({"error": "رابط الرواية مفقود"}), 400

    output_filename = None
    try:
        if 'wattpad.com' in url:
            title, content = scrape_wattpad(url)
        elif 'novlar' in url:
            title, content = scrape_novlar(url)
        elif 'uranus' in url:
            title, content = scrape_uranus(url)
        else:
            return jsonify({"error": "عذراً، هذا الموقع غير مدعوم حالياً. يدعم النظام Wattpad, Novlar, Uranus"}), 400

        if format_type == 'epub':
            safe_title = "".join([c for c in title if c.isalnum() or c.isspace()]).strip()
            output_filename = f"{safe_title or 'novel'}.epub"
            
            generate_epub(title, content, output_filename)
            
            return send_file(output_filename, as_attachment=True)
        else:
            return jsonify({"error": "صيغة PDF قيد التطوير، يرجى اختيار EPUB"}), 501

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return "Novel Converter Backend is Running!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

