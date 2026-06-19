import os
import json
from datetime import datetime
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

TARGET_CHANNELS = ["TRT 1", "ATV", "STAR TV", "KANAL D", "SHOW TV", "TV8", "NOW"]

def get_epg_from_gemini(channel):
    today = datetime.now().strftime('%d.%m.%Y')
    # "Kesin yayın akışı listesi" ifadesini vurguluyoruz
    prompt = (f"Bugün {today} tarihi. '{channel}' kanalının bugün yayınlanacak programlarını ve saatlerini "
              f"Türkiye yerel saatine göre internette ara ve bul. "
              f"Çıktıyı SADECE şu JSON formatında ver: {{'programs': [{{'title': 'Program Adı', 'startTime': 'HH:mm', 'endTime': 'HH:mm'}}]}} "
              f"Eğer saatler tam verilmemişse, mantıklı tahminler yürüt ama listeyi mutlaka doldur.")
    
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                response_mime_type="application/json"
            )
        )
        data = json.loads(response.text)
        return data.get("programs", [])
    except Exception as e:
        print(f"Hata ({channel}): {e}")
        return []

def main():
    xml_lines = ['<?xml version="1.0" encoding="UTF-8"?><tv>']
    
    for ch in TARGET_CHANNELS:
        programs = get_epg_from_gemini(ch)
        xml_lines.append(f'  <channel id="{ch}"><display-name>{ch}</display-name></channel>')
        
        # Eğer program gelmediyse, sistemin hata verdiğini anlamak yerine 
        # en azından boş bir blok oluşturuyoruz
        if not programs:
            print(f"Uyarı: {ch} için veri bulunamadı.")
            
        for p in programs:
            date_str = datetime.now().strftime("%Y%m%d")
            s = p["startTime"].replace(":","") + "00 +0300"
            e = p["endTime"].replace(":","") + "00 +0300"
            xml_lines.append(f'  <programme start="{date_str}{s}" stop="{date_str}{e}" channel="{ch}"><title>{p["title"]}</title></programme>')
    
    xml_lines.append('</tv>')
    
    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write("\n".join(xml_lines))

if __name__ == "__main__":
    main()
