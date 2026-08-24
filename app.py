import os
from flask import Flask, request, send_file, jsonify, render_template_string
from flask_cors import CORS
import requests
from ebooklib import epub
import re
import uuid

app = Flask(__name__)
CORS(app)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Advanced EPUB Generator - Maissa Graphics</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #0f172a; color: #fff; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }
        .card { background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); width: 100%; max-width: 500px; text-align: center; }
        h1 { color: #60a5fa; margin-bottom: 5px; }
        .subtitle { color: #94a3b8; font-size: 14px; margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; text-align: left; }
        label { display: block; margin-bottom: 5px; font-size: 14px; color: #cbd5e1; }
        input, textarea { width: 100%; padding: 10px; border-radius: 6px; border: 1px solid #475569; background: #0f172a; color: #fff; box-sizing: border-box; font-family: inherit; }
        textarea { height: 150px; resize: vertical; }
        button { width: 100%; padding: 12px; background: #2563eb; border: none; border-radius: 6px; color: #fff; font-size: 16px; cursor: pointer; font-weight: bold; margin-top: 10px; }
        button:hover { background: #1d4ed8; }
        #statusMessage { margin-top: 15px; padding: 10px; border-radius: 6px; display: none; font-size: 14px; }
    </style>
</head>
<body>
    <div class="card">
        <h1>EPUB Generator</h1>
        <p class="subtitle">Maissa Graphics - Professional Book Creator</p>
        
        <div class="form-group">
            <label for="novelTitle">Novel Title:</label>
            <input type="text" id="novelTitle" placeholder="Enter novel title...">
        </div>

        <div class="form-group">
            <label for="novelDesc">Novel Description:</label>
            <textarea id="novelDesc" placeholder="Enter description or summary..."></textarea>
        </div>

        <div class="form-group">
            <label for="coverUrl">Cover Image URL (Optional):</label>
            <input type="url" id="coverUrl" placeholder="https://.../image.jpg">
        </div>
        
        <div class="form-group">
            <label for="novelContent">Chapters Content (Format: Chapter 1 ... Text):</label>
            <textarea id="novelContent" style="height: 200px;" placeholder="Chapter 1: Title&#10;Paragraph text here...&#10;&#10;Chapter 2: Title&#10;Paragraph text here..."></textarea>
        </div>
        
        <button onclick="generateEPUB()">Generate & Download EPUB</button>
        <div id="statusMessage"></div>
    </div>

    <script>
        async function generateEPUB() {
            const title = document.getElementById('novelTitle').value.trim();
            const desc = document.getElementById('novelDesc').value.trim();
            const cover = document.getElementById('coverUrl').value.trim();
            const content = document.getElementById('novelContent').value.trim();
            const statusDiv = document.getElementById('statusMessage');

            if (!title || !content) {
                alert('Please enter at least the Novel Title and Content!');
                return;
            }

            statusDiv.style.display = 'block';
            statusDiv.style.background = '#3b82f6';
            statusDiv.innerText = 'Generating your professional EPUB book, please wait...';

            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title, desc, cover, content })
                });

                if (!response.ok) throw new Error('Failed to generate EPUB file');

                const blob = await response.blob();
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = downloadUrl;
                a.download = title.replace(/[^a-zA-Z0-9]/g, '_') + ".epub";
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

def fetch_image(url):
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.content
    except:
        pass
    return None

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    if not data or not data.get('title') or not data.get('content'):
        return jsonify({"error": "Title and content are required"}), 400

    title = clean_text(data.get('title'))
    desc = clean_text(data.get('desc', ''))
    cover_url = clean_text(data.get('cover', ''))
    raw_content = data.get('content')

    try:
        book = epub.EpubBook()
        book.set_identifier(f'id_{uuid.uuid4().hex}')
        book.set_title(title)
        book.set_language('ar')
        book.add_author('Maissa Graphics')

        spine_items = ['nav']

        # إضافة الغلاف إذا توفر الرابط
        if cover_url:
            cover_bytes = fetch_image(cover_url)
            if cover_bytes:
                book.set_cover("cover.jpg", cover_bytes)
                spine_items.append('cover')

        # إضافة صفحة الوصف
        if desc:
            desc_item = epub.EpubHtml(title='Description', file_name='desc.xhtml', lang='ar')
            desc_item.content = f'<?xml version="1.0" encoding="utf-8"?>\n<html xmlns="http://www.w3.org/1999/xhtml" lang="ar" dir="rtl">\n<head><title>Description</title></head>\n<body><div dir="rtl" style="font-family: Arial, sans-serif;"><h2>Description</h2><p>{desc.replace(chr(10), "<br>")}</p></div></body>\n</html>'
            book.add_item(desc_item)
            spine_items.append(desc_item)

        # تقسيم النص إلى فصول بناءً على الكلمات المفتاحية مثل Chapter أو الفصل
        chapters_raw = re.split(r'(?i)(chapter\s*\d+|الفصل\s*\d+)', raw_content)
        
        chapters_data = []
        current_title = "Introduction"
        current_text = []

        for part in chapters_raw:
            if not part.strip():
                continue
            if re.match(r'(?i)(chapter\s*\d+|الفصل\s*\d+)', part.strip()):
                if current_text:
                    chapters_data.append((current_title, "\n".join(current_text)))
                    current_text = []
                current_title = part.strip()
            else:
                current_text.append(part)
        
        if current_text:
            chapters_data.append((current_title, "\n".join(current_text)))

        if not chapters_data:
            chapters_data = [(title, raw_content)]

        toc_links = []
        for idx, (ch_title, ch_text) in enumerate(chapters_data, start=1):
            file_name = f'chap_{idx:03d}.xhtml'
            formatted_text = "".join([f'<p>{p.strip()}</p>' for p in ch_text.split('\n') if p.strip()])
            
            c = epub.EpubHtml(title=ch_title, file_name=file_name, lang='ar')
            c.content = f'<?xml version="1.0" encoding="utf-8"?>\n<html xmlns="http://www.w3.org/1999/xhtml" lang="ar" dir="rtl">\n<head><title>{ch_title}</title></head>\n<body><div dir="rtl" style="font-family: Arial, sans-serif; line-height: 1.6;"><h2>{ch_title}</h2>{formatted_text}</div></body>\n</html>'
            
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

        safe_title = "".join([c for c in title if c.isalnum() or c.isspace()]).strip()
        output_filename = f"{safe_title or 'novel'}.epub"
        
        epub.write_epub(output_filename, book, {})
        return send_file(output_filename, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
