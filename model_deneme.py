from llama_cpp import Llama
import sys

# 1. Modeli Yükle
model_yolu = "llama-3-8b-instruct.Q4_K_M.gguf"

print("Spiker hazırlanıyor... (Lütfen 30-40 saniye bekle)")

llm = Llama(
    model_path=model_yolu,
    n_ctx=256,
    n_gpu_layers=0,
    n_threads=4,
    verbose=False
)

# 2. Veri ve Prompt
hamle_verisi = "Hamle No: 1 | Sıra: Beyaz | Önceki Hamle: Oyun Başlangıcı | Yapılan Hamle: e4 | Aşama: Açılış | Kalite: İyi | Skor: 0.01 | Taktikler: Yok | Tehditler: Yok | Yeme: Hayır | Durum: Normal"
prompt = f"<|start_header_id|>system<|end_header_id|>\n\nSen usta bir satranç spikerisin. Verilen verileri heyecanlı bir Türkçe ile yorumla.<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{hamle_verisi}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"

print("\n---MODEL KONUŞUYOR ---")

# 3. Akış (Streaming) Modunda Üretim
stream = llm(
    prompt,
    max_tokens=150,
    temperature=0.4,
    repeat_penalty=1.2,
    stop=["<|eot_id|>"],
    stream=True
)

# Kelimeler geldikçe ekrana bas
for output in stream:
    token = output["choices"][0]["text"]
    sys.stdout.write(token)
    sys.stdout.flush()

print("\n\n--- 🎙️ YAYIN BİTTİ ---")