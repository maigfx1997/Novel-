import requests
from bs4 import BeautifulSoup
import base64
import re
import os
from flask import Flask, render_template, request, send_file, jsonify

# مكتبات بناء الكتب
from ebooklib import epub
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# إنشاء التطبيق
app = Flask(__name__)

# ترويسات المتصفح لتجاوز الحظر
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.google.com/',
    'DNT': '1'
}

def get_soup(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            return BeautifulSoup(response.text, 'html.parser')
    except Exception:
        return None
    return None

def download_image_as_base64(img_url):
    """تحميل صورة من رابط وتحويلها إلى Base64 لضمان ظهورها في الملفات"""
    if not img_url or not img_url.startswith('http'):
        return None
    try:
        response = requests.get(img_url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            ext = img_url.split('.')[-1].split('?')[0].lower()
            if ext not in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
                ext = 'jpeg'
            encoded = base64.b64encode(response.content).decode('utf-8')
            return f"data:image/{ext};base64,{encoded}"
    except Exception:
        return None
    return None

def extract_content_with_images(soup):
    """استخراج نص الفصل مع تحويل الصور إلى Base64"""
    content_div = soup.find('div', class_=re.compile('chapter-content|content|entry-content|reading-content|chapter', re.I))
    if not content_div:
        content_div = soup.body if soup.body else soup

    # تحويل الصور
    for img in content_div.find_all('img'):
        src = img.get('src')
        if src:
            base64_img = download_image_as_base64(src)
            if base64_img:
                img['src'] = base64_img
    
    return str(content_div)

def get_chapter_title(soup):
    title = soup.find('h1') or soup.find('h2') or soup.find('h3')
    return title.get_text(strip=True) if title else "Untitled Chapter"

def scrape_novel_from_url(url):
    """الدالة الرئيسية المسؤولة عن جلب البيانات من أي موقع"""
    
    # 1. جلب البيانات الوصفية (العنوان، المؤلف، الغلاف، الوصف)
    soup = get_soup(url)
    if not soup: return None, "Error: Cannot access the page"

    title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Unknown"
    author = "Unknown"
    author_tag = soup.find('a', href=re.compile('user|author|profile', re.I))
    if author_tag: author = author_tag.get_text(strip=True)
    
    description = ""
    desc_tag = soup.find('meta', attrs={'name':'description'}) or soup.find('meta', property='og:description')
    if desc_tag: description = desc_tag.get('content', '')

    cover_url = ""
    cover_tag = soup.find('meta', property='og:image') or soup.find('img', class_=re.compile('cover', re.I))
    if cover_tag:
        cover_url = cover_tag.get('content') if cover_tag.name == 'meta' else cover_tag.get('src')

    # 2. استخراج روابط الفصول
    chapter_links = []
    for a in soup.find_all('a', href=True):
        href = a['href'].lower()
        if any(k in href for k in ['chapter', 'chap-', 'novel/', 'part/']): 
            chapter_links.append(a['href'])
    
    chapter_links = list(dict.fromkeys(chapter_links))
    if not chapter_links: return None, "Error: No chapters found"

    # 3. جلب محتوى كل فصل مع الصور
    all_chapters_html = []
    for link in chapter_links:
        full_url = link if link.startswith('http') else f"{url.split('/')[0]}//{url.split('/')[2]}{link}"
        chap_soup = get_soup(full_url)
        if chap_soup:
            chap_html = extract_content_with_images(chap_soup)
            chap_title = get_chapter_title(chap_soup)
            all_chapters_html.append({'title': chap_title, 'html': chap_html})

    # 4. تجهيز البيانات للتحويل
    book_data = {
        'title': title,
        'author': author,
        'description': description,
        'cover_url': cover_url,
        'chapters': all_chapters_html
    }
    return book_data, None

# ==========================================
# دوال التحويل للصيغ المختلفة
# ==========================================

def convert_to_epub(book_data, output_filename):
    book = epub.EpubBook()
    book.set_identifier(f'id_{output_filename}')
    book.set_title(book_data['title'])
    book.set_language('en')
    book.add_author(book_data['author'])
    
    if book_data['description']:
        book.add_metadata('DC', 'description', book_data['description'])

    if book_data['cover_url']:
        try:
            cover_bytes = requests.get(book_data['cover_url'], headers=HEADERS).content
            book.set_cover("cover.jpg", cover_bytes)
        except:
            pass

    chapters = []
    for i, chap in enumerate(book_data['chapters']):
        c = epub.EpubHtml(title=chap['title'], file_name=f'chap_{i}.xhtml', lang='en')
        c.content = f"<h1>{chap['title']}</h1><br/>{chap['html']}"
        book.add_item(c)
        chapters.append(c)

    book.toc = chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    book.spine = ['nav'] + chapters
    epub.write_epub(output_filename, book, {})
    return output_filename

def convert_to_pdf(book_data, output_filename):
    styles = getSampleStyleSheet()
    
    doc = SimpleDocTemplate(output_filename, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    story = []
    
    story.append(Paragraph(book_data['title'], styles['Title']))
    story.append(Paragraph(f"By: {book_data['author']}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    for chap in book_data['chapters']:
        clean_html = BeautifulSoup(chap['html'], 'html.parser').get_text(separator='\n', strip=True)
        story.append(Paragraph(chap['title'], styles['Heading2']))
        for line in clean_html.split('\n'):
            story.append(Paragraph(line, styles['Normal']))
        story.append(Spacer(1, 20))
        
    doc.build(story)
    return output_filename

def convert_to_txt(book_data, output_filename):
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(f"{book_data['title']}\nBy: {book_data['author']}\n\n{book_data['description']}\n\n")
        for chap in book_data['chapters']:
            clean_html = BeautifulSoup(chap['html'], 'html.parser').get_text(separator='\n', strip=True)
            f.write(f"\n--- {chap['title']} ---\n\n")
            f.write(clean_html)
    return output_filename

def convert_to_html(book_data, output_filename):
    html_content = f"<html><head><title>{book_data['title']}</title></head><body>"
    html_content += f"<h1>{book_data['title']}</h1><p>By: {book_data['author']}</p>"
    for chap in book_data['chapters']:
        html_content += f"<hr/><h2>{chap['title']}</h2><br/>{chap['html']}"
    html_content += "</body></html>"
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    return output_filename

def convert_to_azw3(book_data, output_filename):
    # بناء ملف EPUB ثم تسميته AZW3 (أفضل طريقة لأجهزة Kindle)
    return convert_to_epub(book_data, output_filename)

# ==========================================
# مسارات Flask (Routes)
# ==========================================

@app.route('/')
def index():
    return render_template('new_doc.html')

@app.route('/convert', methods=['POST'])
def convert():
    data = request.json
    url = data.get('url')
    output_format = data.get('format')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        # جلب البيانات
        book_data, error = scrape_novel_from_url(url)
        if error:
            return jsonify({'error': error}), 500

        # تحديد الصيغة واسم الملف
        output_file = "book_output"
        
        if output_format == "EPUB":
            final_file = convert_to_epub(book_data, f"{output_file}.epub")
            mime_type = "application/epub+zip"
        elif output_format == "PDF":
            final_file = convert_to_pdf(book_data, f"{output_file}.pdf")
            mime_type = "application/pdf"
        elif output_format == "TXT":
            final_file = convert_to_txt(book_data, f"{output_file}.txt")
            mime_type = "text/plain"
        elif output_format == "HTML":
            final_file = convert_to_html(book_data, f"{output_file}.html")
            mime_type = "text/html"
        elif output_format == "AZW3":
            final_file = convert_to_azw3(book_data, f"{output_file}.azw3")
            mime_type = "application/octet-stream"
        else:
            return jsonify({'error': 'Unsupported format'}), 400

        # إرسال الملف للمستخدم
        return send_file(final_file, as_attachment=True, download_name=os.path.basename(final_file), mimetype=mime_type)

    except Exception as e:
        return jsonify({'error': f'Server Error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
