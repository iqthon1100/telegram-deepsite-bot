import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# الحصول على رمز API من المتغيرات البيئية
TOKEN = os.environ.get("TELEGRAM_TOKEN")

# عنوان DeepSite
DEEPSITE_URL = "https://enzostvs-deepsite.hf.space/"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إرسال رسالة عند تنفيذ أمر /start."""
    user = update.effective_user
    await update.message.reply_html(
        f"مرحباً {user.mention_html()}! أنا بوت يساعدك في إنشاء مواقع ويب باستخدام DeepSite. أرسل لي وصفاً لموقع الويب الذي تريد إنشاءه."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إرسال رسالة عند تنفيذ أمر /help."""
    await update.message.reply_text(
        "أرسل لي وصفاً لموقع الويب الذي تريد إنشاءه، وسأقوم بإنشائه لك باستخدام DeepSite.\n\n"
        "مثال: أنشئ موقع ويب شخصي لمصمم جرافيك يعرض أعماله"
    )

async def generate_website(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إرسال طلب إلى DeepSite وإرجاع النتيجة."""
    progress_message = await update.message.reply_text(
        "جاري إنشاء موقع الويب... قد يستغرق هذا بضع دقائق. يرجى الانتظار."
    )
    
    user_input = update.message.text
    
    try:
        # محاولة استخدام API مباشرة (إذا كان متاحاً)
        api_url = "https://enzostvs-deepsite.hf.space/api/predict"
        payload = {
            "data": [user_input]
        }
        
        # إرسال الطلب إلى API
        response = requests.post(api_url, json=payload, timeout=300)  # زيادة مهلة الانتظار إلى 5 دقائق
        
        if response.status_code == 200:
            # تحليل الاستجابة
            result = response.json()
            
            # استخراج كود HTML من النتيجة
            html_code = result.get('data', [''])[0]
            
            # حفظ كود HTML في ملف مؤقت
            temp_file_path = "website.html"
            with open(temp_file_path, "w", encoding="utf-8") as f:
                f.write(html_code)
            
            # إرسال ملف HTML
            await progress_message.edit_text("تم إنشاء موقع الويب بنجاح! جاري إرسال النتائج...")
            await update.message.reply_document(
                document=open(temp_file_path, "rb"),
                caption="كود HTML لموقع الويب. يمكنك فتح هذا الملف في أي متصفح أو استضافته على منصة مثل GitHub Pages."
            )
            
            # إرسال رابط لمعاينة الموقع
            preview_message = (
                "يمكنك معاينة الموقع باستخدام إحدى الطرق التالية:\n\n"
                "1. فتح الملف HTML على جهازك\n"
                "2. استخدام خدمة مثل https://htmlpreview.github.io/ لمعاينة الموقع عبر الإنترنت\n"
                "3. استضافة الموقع على GitHub Pages أو Netlify"
            )
            await update.message.reply_text(preview_message)
            
            # حذف الملف المؤقت
            os.remove(temp_file_path)
            
        else:
            # إذا فشل استخدام API، نرسل رسالة خطأ
            await progress_message.edit_text(
                f"حدث خطأ أثناء الاتصال بـ DeepSite. الرمز: {response.status_code}\n\n"
                "يمكنك زيارة الموقع مباشرة واستخدامه: https://enzostvs-deepsite.hf.space/"
            )
    
    except Exception as e:
        # في حالة حدوث أي خطأ، نرسل رسالة بديلة
        await progress_message.edit_text(
            f"حدث خطأ: {str(e)}\n\n"
            "يمكنك زيارة الموقع مباشرة واستخدامه: https://enzostvs-deepsite.hf.space/"
        )

def main() -> None:
    """تشغيل البوت."""
    # إنشاء التطبيق وإضافة المعالجات
    application = Application.builder().token(TOKEN).build()

    # أوامر مختلفة
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # معالجة الرسائل النصية
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_website))

    # تشغيل البوت باستخدام webhook إذا كان PORT موجوداً (للاستضافة)، وإلا استخدم polling (للتطوير المحلي)
    port = int(os.environ.get('PORT', 5000))
    
    if os.environ.get('RENDER'):
        # استخدام webhook على Render
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=os.environ.get("WEBHOOK_URL"),
        )
    else:
        # استخدام polling للتطوير المحلي
        application.run_polling()

if __name__ == "__main__":
    main()
