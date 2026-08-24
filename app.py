import requests

def get_wattpad_content(url):
    # ترويسات المتصفح الحقيقي (مهم جداً لتجاوز الحماية)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.wattpad.com/',
        'DNT': '1',
    }
    
    # تنظيف الرابط من أي إضافات (مثل utm_source)
    clean_url = url.split('?')[0] 
    clean_url = clean_url.rstrip('/') # إزالة الشرطة المائلة في النهاية إن وجدت

    try:
        response = requests.get(clean_url, headers=headers, timeout=10)
        
        # إذا تم الحظر أو لم يجد الصفحة
        if response.status_code != 200:
            return None, f"Error fetching page (Status Code: {response.status_code})"
            
        # 2. استخراج معرف الرواية ومعرف الفصل
        # (يجب أن يكون لديك كود لاستخراج الفصول وتحميلها)
        # واتباد يعتمد على JavaScript، لذلك غالباً تحتاج لتحليل الروابط الداخلية
        # بدلاً من الاعتماد على الصفحة الرئيسية فقط.
        
        return response.text, None
        
    except Exception as e:
        return None, f"Error: {str(e)}"
