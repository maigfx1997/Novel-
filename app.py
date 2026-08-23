
def process_single_chapter(ch_data):
    idx, ch_title, ch_url = ch_data
    try:
        res = requests.get(ch_url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.content, 'html.parser')
            
            # البحث عن حاوية نص الفصل بدقة في واتباد والمواقع الأخرى
            content_div = soup.find('div', class_=lambda x: x and ('part-text' in x or 'reading-content' in x or 'story-text' in x or 'entry-content' in x))
            if not content_div:
                content_div = soup.find('div', class_='story-content')
            if not content_div:
                content_div = soup
            
            html_parts = []
            text_parts = []
            
            # استخراج الفقرات النصية الحقيقية للفصل فقط وتجنب القوائم الجانبية
            paragraphs = content_div.find_all(['p', 'div']) if content_div else []
            for el in paragraphs:
                # التأكد من أن العنصر يحتوي على نص حقيقي وليس قائمة تصفح
                if el.name == 'p' or (el.name == 'div' and len(el.get('class', [])) == 0):
                    txt = clean_text(el.get_text())
                    if len(txt) > 20 and not any(k in txt for k in ['Ranks', '#top', 'Completed', 'Starting date']):
                        html_parts.append(f'<p>{txt}</p>')
                        text_parts.append(txt)
            
            return idx, ch_title, "\n".join(html_parts), "\n\n".join(text_parts)
    except:
        pass
    return idx, ch_title, "", ""
