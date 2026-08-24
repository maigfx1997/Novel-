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

# ... (هنا تأتي كل الدوال المساعدة: HEADERS, get_soup, download_image_as_base64, 
# extract_content_with_images, get_chapter_title, scrape_novel_from_url, 
# convert_to_epub, convert_to_pdf, convert_to_txt, convert_to_html, convert_to_azw3) ...

# ==========================================
# مسارات Flask (Routes) - ضعها هنا في النهاية
# ==========================================

# 1. المسار الرئيسي لعرض الصفحة (هنا يعمل render_template)
@app.route('/')
def index():
    return render_template('new_doc.html')

# 2. مسار استقبال البيانات وتحويلها
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

# تشغيل التطبيق
if __name__ == '__main__':
    app.run(debug=True, port=5000)
