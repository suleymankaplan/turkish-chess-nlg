import json
import os
import requests

# --- AYARLAR ---
GIRIS_DOSYASI = "MUKEMMEL_ETIKETLI_VERI.json"
CIKIS_DOSYASI = "NIHAI_EGITIM_VERISI_OLLAMA.json"
BATCH_SIZE = 5  # Yerel modelin hafızasını yormamak için 5'erli gönderiyoruz
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5" # Eğer başka model indirirsen adını buraya yazarsın

SYSTEM_PROMPT = """Sen usta bir satranç spikerisin. Aşağıda sana bir liste halinde verilen hamlelerin her biri için teknik verileri kullanarak, heyecanlı ve profesyonel bir Türkçe yorum yap.
Yorum yaparken oyunun kaçıncı hamlesinde olunduğuna, skora ve önceki hamleye mutlaka dikkat et.
Çıktıyı SADECE şu JSON formatında ver: [{"move": "hamle_adi", "comment": "yorum"}]
Açıklama yapma, sadece JSON'ı gönder."""

def yerel_yorumlat():
    with open(GIRIS_DOSYASI, "r", encoding="utf-8") as f:
        ham_veriler = json.load(f)

    if os.path.exists(CIKIS_DOSYASI):
        with open(CIKIS_DOSYASI, "r", encoding="utf-8") as f:
            egitim_veriseti = json.load(f)
    else:
        egitim_veriseti = []

    islenen_sayisi = len(egitim_veriseti)
    print(f"🔄 Sınırsız Yerel Motor Devrede. Kaldığı yer: {islenen_sayisi}/{len(ham_veriler)}")

    for i in range(islenen_sayisi, len(ham_veriler), BATCH_SIZE):
        batch = ham_veriler[i:i + BATCH_SIZE]
        
        batch_text_lines = []
        for j, v in enumerate(batch):
            taktik_str = ", ".join(v['tactical_motifs']) if v.get('tactical_motifs') else "Yok"
            tehdit_str = ", ".join(v['threatens']) if v.get('threatens') else "Yok"
            
            satir = (f"{j+1}. Hamle No: {v['fullmove_number']} | Sıra: {v['turn']} | "
                     f"Önceki: {v['previous_move']} -> Yapılan: {v['move_san']} | "
                     f"Aşama: {v['phase']} | Kalite: {v['move_quality']} | Skor: {v['eval_score']} | "
                     f"Taktik: {taktik_str} | Tehdit: {tehdit_str}")
            batch_text_lines.append(satir)
            
        batch_text = "\n".join(batch_text_lines)

        print(f"📦 Yerel Modele Paket Gönderiliyor ({i}-{i+len(batch)})...")
        
        payload = {
            "model": MODEL_NAME,
            "prompt": f"{SYSTEM_PROMPT}\n\nHamleler:\n{batch_text}",
            "stream": False # Tam yanıtı bekleyip tek seferde alıyoruz
        }

        try:
            # Ollama'ya istek atıyoruz
            response = requests.post(OLLAMA_URL, json=payload)
            response.raise_for_status() # Hata varsa yakala
            
            # Gelen cevabı al ve temizle
            yanit_metni = response.json()["response"]
            temiz_metin = yanit_metni.replace("```json", "").replace("```", "").strip()
            
            yorumlar = json.loads(temiz_metin)

            # Nihai Veri Setine Ekleme
            for idx, item in enumerate(yorumlar):
                if idx < len(batch):
                    taktik_str = ", ".join(batch[idx]['tactical_motifs']) if batch[idx].get('tactical_motifs') else "Yok"
                    tehdit_str = ", ".join(batch[idx]['threatens']) if batch[idx].get('threatens') else "Yok"

                    egitim_veriseti.append({
                        "instruction": "Bir satranç spikeri gibi hamleyi teknik ve heyecanlı bir dille yorumla.",
                        "input": (
                            f"Hamle No: {batch[idx]['fullmove_number']} | "
                            f"Sıra: {batch[idx]['turn']} | "
                            f"Önceki Hamle: {batch[idx]['previous_move']} | "
                            f"Yapılan Hamle: {batch[idx]['move_san']} ({batch[idx]['piece']}) | "
                            f"Aşama: {batch[idx]['phase']} | "
                            f"Kalite: {batch[idx]['move_quality']} | "
                            f"Oyun Skoru: {batch[idx]['eval_score']} | "
                            f"Taktikler: {taktik_str} | "
                            f"Tehditler: {tehdit_str} | "
                            f"Yeme: {'Evet' if batch[idx]['is_capture'] else 'Hayır'} | "
                            f"Şah/Mat: {'Mat' if batch[idx]['is_mate'] else 'Şah' if batch[idx]['is_check'] else 'Hayır'} | "
                            f"Materyal Dengesi: {batch[idx]['material_balance']}"
                        ),
                        "output": item['comment']
                    })

            # Hemen Kaydet
            with open(CIKIS_DOSYASI, "w", encoding="utf-8") as out:
                json.dump(egitim_veriseti, out, indent=4, ensure_ascii=False)
            
            print(f"✅ Toplam {len(egitim_veriseti)} hamle tamamlandı. (Sıfır Limit, Sıfır Bekleme!)")

        except Exception as e:
            print(f"⚠️ Model JSON formatını bozdu veya bir hata oluştu: {e}")
            print("🔄 Bu paket atlanıyor, bir sonrakine geçiliyor...")
            continue # Yerel model hata yaparsa beklemeden diğerine geç

if __name__ == "__main__":
    yerel_yorumlat()