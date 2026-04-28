# ♟️ Turkish Chess NLP: Yapay Zeka Destekli Satranç Spikeri

Stockfish'in soğuk ve sayısal analizlerini, profesyonel bir e-spor spikerinin heyecanıyla birleştiren, Doğal Dil İşleme (NLP) tabanlı bir veri seti üretim boru hattıdır. Bu proje, satranç hamlelerini derinlemesine analiz eder ve bir LLM (Large Language Model) aracılığıyla anlamlı, teknik ve aksiyon dolu Türkçe yorumlar üretir.

## ✨ Özellikler

* **🎯 Gelişmiş Taktik Radarı:** Hamlelerdeki çatal, açmaz, feda, rok, geçerken alma ve terfi gibi taktik motifleri anlık olarak tespit eder.
* **🤖 Gemini Pro Entegrasyonu:** Google Gemini API'sini kullanarak, "şablon" hissi vermeyen, doğal ve yüksek kaliteli sentetik yorumlar üretir.
* **📊 Stockfish 16+ Analizi:** Her hamleyi motor derinliğiyle sorgulayarak "Blunder" (Büyük Hata) veya "Brilliant" (Harika) gibi kalite etiketleri atar.
* **🚀 Fine-Tuning Hazır:** Llama-3, Mistral veya Phi-3 gibi modelleri eğitmek için doğrudan kullanılabilen `Instruction-Input-Output` formatında veri seti çıktısı verir.

## 🏗️ Mimari Akış

1.  **Veri Toplama:** PGN formatındaki oyun dosyaları (Lichess vb.) sisteme beslenir.
2.  **Teknik Etiketleme (`etiketle.py`):** Stockfish ve `python-chess` kütüphanesi ile hamleler; skor, taktik ve kalite metrikleriyle zenginleştirilir.
3.  **NLP Yorumlama (`yorum_ekle.py`):** Etiketlenen veriler Gemini API'sine gönderilerek bir spiker personasıyla Türkçeye dönüştürülür.
4.  **Dataset Oluşturma:** Nihai veriler `EGITIM_VERISI_GEMINI.json` dosyasında toplanır.

## 🛠️ Kurulum

1.  **Depoyu Klonlayın:**
    ```bash
    git clone [https://github.com/suleymankaplan/turkish-chess-nlg.git](https://github.com/suleymankaplan/turkish-chess-nlg.git)
    cd turkish-chess-nlg
    ```

2.  **Bağımlılıkları Yükleyin:**
    ```bash
    pip install python-chess google-generativeai python-dotenv
    ```

3.  **Stockfish Ayarı:**
    Sisteminizde yüklü olan Stockfish yolunu `etiketle.py` içindeki `STOCKFISH_PATH` değişkenine tanımlayın.

4.  **API Anahtarını Gizleyin:**
    Proje ana dizininde bir `.env` dosyası oluşturun ve Gemini API anahtarınızı ekleyin:
    ```env
    GEMINI_API_KEY=AIzaSy...your_key_here
    ```

## 🚀 Kullanım

Önce PGN verilerini Stockfish ile analiz edip etiketleyin:
```bash
python etiketle.py
