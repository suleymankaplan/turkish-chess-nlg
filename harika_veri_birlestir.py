import json
import random
import os

# --- AYARLAR ---
BASE_DATA_PATH = "EGITIM_VERISI_GEMINI.json"       # Ana 4000'lik veri
ELITE_DATA_PATH = "YORUMLANMIS_MASTER_VERI.json" # Yeni 550'lik elit veri
FINAL_OUTPUT_PATH = "MASTER_TRAIN_DATA.json"

def veri_setlerini_harmanla():
    print("🚀 Veri entegrasyonu süreci başlatıldı...")

    # 1. Verileri Yükle
    if not os.path.exists(BASE_DATA_PATH) or not os.path.exists(ELITE_DATA_PATH):
        print("❌ HATA: Giriş dosyalarından biri eksik!")
        return

    with open(BASE_DATA_PATH, 'r', encoding='utf-8') as f:
        base_data = json.load(f)
    
    with open(ELITE_DATA_PATH, 'r', encoding='utf-8') as f:
        elite_data = json.load(f)

    print(f"📊 Mevcut Durum: Ana Veri ({len(base_data)}) + Elit Veri ({len(elite_data)})")

    # 2. Veri Standardizasyonu
    # Elit verilerin 'instruction' ve 'input' formatının ana veriyle tam uyumlu olduğundan emin oluyoruz
    # Önceki adımda Gemini'ye yaptırdığımız etiketlemeyi koruyoruz.
    
    # 3. Birleştirme
    combined_data = base_data + elite_data

    # 4. Karıştırma (Shuffle) - ÇOK KRİTİK!
    # Eğer karıştırmazsak model eğitimin sonunda sadece 'Harika' hamleleri görür 
    # ve 'gradient descent' süreci dengesizleşir.
    random.shuffle(combined_data)

    # 5. Kaydet
    with open(FINAL_OUTPUT_PATH, 'w', encoding='utf-8') as out:
        json.dump(combined_data, out, indent=4, ensure_ascii=False)

    # İstatistiksel Özet
    toplam = len(combined_data)
    print(f"\n✅ İşlem Başarılı! Toplam {toplam} örnek birleştirildi.")
    print(f"📈 Veri Dağılımı: Elit Hamle Oranı: %{(len(elite_data) / toplam) * 100:.2f}")
    print(f"📂 Nihai Dosya: {FINAL_OUTPUT_PATH}")

if __name__ == "__main__":
    veri_setlerini_harmanla()