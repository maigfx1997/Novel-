def scrape_universal_metadata(url):
    # التأكد من أن الرابط يبدأ بـ http
    if not url.startswith('http'):
        raise Exception("الرابط غير صحيح، يجب أن يبدأ بـ https://")
        
    res = requests.get(url, headers=HEADERS, timeout=10)
    if res.status_code != 200:
        raise Exception(f"فشل الاتصال بالموقع، الرمز: {res.status_code}")
        
    soup = BeautifulSoup(res.content, 'html.parser')
    
    title = "رواية_واتباد"
    title_tag = soup.find('meta', property='og:title') or soup.find('h1')
    if title_tag:
        title = clean_text(title_tag.get('content') if title_tag.get('content') else title_tag.text)
    
    desc = ""
    desc_tag = soup.find('meta', property='og:description')
    if desc_tag:
        desc = clean_text(desc_tag.get('content'))
    
    cover_url = None
    cover_tag = soup.find('meta', property='og:image')
    if cover_tag:
        cover_url = cover_tag.get('content')

    chapters_data = []
    seen_links = set()
    
    # استخراج روابط الفصول الخاصة بـ واتباد أو المواقع الأخرى بدقة
    for a in soup.find_all('a', href=True):
        href = a.get('href', '')
        text = clean_text(a.get_text())
        # البحث عن روابط الفصول الفعلية وتجنب الروابط الجانبية
        if '/story/' in href or '/chapter/' in href or '10-' in href or '20-' in href:
            full_link = urljoin(url, href)
            if full_link not in seen_links and full_link != url and '#' not in href:
                seen_links.add(full_link)
                chapters_data.append((text or f"فصل", full_link))
                
    # إذا لمש يتم العثور على فصول متعددة، نعتبر الصفحة الحالية هي الفصل الوحيد
    if not chapters_data:
        chapters_data = [(title, url)]
        
    return title, desc, cover_url, chapters_data[:30]

