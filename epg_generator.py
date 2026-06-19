# -*- coding: utf-8 -*-
import os
import re
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

# --- YAPILANDIRMA ---
# EPG'si çekilecek kanal listesi (Temizlenmiş adlarıyla)
# Buraya M3U dosyanızdaki önemli kanalları ekleyin
TARGET_CHANNELS = [
    "TRT 1", "ATV", "STAR TV", "KANAL D", "SHOW TV", "TV8", "NOW", "TRT HABER", 
    "HABERTÜRK", "CNN TÜRK", "TRT BELGESEL", "TRT SPOR", "NTV", "SÖZCÜ TV"
]

# EPG'nin geçerli olacağı tarih (Bugün)
CURRENT_DATE = datetime.now()
CURRENT_DATE_STR = CURRENT_DATE.strftime("%Y-%m-%d")

def clean_channel_name(name):
    """Kanal isimlerindeki fazlalıkları temizler (TRT 1 (YEDEK) -> TRT 1)"""
    if not name:
        return ""
    clean = name
    clean = re.sub(r'^(TR\s*[:|_-]\s*)', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\s*[\(\[][^\]\)]*[\]\)]', '', clean) # Parantez içlerini siler
    
    # Gereksiz kelimeleri sil
    trash = ["hd", "sd", "uhd", "4k", "yedek", "backup", "fhd", "hevc", "1080p", "720p"]
    for word in trash:
        clean = re.sub(r'\b' + word + r'\b', '', clean, flags=re.IGNORECASE)
        
    return " ".join(clean.split()).strip()

def get_fallback_schedule(channel_name):
    """API hatası durumunda üretilecek yedek yayın akışı"""
    return [
        {"title": "Güne Başlarken", "description": "Günün ilk gelişmeleri ve gazete manşetleri.", "startTime": f"{CURRENT_DATE_STR} 07:00", "endTime": f"{CURRENT_DATE_STR} 09:00"},
        {"title": "Sabah Kuşağı", "description": "Hayata dair sohbetler, konuklar ve güncel paylaşımlar.", "startTime": f"{CURRENT_DATE_STR} 09:00", "endTime": f"{CURRENT_DATE_STR} 12:00"},
        {"title": "Gün Ortası Haberleri", "description": "Gelişmeler ve sıcak bağlantılar.", "startTime": f"{CURRENT_DATE_STR} 12:00", "endTime": f"{CURRENT_DATE_STR} 13:00"},
        {"title": "Günün Dizisi (Tekrar)", "description": "Kaçırdığınız popüler dizinin heyecan dolu anları.", "startTime": f"{CURRENT_DATE_STR} 13:00", "endTime": f"{CURRENT_DATE_STR} 16:00"},
        {"title": "Aktüel Yaşam", "description": "Kültür, sanat ve yaşam haberleri.", "startTime": f"{CURRENT_DATE_STR} 16:00", "endTime": f"{CURRENT_DATE_STR} 19:00"},
        {"title": "Ana Haber Bülteni", "description": "Günün en sıcak gelişmeleri ve analizler.", "startTime": f"{CURRENT_DATE_STR} 19:00", "endTime": f"{CURRENT_DATE_STR} 21:00"},
        {"title": "Sinema Kuşağı / Prime Time", "description": "Ekran başındakileri kilitleyecek harika bir yapım.", "startTime": f"{CURRENT_DATE_STR} 21:00", "endTime": f"{CURRENT_DATE_STR} 23:59"}
    ]

def fetch_epg_from_gemini(channel_name, api_key):
    """Gemini API kullanarak Google Search Grounding ile gerçek yayın akışını çeker"""
    print(f"-> {channel_name} için gerçek zamanlı yayın akışı sorgulanıyor...")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={api_key}"
    
    user_query = f'Find the actual, official Turkish television schedule (yayın akışı) for "{channel_name}" on {CURRENT_DATE_STR}. Ensure timings are accurate local Turkey time (UTC+3).'
    system_prompt = "You are a TV Guide EPG compiler. Search Google for today's TV schedule. Return strictly JSON with 'programs' list containing 'title', 'description', 'startTime' (YYYY-MM-DD HH:mm), and 'endTime' (YYYY-MM-DD HH:mm). No markdown format other than the raw JSON."

    payload = {
        "contents": [{"parts": [{"text": user_query}]}],
        "tools": [{"google_search": {}}],
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "programs": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "title": {"type": "STRING"},
                                "description": {"type": "STRING"},
                                "startTime": {"type": "STRING"},
                                "endTime": {"type": "STRING"}
                            },
                            "required": ["title", "startTime", "endTime"]
                        }
                    }
                },
                "required": ["programs"]
            }
        }
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=30) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            text_response = res_data['candidates'][0]['content']['parts'][0]['text']
            parsed_data = json.loads(text_response)
            if "programs" in parsed_data and len(parsed_data["programs"]) > 0:
                print(f"   [Başarılı] {len(parsed_data['programs'])} program çekildi.")
                return parsed_data["programs"]
    except Exception as e:
        print(f"   [Hata] Yapay zeka sorgusu başarısız oldu: {e}. Yedek şablon kullanılıyor.")
    
    return get_fallback_schedule(channel_name)

def escape_xml(text):
    """XML için geçersiz karakterleri temizler"""
    if not text:
        return ""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;")

def to_xmltv_time(time_str):
    """Zaman formatını XMLTV standardına dönüştürür"""
    digits = re.sub(r'[^0-9]', '', time_str)
    if len(digits) >= 12:
        return f"{digits[:12]}00 +0300"
    return f"{CURRENT_DATE_STR.replace('-', '')}000000 +0300"

def main():
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("[Hata] GEMINI_API_KEY bulunamadı! Lütfen Secrets ayarlarına ekleyin.")
        return

    epg_store = {}
    for channel in TARGET_CHANNELS:
        clean_name = clean_channel_name(channel)
        programs = fetch_epg_from_gemini(clean_name, api_key)
        epg_store[clean_name] = programs
        time.sleep(2) # API limitlerine takılmamak için bekleme süresi

    # XMLTV Dosyasını Oluştur
    print("-> XMLTV dosyası derleniyor...")
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<!DOCTYPE tv SYSTEM "xmltv.dtd">\n'
    xml_content += '<tv generator-info-name="OtomatikEPGMotoru">\n'

    # 1. Kanallar
    for ch_name in epg_store.keys():
        xml_content += f'  <channel id="{ch_name}">\n'
        xml_content += f'    <display-name lang="tr">{escape_xml(ch_name)}</display-name>\n'
        xml_content += '  </channel>\n'

    # 2. Programlar
    for ch_name, programs in epg_store.items():
        for prog in programs:
            start = to_xmltv_time(prog['startTime'])
            stop = to_xmltv_time(prog['endTime'])
            title = escape_xml(prog['title'])
            desc = escape_xml(prog.get('description', 'Yayın Akışı Programı'))
            
            xml_content += f'  <programme start="{start}" stop="{stop}" channel="{ch_name}">\n'
            xml_content += f'    <title lang="tr">{title}</title>\n'
            xml_content += f'    <desc lang="tr">{desc}</desc>\n'
            xml_content += '  </programme>\n'

    xml_content += '</tv>'

    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write(xml_content)

    print("[Tamamlandı] epg.xml başarıyla oluşturuldu!")

if __name__ == "__main__":
    main()
