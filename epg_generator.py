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
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={api_key}"
    
    # Arama sorgusunu güncel tarihle daha spesik hale getirdik
    search_query = f"{channel_name} yayın akışı {CURRENT_DATE_STR}"
    
    prompt = (f"Bugün tarih: {CURRENT_DATE_STR}. Google Search kullanarak '{channel_name}' kanalının "
              f"bugün ({CURRENT_DATE_STR}) Türkiye saatiyle (UTC+3) güncel yayın akışını bul. "
              f"Eğer kesin veriye ulaşamazsan, kanalın tipik günlük yayın akışını temsil eden mantıklı bir liste oluştur. "
              f"Cevabını sadece ve sadece şu JSON formatında ver, başka hiçbir açıklama yapma: "
              f"{{ 'programs': [ {{ 'title': 'Program Adı', 'startTime': 'YYYY-MM-DD HH:mm', 'endTime': 'YYYY-MM-DD HH:mm' }} ] }}")

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"google_search": {}}],
        "generationConfig": {
            "temperature": 0.1, 
            "responseMimeType": "application/json"
        }
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=60) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            text_response = res_data['candidates'][0]['content']['parts'][0]['text']
            text_response = text_response.replace('```json', '').replace('```', '').strip()
            parsed_data = json.loads(text_response)
            return parsed_data.get("programs", [])
    except Exception as e:
        print(f"   [HATA] API Sorgusu başarısız veya veri dönmedi: {e}")
        return []

def get_fallback_schedule():
    return [
        {"title": "Güne Başlarken", "startTime": f"{CURRENT_DATE_STR} 07:00", "endTime": f"{CURRENT_DATE_STR} 09:00"},
        {"title": "Haber Bülteni", "startTime": f"{CURRENT_DATE_STR} 09:00", "endTime": f"{CURRENT_DATE_STR} 12:00"},
        {"title": "Güncel Programlar", "startTime": f"{CURRENT_DATE_STR} 12:00", "endTime": f"{CURRENT_DATE_STR} 18:00"},
        {"title": "Ana Haber", "startTime": f"{CURRENT_DATE_STR} 19:00", "endTime": f"{CURRENT_DATE_STR} 21:00"},
        {"title": "Prime Time", "startTime": f"{CURRENT_DATE_STR} 21:00", "endTime": f"{CURRENT_DATE_STR} 23:59"}
    ]

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    xml_content = '<?xml version="1.0" encoding="UTF-8"?><tv>\n'
    
    for ch in TARGET_CHANNELS:
        programs = fetch_epg_from_gemini(ch, api_key)
        
        # Eğer API boş liste döndürürse yedek veriyi zorunlu kıl
        if not programs:
            print(f"   ! {ch} için yedek akış kullanılıyor.")
            programs = get_fallback_schedule()
        
        xml_content += f'  <channel id="{ch}"><display-name>{ch}</display-name></channel>\n'
        for p in programs:
            start_fmt = p["startTime"].replace("-","").replace(":","").replace(" ","")
            stop_fmt = p["endTime"].replace("-","").replace(":","").replace(" ","")
            xml_content += f'  <programme start="{start_fmt}00 +0300" stop="{stop_fmt}00 +0300" channel="{ch}"><title>{p["title"]}</title></programme>\n'
    
    xml_content += '</tv>'
    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write(xml_content)
    print("İşlem tamamlandı: epg.xml güncellendi.")

if __name__ == "__main__":
    main()
