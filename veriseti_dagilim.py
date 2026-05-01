import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re

# 1. Veriyi Yükleme
with open('MASTER_TRAIN_DATA.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 2. 'Input' stringini parçalayarak DataFrame oluşturma
def parse_input(text):
    patterns = {
        'Hamle No': r'Hamle No: (\d+)',
        'Sıra': r'Sıra: (\w+)',
        'Aşama': r'Aşama: (\w+)',
        'Kalite': r'Kalite: ([\w\s]+)',
        'Skor': r'Skor: ([\d.-]+)',
        'Taktikler': r'Taktikler: ([\w\s,]+)',
    }
    extracted = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            extracted[key] = match.group(1).strip()
    return extracted

df = pd.DataFrame([parse_input(item['input']) for item in data])
df['Skor'] = pd.to_numeric(df['Skor'], errors='coerce')

# 3. Görselleştirme
sns.set_theme(style="whitegrid")
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Grafik 1: Hamle Kalitesi (En önemli metrik)
sns.countplot(data=df, x='Kalite', ax=axes[0,0], order=df['Kalite'].value_counts().index, palette='viridis')
axes[0,0].set_title('Hamle Kalitesi Dağılımı')

# Grafik 2: Oyun Aşaması (Açılış/Orta/Oyun Sonu)
phase_counts = df['Aşama'].value_counts()
axes[0,1].pie(phase_counts, labels=phase_counts.index, autopct='%1.1f%%', startangle=140)
axes[0,1].set_title('Oyun Aşaması Dağılımı')

# Grafik 3: Skor Dağılımı (Oyun dengesi)
sns.histplot(df['Skor'].dropna(), bins=30, kde=True, ax=axes[1,0], color='skyblue')
axes[1,0].set_title('Stockfish Skor Dağılımı')

# Grafik 4: Taktik Motif Analizi
all_tactics = []
for t in df['Taktikler'].dropna():
    if t != 'Yok':
        all_tactics.extend([x.strip() for x in t.split(',')])
tactic_counts = pd.Series(all_tactics).value_counts().head(10)
tactic_counts.plot(kind='bar', ax=axes[1,1], color='salmon')
axes[1,1].set_title('En Sık Rastlanan 10 Taktik Motif')

plt.tight_layout()
plt.savefig('dataset_analizi.png')
print("Analiz grafiği 'dataset_analizi.png' olarak kaydedildi.")