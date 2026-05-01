import json
import pandas as pd

# 1. Lokaldeki veriyi oku
file_path = "MASTER_TRAIN_DATA.json"
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

df = pd.DataFrame(data)

# 2. ChatML / Alpaca Prompt Şablonu
prompt_template = """Aşağıda, yerine getirmen gereken bir görev ve bu göreve bağlam sağlayan bir girdi bulunmaktadır. Görevi başarıyla tamamlayan profesyonel bir satranç spikeri yorumu yaz.

### Görev (Instruction):
{}

### Bağlam (Input):
{}

### Yorum (Output):
{}<|end_of_text|>""" # Unsloth Llama-3 için genelde <|end_of_text|> kullanılır

formatted_texts = []

# 3. Veriyi şablona oturt
for index, row in df.iterrows():
    formatted_text = prompt_template.format(
        row['instruction'], 
        row['input'], 
        row['output']
    )
    formatted_texts.append({"text": formatted_text})

# 4. Eğitim için JSONL formatında kaydet
formatted_df = pd.DataFrame(formatted_texts)
output_path = "FORMATTED_CHESS_TRAIN_DATA.jsonl"
formatted_df.to_json(output_path, orient="records", lines=True, force_ascii=False)

print(f"[+] Veri başarıyla formatlandı ve {output_path} olarak kaydedildi.")