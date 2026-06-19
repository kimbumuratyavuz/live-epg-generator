import os
import sys
import google.generativeai as genai

def setup_gemini():
    """
    GitHub Secrets'tan gelen API anahtarını ortam değişkeninden alır
    ve Gemini istemcisini yapılandırır.
    """
    # GitHub Actions'da env olarak tanımlanan değişkeni çekiyoruz
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        print("HATA: GEMINI_API_KEY ortam değişkeni bulunamadı.")
        print("Lütfen GitHub Actions workflow dosyanızda 'env' kısmında tanımladığınızdan emin olun.")
        sys.exit(1)

    try:
        # API anahtarını yapılandır
        genai.configure(api_key=api_key)
        
        # Model tanımlaması
        model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
        return model
    except Exception as e:
        print(f"HATA: API yapılandırması sırasında bir sorun oluştu: {e}")
        sys.exit(1)

def generate_content(prompt):
    """
    Verilen prompt ile içerik üretir.
    """
    model = setup_gemini()
    
    try:
        response = model.generate_content(prompt)
        # Hata kontrolü (Safety settings veya içerik kısıtlamaları için)
        if response.text:
            return response.text
        else:
            return "İçerik üretilemedi veya boş döndü."
    except Exception as e:
        return f"Gemini API hatası: {e}"

if __name__ == "__main__":
    # Test amaçlı basit bir prompt
    test_prompt = "Merhaba, GitHub Actions üzerinden başarıyla çalıştığını onayla."
    result = generate_content(test_prompt)
    print("Sonuç:", result)
