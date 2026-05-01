import json
import os
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- AYARLAR ---
load_dotenv()
API_KEY = "AIzaSyCr4d-7Wf664DnVc_5qDbVf-j6WTiVpA54"
INPUT_FILE = "HARIKA_HAMLELER_VERISI.json"  # Senin 550 hamlelik dosyan
OUTPUT_FILE = "YORUMLANMIS_MASTER_VERI.json"
BATCH_SIZE = 10  # Hız ve bağlam dengesi için 10'arlı gruplar
SAVE_EVERY = 50  # Her 50 hamlede bir diske kaydet

if not API_KEY:
    raise ValueError("⚠️ HATA: API Anahtarı bulunamadı! .env dosyasını kontrol et.")

client = genai.Client(api_key=API_KEY)

# --- SÖZLÜKLER (DOĞRU ETİKETLEME İÇİN) ---
CEVIRI_TAS = {
    "king": "Şah", "queen": "Vezir", "rook": "Kale", 
    "bishop": "Fil", "knight": "At", "pawn": "Piyon"
}
CEVIRI_KALITE = {
    "Brilliant": "Harika", "Excellent": "Mükemmel", 
    "Good Move": "İyi", "Mistake": "Hata", "Blunder": "Büyük Hata"
}

SYSTEM_PROMPT = """Sen usta, profesyonel ve tutkulu bir Türk e-spor satranç spikerisin. 
Görevin, sana verilen "Harika" veya "Mükemmel" hamleleri izleyiciyi heyecanlandıracak şekilde yorumlamak.

HAYATİ KURALLAR:
1. JARGON: Sadece "Şah", "Vezir", "Kale", "Fil", "At", "Piyon" kullan. "Kral" KESİNLİKLE YASAK.
2. DUYGU: Hamleler elit seviyede olduğu için "Aman Allah'ım!", "İnanılmaz bir feda!", "Tahta alev alıyor!" gibi tepkiler ver.
3. HALÜSİNASYON: Veride "Yeme: Hayır" ise taş alındığını söyleme. "Yeme: Evet" ise imha operasyonundan bahset.
4. DİL: Sadece saf Türkçe. "Respuesta", "Oportunite" gibi terimler kullanma.
5. FORMAT: Çıktıyı sadece JSON formatında, her hamle için bir "comment" içerecek şekilde ver.

Format: [{"comment": "Spikerin coşkulu yorumu"}]"""

def generate_comments_batch(batch_data):
    """Gemini'ye toplu hamle gönderir ve yorumları alır."""
    batch_text = ""
    for idx, item in enumerate(batch_data):
        # Input string'ini etiketleme kurallarına göre düzenliyoruz
        batch_text += f"{idx+1}. Hamle Verisi: {item['input']}\n"

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview", # En hızlı ve güncel model
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7,
                response_mime_type="application/json"
            ),
            contents=f"Şu elit hamleleri yorumla:\n{batch_text}"
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"❌ API Hatası: {e}")
        return None

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Hata: {INPUT_FILE} bulunamadı!")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        raw_dataset = json.load(f)

    # Varsa önceki çalışmaları yükle (Checkpoint)
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            final_dataset = json.load(f)
    else:
        final_dataset = []

    processed_count = len(final_dataset)
    print(f"🚀 İşlem başlıyor... ({processed_count}/{len(raw_dataset)} tamamlandı)")

    for i in range(processed_count, len(raw_dataset), BATCH_SIZE):
        batch = raw_dataset[i : i + BATCH_SIZE]
        print(f"📦 {i} - {i+len(batch)} arası yorumlanıyor...")

        results = generate_comments_batch(batch)
        
        if results:
            for idx, res in enumerate(results):
                if idx < len(batch):
                    # Orijinal veriyi al ve eğitim formatına sok
                    current_item = batch[idx]
                    
                    # Veri zaten 'input' olarak hazırlanmış geliyor (önceki koddan)
                    # Sadece output kısmını Gemini'den gelen yorumla dolduruyoruz
                    final_dataset.append({
                        "instruction": "Bir satranç spikeri gibi hamleyi teknik ve heyecanlı bir dille yorumla.",
                        "input": current_item['input'],
                        "output": res['comment']
                    })
            
            # Kaydetme periyodu (SAVE_EVERY = 50)
            if len(final_dataset) % SAVE_EVERY == 0 or (i + BATCH_SIZE) >= len(raw_dataset):
                with open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
                    json.dump(final_dataset, out, indent=4, ensure_ascii=False)
                print(f"💾 Checkpoint: {len(final_dataset)} hamle kaydedildi.")
        
        time.sleep(2) # Rate limit koruması

    print(f"🎉 İşlem bitti! Toplam {len(final_dataset)} elit hamle yorumlandı: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()