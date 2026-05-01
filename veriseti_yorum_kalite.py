import json
import re

def detect_and_show_errors(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    errors = {
        "yeme_celiskisi": [],
        "kalite_celiskisi": [],
        "durum_celiskisi": []
    }

    # 1. Genişletilmiş 'Yeme' (Capture) Sözlüğü
    yeme_kelimeleri = [
        r"yedi", r"aldı", r"süpürdü", r"kırdı", r"kopardı", r"biçip", 
        r"yuttu", r"mideye indirdi", r"ortadan kaldırıyor", r"tahtadan siliyor", 
        r"patlatıyor", r"söküp", r"parçalayarak", r"kellesini"
    ]

    # 2. Genişletilmiş 'Hata' (Blunder/Mistake) Sözlüğü
    hata_kelimeleri = [
        r"hata", r"risk", r"felaket", r"intihar", r"gaf", r"yanlış", 
        r"kaçırmasına", r"unuttu", r"elinin tersiyle", r"kendi sonunu", 
        r"kaybetmek", r"ipini çekti", r"teslim bayrağı", r"kendi ayağına", 
        r"akıl tutulması", r"pahalıya patlayabilir", r"nefes aldırdı", r"kötüleştirdi",
        r"bedeli çok ağır", r"tehlike çanları", r"sallanıyor", r"çöktü", r"darmadağın"
    ]

    # 3. Şah / Mat Kontrolü
    sah_mat_kelimeleri = [r"\bşah\b", r"\bmat\b"]

    for index, item in enumerate(dataset):
        input_text = item.get("input", "")
        output_text = item.get("output", "").lower()

        try:
            # Input'taki key:value çiftlerini ayıkla
            input_dict = {k.strip(): v.strip() for part in input_text.split('|') if ':' in part for k, v in [part.split(':', 1)]}
        except Exception:
            continue

        # --- YEME ÇELİŞKİSİ KONTROLÜ ---
        if input_dict.get("Yeme") == "Hayır":
            if any(re.search(word, output_text) for word in yeme_kelimeleri):
                errors["yeme_celiskisi"].append({
                    "index": index,
                    "hamle": input_dict.get("Hamle No", "?"),
                    "output_metni": item.get("output")
                })

        # --- KALİTE ÇELİŞKİSİ KONTROLÜ ---
        kalite = input_dict.get("Kalite", "")
        if kalite in ["Hata", "Büyük Hata"]:
            if not any(re.search(word, output_text) for word in hata_kelimeleri):
                errors["kalite_celiskisi"].append({
                    "index": index,
                    "hamle": input_dict.get("Hamle No", "?"),
                    "beklenen_kalite": kalite,
                    "output_metni": item.get("output")
                })

        # --- DURUM ÇELİŞKİSİ KONTROLÜ ---
        if input_dict.get("Durum") == "Normal":
            if any(re.search(word, output_text) for word in sah_mat_kelimeleri):
                if "şahını" not in output_text and "şahı" not in output_text:
                    errors["durum_celiskisi"].append({
                        "index": index,
                        "hamle": input_dict.get("Hamle No", "?"),
                        "output_metni": item.get("output")
                    })

    # --- DETAYLI RAPORLAMA VE LOGLAMA ---
    print(f"Toplam İncelenen Veri: {len(dataset)}\n")
    
    def print_error_category(title, error_list):
        print(f"{'='*60}")
        print(f"{title} ({len(error_list)} Hata Bulundu)")
        print(f"{'='*60}")
        if not error_list:
            print("Bu kategoride hiç hata bulunmadı! Temiz iş.\n")
            return
            
        for err in error_list:
            print(f"-> JSON Index: {err['index']} | Hamle No: {err['hamle']}")
            if 'beklenen_kalite' in err:
                print(f"-> Beklenen Etiket: {err['beklenen_kalite']}")
            print(f"-> Modelin Çıktısı: {err['output_metni']}")
            print("-" * 40)
        print("\n")

    print_error_category("1. YEME ÇELİŞKİSİ (Yeme: Hayır ama spiker taşı yediğini söylüyor)", errors["yeme_celiskisi"])
    print_error_category("2. KALİTE ÇELİŞKİSİ (Hata var ama spiker bunu terminolojik olarak yansıtamamış)", errors["kalite_celiskisi"])
    print_error_category("3. DURUM ÇELİŞKİSİ (Durum: Normal ama spiker Şah/Mat olduğunu iddia ediyor)", errors["durum_celiskisi"])

# Fonksiyonu çalıştırmak için:
detect_and_show_errors("EGITIM_VERISI_GEMINI.json")