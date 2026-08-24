import requests
from bs4 import BeautifulSoup
import base64
import re
import os
from flask import Flask, render_template, request, send_file, jsonify

# مكتبات بناء الكتب
from ebooklib import epub
import ebooklib
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
    
    # تنظيف الرابط من أي إضافات (مثل utm_source أو wp_page)
    clean_url = url.split('?')[0].strip()
    
    # ---------------------------------------------------------
    # دعم خاص لموقع واتباد (Wattpad)
    # ---------------------------------------------------------
    if "wattpad.com" in clean_url:
        match = re.search(r'/story/(\d+)', clean_url)
        if not match:
            return None, "Invalid Wattpad URL"
            
        story_id = match.group(1)
        api_url = f"https://www.wattpad.com/api/v3/stories/{story_id}"
        
        try:
            # استخدام ترويسات مخصصة أكثر تشابهاً للمتصفح لتجاوز الحجب
            api_headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                'Accept': 'application/json, text/plain, */*',
                'Referer': f'https://www.wattpad.com/story/{story_id}',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            response = requests.get(api_url, headers=api_headers, timeout=30)
            if response.status_code != 200:
                # إذا تم حجب الـ API، نحاول جلب البيانات من الصفحة العادية
                soup_page = get_soup(clean_url)
                if not soup_page:
                    return None, "Wattpad API blocked"
                
                title = soup_page.find('h1').get_text(strip=True) if soup_page.find('h1') else "Unknown"
                author = "Unknown"
                author_tag = soup_page.find('a', href=re.compile('user|author', re.I))
                if author_tag: author = author_tag.get_text(strip=True)
                description = ""
                desc_tag = soup_page.find('meta', attrs={'name':'description'})
                if desc_tag: description = desc_tag.get('content', '')
                
                # فلترة روابط الفصول من الصفحة العادية
                chapters = []
                for a in soup_page.find_all('a', href=True):
                    href = a['href']
                    if f'/story/{story_id}/' in href:
                        chapters.append(href)
                
                chapters = list(dict.fromkeys(chapters))
                if not chapters: return None, "No chapters found"
                
                all_chapters_html = []
                for link in chapters:
                    full_url = link if link.startswith('http') else f"https://www.wattpad.com{link}"
                    chap_soup = get_soup(full_url)
                    if chap_soup:
                        chap_html = extract_content_with_images(chap_soup)
                        chap_title = get_chapter_title(chap_soup)
                        all_chapters_html.append({'title': chap_title, 'html': chap_html})
                
                book_data = {'title': title, 'author': author, 'description': description, 'cover_url': '', 'chapters': all_chapters_html}
                return book_data, None

            data = response.json()
            title = data.get('title', 'Unknown')
            author = data.get('user', {}).get('name', 'Unknown')
            description = data.get('description', '')
            cover_url = data.get('cover', '')
            num_chapters = int(data.get('numParts', 0))
            
            # ⚠️ حد أقصى 30 فصل حتى لا ينقطع الاتصال بسبب الوقت
            if num_chapters > 30:
                num_chapters = 30
            
            all_chapters_html = []
            for part in range(1, num_chapters + 1):
                part_api_url = f"https://www.wattpad.com/api/v3/stories/{story_id}/parts/{part}"
                part_res = requests.get(part_api_url, headers=api_headers, timeout=30)
                if part_res.status_code == 200:
                    part_data = part_res.json()
                    part_title = part_data.get('title', f'Chapter {part}')
                    part_html = part_data.get('text', '')
                    
                    soup_part = BeautifulSoup(part_html, 'html.parser')
                    for img in soup_part.find_all('img'):
                        src = img.get('src')
                        if src:
                            base64_img = download_image_as_base64(src)
                            if base64_img:
                                img['src'] = base64_img
                    
                    all_chapters_html.append({'title': part_title, 'html': str(soup_part)})
            
            if not all_chapters_html:
                return None, "No chapters found"
                
            book_data = {
                'title': title,
                'author': author,
                'description': description,
                'cover_url': cover_url,
                'chapters': all_chapters_html
            }
            return book_data, None
            
        except Exception as e:
            return None, f"Wattpad API Error: {str(e)}"

    # ---------------------------------------------------------
    # المنطق العام للمواقع الأخرى (Novlar, Uranus, إلخ)
    # ---------------------------------------------------------
    soup = get_soup(clean_url)
    if not soup: return None, "Cannot access page"

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

    # استخراج روابط الفصول (محاولة عامة)
    chapter_links = []
    for a in soup.find_all('a', href=True):
        href = a['href'].lower()
        if any(k in href for k in ['chapter', 'chap-', 'novel/', 'part/']): 
            chapter_links.append(a['href'])
    
    chapter_links = list(dict.fromkeys(chapter_links))
    if not chapter_links: return None, "No chapters found"

    all_chapters_html = []
    for link in chapter_links:
        full_url = link if link.startswith('http') else f"{clean_url.split('/')[0]}//{clean_url.split('/')[2]}{link}"
        chap_soup = get_soup(full_url)
        if chap_soup:
            chap_html = extract_content_with_images(chap_soup)
            chap_title = get_chapter_title(chap_soup)
            all_chapters_html.append({'title': chap_title, 'html': chap_html})

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
    # بناء ملف EPUB ثم تسميته AZW3
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
