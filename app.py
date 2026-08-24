import os
from flask import Flask, request, send_file, jsonify, render_template_string
from flask_cors import CORS
from ebooklib import epub
import uuid

app = Flask(__name__)
CORS(app)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Direct EPUB Generator - Maissa Graphics</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #0f172a; color: #fff; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }
        .card { background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); width: 100%; max-width: 500px; text-align: center; }
        h1 { color: #60a5fa; margin-bottom: 5px; font-size: 22px; }
        .subtitle { color: #94a3b8; font-size: 13px; margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; text-align: left; }
        label { display: block; margin-bottom: 5px; font-size: 14px; }
        input, textarea { width: 100%; padding: 10px; border-radius: 6px; border: 1px solid #475569; background: #0f172a; color: #fff; box-sizing: border-box; font-family: Arial, sans-serif; }
        textarea { resize: vertical; height: 150px; direction: rtl; text-align: right; }
        button { width: 100%; padding: 12px; background: #2563eb; border: none; border-radius: 6px; color: #fff; font-size: 16px; cursor: pointer; font-weight: bold; margin-top: 10px; }
        button:hover { background: #1d4ed8; }
        #statusMessage { margin-top: 15px; padding: 10px; border-radius: 6px; display: none; font-size: 14px; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Direct EPUB Generator</h1>
        <p class="subtitle">Paste your Arabic novel text and convert instantly</p>
        
        <div class="form-group">
            <label for="bookTitle">Book Title:</label>
            <input type="text" id="bookTitle" placeholder="Enter book title here...">
        </div>
        
        <div class="form-group">
            <label for="bookContent">Novel Text (Arabic):</label>
            <textarea id="bookContent" placeholder="الصق نص الرواية أو الفصول هنا..."></textarea>
        </div>
        
        <button onclick="generateEpub()">Generate & Download EPUB</button>
        <div id="statusMessage"></div>
    </div>

    <script>
        async function generateEpub() {
            const title = document.getElementById('bookTitle').value.trim();
            const content = document.getElementById('bookContent').value.trim();
            const statusDiv = document.getElementById('statusMessage');

            if (!title || !content) {
                alert('Please enter both the book title and the text content!');
                return;
            }

            statusDiv.style.display = 'block';
            statusDiv.style.background = '#3b82f6';
            statusDiv.innerText = 'Generating your EPUB file, please wait...';

            try {
                const response = await fetch('/create-epub', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title, content })
                });

                if (!response.ok) throw new Error('Failed to generate EPUB file.');

                const blob = await response.blob();
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = downloadUrl;
                a.download = title.replace(/[^a-zA-Z0-9ء-ي]/g, '_') + ".epub";
                document.body.appendChild(a);
                a.click();
                a.remove();

                statusDiv.style.background = '#064e3b';
                statusDiv.style.color = '#34d399';
                statusDiv.innerText = 'EPUB downloaded successfully!';
            } catch (error) {
                statusDiv.style.background = '#7f1d1d';
                statusDiv.style.color = '#fca5a5';
                statusDiv.innerText = 'Error: ' + error.message;
            }
        }
    </script>
</body>
</html>"""

def generate_epub_file(title, text_content, output_filename):
    book = epub.EpubBook()
    book.set_identifier(f'id_{uuid.uuid4().hex}')
    book.set_title(title)
    book.set_language('ar')
    book.add_author('Maissa Graphics')

    # تنسيق الفقرات والنصوص العربية بوضوح ودعم الاتجاه من اليمين لليسار
    formatted_paragraphs = "".join([f"<p>{p.strip()}</p>" for p in text_content.split('\n') if p.strip()])
    
    c = epub.EpubHtml(title=title, file_name='content.xhtml', lang='ar')
    c.content = f'<?xml version="1.0" encoding="utf-8"?>\n<html xmlns="http://www.w3.org/1999/xhtml" lang="ar" dir="rtl">\n<head><title>{title}</title></head>\n<body><div dir="rtl"><h2>{title}</h2>{formatted_paragraphs}</div></body>\n</html>'
    
    book.add_item(c)
    book.toc = (epub.Link('content.xhtml', title, 'intro'),)
    
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    style = 'BODY {direction: rtl; text-align: right; line-height: 1.6; font-family: Arial, sans-serif;}'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)
    
    book.spine = ['nav', c]
    epub.write_epub(output_filename, book, {})

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/create-epub', methods=['POST'])
def create_epub():
    data = request.json
    if not data or not data.get('title') or not data.get('content'):
        return jsonify({"error": "Title or content is missing"}), 400
        
    title = data.get('title').strip()
    content = data.get('content').strip()

    try:
        safe_title = "".join([c for c in title if c.isalnum() or c.isspace()]).strip()
        output_filename = f"{safe_title or 'novel'}.epub"
        
        generate_epub_file(title, content, output_filename)
        return send_file(output_filename, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
