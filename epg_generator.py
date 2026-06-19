import os
import json
from datetime import datetime
from google import genai
from google.genai import types

# İstemciyi API anahtarı ile başlat
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

TARGET_CHANNELS = ["TRT 1", "ATV", "STAR TV", "KANAL D", "SHOW TV", "TV8", "NOW"]

def get_epg_from_gemini(channel):
    today = datetime.now().strftime('%Y-%m-%d')
    prompt = (f"Bugün {today}. '{channel}' kanalının bugün için güncel yayın akışını bul. "
              f"Veriyi şu JSON formatında ver: {{'programs': [{{'title': 'Program Adı', 'startTime': 'HH:mm', 'endTime': 'HH:mm'}}]}} "
              f"Hiçbir açıklama yapma. Eğer güncel veri bulamazsan boş liste [] dön.")
    
    try:
        # Google Search aracı aktif edilmiş model çağrısı
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        # JSON yanıtını temizle ve ayrıştır
        text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(text).get("programs", [])
    except Exception as e:
        print(f"Hata ({channel}): {e}")
        return []

def main():
    xml_lines = ['<?xml version="1.0" encoding="UTF-8"?><tv>']
    
    for ch in TARGET_CHANNELS:
        programs = get_epg_from_gemini(ch)
        xml_lines.append(f'  <channel id="{ch}"><display-name>{ch}</display-name></channel>')
        
        for p in programs:
            date_str = datetime.now().strftime("%Y%m%d")
            # Saat formatını XMLTV uyumlu hale getir
            s = p["startTime"].replace(":","") + "00 +0300"
            e = p["endTime"].replace(":","") + "00 +0300"
            xml_lines.append(f'  <programme start="{date_str}{s}" stop="{date_str}{e}" channel="{ch}"><title>{p["title"]}</title></programme>')
    
    xml_lines.append('</tv>')
    
    # Dosyayı kaydet
    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write("\n".join(xml_lines))
    print("epg.xml dosyası başarıyla oluşturuldu.")

if __name__ == "__main__":
    main()
