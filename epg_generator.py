# -*- coding: utf-8 -*-
import os
import json
import time
import urllib.request
from datetime import datetime

# --- YAPILANDIRMA ---
TARGET_CHANNELS = ["TRT 1", "ATV", "STAR TV", "KANAL D", "SHOW TV", "TV8", "NOW"]
CURRENT_DATE_STR = datetime.now().strftime("%Y-%m-%d")

def fetch_epg_from_gemini(channel_name, api_key):
    print(f"-> {channel_name} için sorgulanıyor...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={api_key}"
    
    # Sorguyu basitleştirdik ve formatı "katı" hale getirdik
    prompt = f"Bugün tarih: {CURRENT_DATE_STR}. '{channel_name}' kanalının bugünkü yayın akışını Türkiye saatiyle (UTC+3) bul. Lütfen cevabını sadece ve sadece şu JSON formatında ver, başka hiçbir yazı ekleme: {{ 'programs': [ {{ 'title': 'Program Adı', 'startTime': 'YYYY-MM-DD HH:mm', 'endTime': 'YYYY-MM-DD HH:mm' }} ] }}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"google_search": {}}],
        "generationConfig": {
            "temperature": 0.2, # Daha tutarlı yanıt için düşürdük
            "responseMimeType": "application/json"
        }
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=50) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            text_response = res_data['candidates'][0]['content']['parts'][0]['text']
            # Temizlik: Eğer API markdown içine gömülü JSON dönerse diye temizliyoruz
            text_response = text_response.replace('```json', '').replace('```', '').strip()
            parsed_data = json.loads(text_response)
            return parsed_data["programs"]
    except Exception as e:
        print(f"   [HATA] API Sorgusu başarısız: {e}")
        # Hata durumunda boş liste dönüyoruz ki yedekler devreye girsin
        return []

def get_fallback_schedule():
    # Hata durumunda kullanılacak yedek
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
        if not programs:
            programs = get_fallback_schedule()
        
        xml_content += f'  <channel id="{ch}"><display-name>{ch}</display-name></channel>\n'
        for p in programs:
            xml_content += f'  <programme start="{p["startTime"].replace("-","").replace(":","").replace(" ","")}00 +0300" stop="{p["endTime"].replace("-","").replace(":","").replace(" ","")}00 +0300" channel="{ch}"><title>{p["title"]}</title></programme>\n'
    
    xml_content += '</tv>'
    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write(xml_content)

if __name__ == "__main__":
    main()
