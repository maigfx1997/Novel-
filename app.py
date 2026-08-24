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
    # دعم خاص لموقع Novlar
    # ---------------------------------------------------------
    if "novlar.com" in clean_url:
        soup = get_soup(clean_url)
        if not soup:
            return None, "Cannot access Novlar page"
        
        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Unknown"
        author = "Unknown"
        description = ""
        cover_url = ""

        # استخراج روابط الفصول من صفحة الفهرس
        chapter_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/chapter' in href or '/chap-' in href or '/read' in href:
                chapter_links.append(a['href'])
        
        chapter_links = list(dict.fromkeys(chapter_links))
        if not chapter_links:
            return None, "No chapters found on Novlar"

        all_chapters_html = []
        # الحد الأقصى للفصول (لتجنب انقطاع الخادم)
        for link in chapter_links[:30]:
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

    # ---------------------------------------------------------
    # المنطق العام للمواقع الأخرى (Uranus, إلخ)
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
    for link in chapter_links[:30]:  # حد أقصى 30 فصل
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
