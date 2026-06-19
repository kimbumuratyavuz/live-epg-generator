# -*- coding: utf-8 -*-
import os
import json
import urllib.request
from datetime import datetime

# --- YAPILANDIRMA ---
TARGET_CHANNELS = ["TRT 1", "ATV", "STAR TV", "KANAL D", "SHOW TV", "TV8", "NOW"]

def get_current_date():
    return datetime.now().strftime("%Y-%m-%d")

def fetch_epg_from_gemini(channel_name, api_key):
    current_date = get_current_date()
    # Modeli güncel ve daha yetenekli bir sürümle değiştiriyoruz
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={api_key}"
    
    # Promptu daha detaylı hale getirerek gerçek veri zorunluluğu ekliyoruz
    prompt = (f"Bugün 19 Haziran 2026. {channel_name} kanalının gerçek ve güncel yayın akışını "
              f"Türkiye yerel saatiyle (UTC+3) internetten araştırarak bul. "
              f"Sadece JSON formatında şu yapıda dön: {{'programs': [{{'title': 'Program Adı', 'startTime': '{current_date} HH:mm', 'endTime': '{current_date} HH:mm'}}]}}. "
              f"Veri bulamazsan boş liste döndür ama asla sahte veya şablon veri uydurma.")

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"google_search": {}}],
        "generationConfig": {
            "temperature": 0.0, # Yaratıcılığı sıfıra indiriyoruz (sadece gerçek veri)
            "responseMimeType": "application/json"
        }
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=60) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            text = res_data['candidates'][0]['content']['parts'][0]['text']
            parsed = json.loads(text.replace('```json', '').replace('```', '').strip())
            
            programs = parsed.get("programs", [])
            if not programs:
                print(f"   [UYARI] {channel_name} için gerçek veri bulunamadı.")
            return programs
    except Exception as e:
        print(f"API hatası ({channel_name}): {e}")
        return None

def get_fallback_schedule():
    d = get_current_date()
    return [
        {"title": "Güne Başlarken", "startTime": f"{d} 07:00", "endTime": f"{d} 12:00"},
        {"title": "Gündüz Kuşağı", "startTime": f"{d} 12:00", "endTime": f"{d} 18:00"},
        {"title": "Ana Haber", "startTime": f"{d} 19:00", "endTime": f"{d} 20:00"},
        {"title": "Prime Time", "startTime": f"{d} 20:00", "endTime": f"{d} 23:59"}
    ]

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: return

    xml_lines = ['<?xml version="1.0" encoding="UTF-8"?><tv>']
    
    for ch in TARGET_CHANNELS:
        programs = fetch_epg_from_gemini(ch, api_key)
        # Eğer gerçek veri gelmediyse yedek veriye düş
        if not programs: 
            programs = get_fallback_schedule()
        
        xml_lines.append(f'  <channel id="{ch}"><display-name>{ch}</display-name></channel>')
        for p in programs:
            # Zaman formatını temizleyip XMLTV uyumlu hale getiriyoruz
            s = p["startTime"].replace("-","").replace(":","").replace(" ","") + "00 +0300"
            e = p["endTime"].replace("-","").replace(":","").replace(" ","") + "00 +0300"
            xml_lines.append(f'  <programme start="{s}" stop="{e}" channel="{ch}"><title>{p["title"]}</title></programme>')
    
    xml_lines.append('</tv>')
    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write("\n".join(xml_lines))

if __name__ == "__main__":
    main()
