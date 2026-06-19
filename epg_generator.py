# -*- coding: utf-8 -*-
import os
import json
import urllib.request
from datetime import datetime

# --- YAPILANDIRMA ---
TARGET_CHANNELS = ["TRT 1", "ATV", "STAR TV", "KANAL D", "SHOW TV", "TV8", "NOW"]
CURRENT_DATE_STR = datetime.now().strftime("%Y-%m-%d")

def fetch_epg_from_gemini(channel_name, api_key):
    print(f"-> {channel_name} için gerçek zamanlı yayın akışı sorgulanıyor...")
    # API modelini güncel tutuyoruz
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={api_key}"
    
    # API'ye çok daha katı bir yapılandırma talimatı veriyoruz
    prompt = (f"Bugün {CURRENT_DATE_STR}. '{channel_name}' kanalının bugün için güncel yayın akışını "
              f"Türkiye saatiyle (UTC+3) bul. Eğer tam veriye ulaşamazsan, kanalın o günkü "
              f"yayın formatına uygun (sabah haberleri, kuşak programları, ana haber, dizi/program) "
              f"mantıklı bir liste oluştur. "
              f"Çıktıyı SADECE ve SADECE geçerli bir JSON objesi olarak ver: "
              f"{{ 'programs': [ {{ 'title': 'Program Adı', 'startTime': 'YYYY-MM-DD HH:mm', 'endTime': 'YYYY-MM-DD HH:mm' }} ] }}. "
              f"Başka hiçbir metin veya açıklama ekleme.")

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"google_search": {}}],
        "generationConfig": {
            "temperature": 0.05, # Yaratıcılığı minimize ettik
            "responseMimeType": "application/json"
        }
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=60) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            
            # API yanıtını parçalayıp güvenli bir şekilde alıyoruz
            text_response = res_data['candidates'][0]['content']['parts'][0]['text']
            
            # JSON temizleme: Gereksiz markdown etiketlerini at
            clean_json = text_response.replace('```json', '').replace('```', '').strip()
            parsed_data = json.loads(clean_json)
            
            programs = parsed_data.get("programs", [])
            if programs:
                return programs
            return []
    except Exception as e:
        print(f"   [HATA] {channel_name} için veri alınamadı: {e}")
        return []

def get_fallback_schedule():
    # API tamamen başarısız olursa kullanılacak yedek liste
    return [
        {"title": "Sabah Kuşağı", "startTime": f"{CURRENT_DATE_STR} 07:00", "endTime": f"{CURRENT_DATE_STR} 12:00"},
        {"title": "Gündüz Programı", "startTime": f"{CURRENT_DATE_STR} 12:00", "endTime": f"{CURRENT_DATE_STR} 18:00"},
        {"title": "Ana Haber", "startTime": f"{CURRENT_DATE_STR} 19:00", "endTime": f"{CURRENT_DATE_STR} 20:00"},
        {"title": "Akşam Kuşağı", "startTime": f"{CURRENT_DATE_STR} 20:00", "endTime": f"{CURRENT_DATE_STR} 23:59"}
    ]

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("API Anahtarı bulunamadı!")
        return

    xml_content = '<?xml version="1.0" encoding="UTF-8"?><tv>\n'
    
    for ch in TARGET_CHANNELS:
        programs = fetch_epg_from_gemini(ch, api_key)
        
        if not programs:
            print(f"   ! {ch} için yedek veriye geçiliyor.")
            programs = get_fallback_schedule()
        
        xml_content += f'  <channel id="{ch}"><display-name>{ch}</display-name></channel>\n'
        for p in programs:
            # Tarih/Saat formatını XML standartlarına uygun hale getir
            s = p["startTime"].replace("-","").replace(":","").replace(" ","")
            e = p["endTime"].replace("-","").replace(":","").replace(" ","")
            xml_content += f'  <programme start="{s}00 +0300" stop="{e}00 +0300" channel="{ch}"><title>{p["title"]}</title></programme>\n'
    
    xml_content += '</tv>'
    
    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write(xml_content)
    print("EPG dosyası başarıyla güncellendi.")

if __name__ == "__main__":
    main()
