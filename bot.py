import os
import re
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# استيراد الدوال الموجودة في app.py
from app import scrape_novel_from_url, convert_to_epub, convert_to_pdf, convert_to_txt, convert_to_azw3, convert_to_html

# ⚠️ ضع التوكن الجديد هنا (الذي ستحصل عليه بعد الضغط على Revoke)
TOKEN = "8261617329:AAFPC9dI8ofxIl8FQjXYTUq1ckBjL0wBbQ0"

# إنشاء خادم ويب مصغر فقط للاستماع للمنفذ
health_app = Flask(__name__)

@health_app.route('/')
def home():
    return "Bot is running!"

def run_health_server():
    health_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر البداية"""
    await update.message.reply_text(
        "مرحباً! 👋\n"
        "أرسل لي رابط الرواية أو الفانفيك، وسأقوم بتحويله إلى كتاب إلكتروني.\n\n"
        "📚 الصيغ المتوفرة:\n"
        "- EPUB (أبل)\n"
        "- AZW3 (كيندل)\n"
        "- PDF\n"
        "- TXT\n"
        "- HTML\n\n"
        "⚠️ ملاحظة: يرجى إرسال رابط نظيف بدون إضافات."
    )

async def convert_novel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال الرابط وتحويله"""
    url = update.message.text.strip()
    status_message = await update.message.reply_text("⏳ جاري تحميل الرواية وتجهيز الملف... (قد يستغرق ذلك بضع دقائق)")

    try:
        # 1. جلب البيانات من الرابط
        book_data, error = scrape_novel_from_url(url)
        
        if error:
            await status_message.edit_text(f"❌ خطأ: {error}")
            return

        # 2. تحويل الصيغة الافتراضية (EPUB)
        output_file = "book_output.epub"
        convert_to_epub(book_data, output_file)

        # 3. إرسال الملف للمستخدم
        with open(output_file, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=f"{book_data['title']}.epub",
                caption="✅ تم التحويل بنجاح!"
            )
        
        # حذف الملف من السيرفر بعد إرساله
        os.remove(output_file)

    except Exception as e:
        await status_message.edit_text(f"❌ خطأ غير متوقع: {str(e)}")

if __name__ == '__main__':
    # تشغيل خادم الصحة في الخلفية (ليعطي Render المنفذ المطلوب)
    threading.Thread(target=run_health_server, daemon=True).start()
    
    # تشغيل البوت
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, convert_novel))
    print("🤖 البوت يعمل الآن...")
    application.run_polling()
