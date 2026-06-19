import os
import json
import google.generativeai as genai
from datetime import datetime

# API Ayarları
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

TARGET_CHANNELS = ["TRT 1", "ATV", "STAR TV", "KANAL D", "SHOW TV", "TV8", "NOW"]

def get_epg_from_gemini(channel):
    # Google Arama yetkili model
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        tools=[{"google_search": {}}]
    )
    
    prompt = (f"Bugün {datetime.now().strftime('%Y-%m-%d')}. "
              f"'{channel}' kanalının bugün için güncel yayın akışını bul. "
              f"Veriyi şu JSON formatında ver: {{'programs': [{{'title': 'Program', 'startTime': 'HH:mm', 'endTime': 'HH:mm'}}]}} "
              f"HİÇBİR açıklama yapma. Eğer güncel veri bulamazsan boş liste [] dön.")
    
    try:
        response = model.generate_content(prompt)
        # Markdown etiketlerini temizle
        text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(text).get("programs", [])
    except Exception as e:
        print(f"Hata ({channel}): {e}")
        return []

def main():
    xml_content = '<?xml version="1.0" encoding="UTF-8"?><tv>\n'
    
    for ch in TARGET_CHANNELS:
        programs = get_epg_from_gemini(ch)
        
        xml_content += f'  <channel id="{ch}"><display-name>{ch}</display-name></channel>\n'
        for p in programs:
            date_str = datetime.now().strftime("%Y%m%d")
            s = p["startTime"].replace(":","") + "00 +0300"
            e = p["endTime"].replace(":","") + "00 +0300"
            xml_content += f'  <programme start="{date_str}{s}" stop="{date_str}{e}" channel="{ch}"><title>{p["title"]}</title></programme>\n'
    
    xml_content += '</tv>'
    
    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write(xml_content)

if __name__ == "__main__":
    main()
