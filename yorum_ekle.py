import json
import os
import google.generativeai as genai
from dotenv import load_dotenv

API_KEY = os.getenv("GEMINI_API_KEY")
GIRIS_DOSYASI = "ETIKETLI_VERI.json"
CIKIS_DOSYASI = "EGITIM_VERISI_GEMINI.json"
BATCH_SIZE = 10
MODEL_NAME = "gemini-3-flash-preview"

if not API_KEY:
    print("⚠️ HATA: API Anahtarı bulunamadı! .env dosyasını kontrol et.")

genai.configure(api_key=API_KEY)

SYSTEM_PROMPT = """Sen usta, profesyonel ve heyecanlı bir Türk e-spor satranç spikerisin. 
Sana verilen teknik verileri kullanarak, maçın o anını aksiyon filmi gibi Türkçe yorumlayacaksın.

HAYATİ KURALLAR:
1. SAF TÜRKÇE: "Oportunite", "respuesta", "already" gibi yabancı kelimeler KESİNLİKLE YASAK! Çeviri kokan cümleler kurma.
2. DOĞRU JARGON: Sadece "Şah", "Vezir", "Kale", "Fil", "At", "Piyon" kullan. "Kral" KESİNLİKLE DEME.
3. BAĞLAMI VE TAKTİĞİ ANLA: Veride "Açarak Şah", "Çatal", "Blunder" veya "Brilliant" gibi taktikler varsa buna mutlaka ÇILDIRARAK tepki ver! "Aman Allah'ım bir feda mı izliyoruz!" gibi spiker reaksiyonları göster. 
4. SKOR YORUMU: Skor +10 veya -10 gibi uçuk rakamlara ulaştıysa "Siyah zaten maçı kopardı" gibi doğal konuş.
5. ASLA İNGİLİZCE KELİME KULLANMA. ÇIKTIYI SADECE JSON FORMATINDA VER.

Format: [{"move": "hamle_adi", "comment": "Türkçe Spiker Yorumu"}]"""

model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    system_instruction=SYSTEM_PROMPT,
    generation_config=genai.types.GenerationConfig(
        temperature=0.5, 
        response_mime_type="application/json"
    )
)

CEVIRI_TAS = {
    "king": "Şah", "queen": "Vezir", "rook": "Kale", 
    "bishop": "Fil", "knight": "At", "pawn": "Piyon"
}
CEVIRI_KALITE = {
    "Brilliant": "Harika", "Excellent": "Mükemmel", 
    "Good Move": "İyi", "Mistake": "Hata", "Blunder": "Büyük Hata"
}

def vip_yorumlat():
    with open(GIRIS_DOSYASI, "r", encoding="utf-8") as f:
        ham_veriler = json.load(f)

    if os.path.exists(CIKIS_DOSYASI):
        with open(CIKIS_DOSYASI, "r", encoding="utf-8") as f:
            egitim_veriseti = json.load(f)
    else:
        egitim_veriseti = []

    islenen_sayisi = len(egitim_veriseti)
    print(f"emini Motoru Devrede, Kaldığı yer: {islenen_sayisi}/{len(ham_veriler)}")

    for i in range(islenen_sayisi, len(ham_veriler), BATCH_SIZE):
        batch = ham_veriler[i:i + BATCH_SIZE]
        
        batch_text_lines = []
        for j, v in enumerate(batch):
            tr_tas = CEVIRI_TAS.get(v['piece'], v['piece'])
            tr_kalite = CEVIRI_KALITE.get(v['move_quality'], v['move_quality'])
            taktik_str = ", ".join(v['tactical_motifs']) if v.get('tactical_motifs') else "Yok"
            tehdit_str = ", ".join(v['threatens']) if v.get('threatens') else "Yok"
            
            satir = (f"{j+1}. Hamle No: {v['fullmove_number']} | Sıra: {v['turn']} | "
                     f"Önceki: {v['previous_move']} -> Yapılan: {v['move_san']} ({tr_tas}) | "
                     f"Aşama: {v['phase']} | Kalite: {tr_kalite} | Skor: {v['eval_score']} | "
                     f"Taktik: {taktik_str} | Tehdit: {tehdit_str} | "
                     f"Yeme: {'Evet' if v['is_capture'] else 'Hayır'} | "
                     f"Durum: {'Mat' if v.get('is_mate') else 'Şah' if v.get('is_check') else 'Normal'}")
            batch_text_lines.append(satir)
            
        batch_text = "\n".join(batch_text_lines)
        print(f"Paketleniyor ({i}-{i+len(batch)})...")

        try:
            response = model.generate_content(f"Şu hamleleri yorumla:\n{batch_text}")
            
            yorumlar = json.loads(response.text)

            for idx, item in enumerate(yorumlar):
                if idx < len(batch):
                    v = batch[idx]
                    tr_tas = CEVIRI_TAS.get(v['piece'], v['piece'])
                    tr_kalite = CEVIRI_KALITE.get(v['move_quality'], v['move_quality'])
                    taktik_str = ", ".join(v['tactical_motifs']) if v.get('tactical_motifs') else "Yok"
                    tehdit_str = ", ".join(v['threatens']) if v.get('threatens') else "Yok"

                    egitim_veriseti.append({
                        "instruction": "Bir satranç spikeri gibi hamleyi teknik ve heyecanlı bir dille yorumla.",
                        "input": (
                            f"Hamle No: {v['fullmove_number']} | Sıra: {v['turn']} | "
                            f"Önceki Hamle: {v['previous_move']} | Yapılan Hamle: {v['move_san']} ({tr_tas}) | "
                            f"Aşama: {v['phase']} | Kalite: {tr_kalite} | Skor: {v['eval_score']} | "
                            f"Taktikler: {taktik_str} | Tehditler: {tehdit_str} | "
                            f"Yeme: {'Evet' if v['is_capture'] else 'Hayır'} | "
                            f"Durum: {'Mat' if v.get('is_mate') else 'Şah' if v.get('is_check') else 'Normal'}"
                        ),
                        "output": item['comment']
                    })

            with open(CIKIS_DOSYASI, "w", encoding="utf-8") as out:
                json.dump(egitim_veriseti, out, indent=4, ensure_ascii=False)
            
            print(f"{len(egitim_veriseti)} hamle tamamlandı!")

        except Exception as e:
            print(f"Ufak bir takılma oldu: {e}")
            print("3 saniye bekleyip devam ediliyor...")
            import time
            time.sleep(3)

if __name__ == "__main__":
    vip_yorumlat()