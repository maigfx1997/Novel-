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

def scrape_novel_content(url):
    """دالة عامة ذكية لسحب العنوان وجميع النصوص والفقرات من أي رابط مدعوم"""
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"فشل الاتصال بالموقع، رمز الاستجابة: {response.status_code}")
        
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # 1. استخراج عنوان الرواية أو الفصل بأكثر من طريقة مضمونة
    title_tag = soup.find('h1') or soup.find('h2', class_='story-title') or soup.find('title')
    title = title_tag.text.strip() if title_tag else "رواية_مترجمة"
    
    # 2. سحب جميع الفقرات النصية المتاحة في الصفحة لضمان عدم إفراغ المحتوى
    paragraphs = soup.find_all('p')
    content_list = []
    
    for p in paragraphs:
        text = p.get_text().strip()
        # استبعاد النصوص القصيرة جداً أو الخاصة بالقوائم والإعلانات
        if len(text) > 20: 
            content_list.append(text)
            
    if not content_list:
        # محاولة بديلة لو كانت النصوص داخل وسم pre أو div رئيسي
        divs = soup.find_all(['pre', 'div'], class_=lambda x: x and ('content' in x or 'text' in x or 'read' in x))
        for d in divs:
            text = d.get_text().strip()
            if len(text) > 50:
                content_list.append(text)
                
    content = "\n\n".join(content_list)
    
    if not content.strip():
        raise Exception("عذراً، لم يتم العثور على نص داخل هذه الصفحة. قد تكون محمية أو تتطلب تسجيل دخول.")
        
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

    try:
        # التحقق من دعم الروابط
        if 'wattpad.com' in url or 'novlar' in url or 'uranus' in url or 'http' in url:
            title, content = scrape_novel_content(url)
        else:
            return jsonify({"error": "عذراً، هذا الرابط غير مدعوم."}), 400

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
    return "Novel Converter Backend is Running with Full Content Scraper!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
