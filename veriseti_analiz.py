import json
import pandas as pd
import re
import matplotlib.pyplot as plt
import seaborn as sns

def load_dataset(file_path):
    """JSON formatındaki satranç veri setini yükler ve DataFrame'e çevirir."""
    print(f"[*] '{file_path}' yükleniyor...")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    print(f"[+] Veri seti yüklendi. Toplam kayıt: {len(df)}")
    return df

def calculate_lexical_diversity(df):
    """
    TTR (Type-Token Ratio) hesaplar. 
    Modelin output'larında kullandığı kelime dağarcığının zenginliğini ölçer.
    """
    print("\n--- 1. Sözcük Çeşitliliği Analizi (Lexical Diversity) ---")
    all_text = " ".join(df['output'].dropna()).lower()
    
    # Sadece alfanumerik kelimeleri ayıkla (Tokenization simülasyonu)
    words = re.findall(r'\b\w+\b', all_text)
    unique_words = set(words)
    
    total_words = len(words)
    total_unique = len(unique_words)
    ttr = (total_unique / total_words) * 100 if total_words > 0 else 0
    
    print(f"Toplam Kelime (Token): {total_words}")
    print(f"Benzersiz Kelime (Type): {total_unique}")
    print(f"TTR Skoru: %{ttr:.2f}")
    
    return total_words, total_unique, ttr

def check_tactical_alignment(df):
    """
    Input'ta belirtilen 'Açmaz', 'Çatal' gibi taktiklerin, 
    Output (yorum) metninde geçip geçmediğini kontrol eder.
    """
    print("\n--- 2. Taktiksel Bağlam Uyumu (Tactical Alignment) ---")
    
    match_count = 0
    valid_tactic_count = 0
    
    for _, row in df.iterrows():
        input_text = str(row['input'])
        output_text = str(row['output']).lower()
        
        # Regex ile "Taktikler: [Taktik Adı]" kısmını yakala
        match = re.search(r'Taktikler:\s*([^|]+)', input_text)
        if match:
            tactic = match.group(1).strip().lower()
            if tactic != "yok":
                valid_tactic_count += 1
                # Taktik içindeki kelimelerden en az biri yorumda geçiyor mu?
                tactic_keywords = tactic.split()
                if any(kw in output_text for kw in tactic_keywords if len(kw) > 3):
                    match_count += 1
                    
    alignment_rate = (match_count / valid_tactic_count) * 100 if valid_tactic_count > 0 else 0
    print(f"Taktik İçeren Toplam Hamle: {valid_tactic_count}")
    print(f"Taktiğin Yorumda Başarıyla Kullanılma Oranı: %{alignment_rate:.2f}")
    
    return alignment_rate

def check_semantic_consistency(df):
    """
    'Büyük Hata' içeren inputların, dramatik ve eleştirel bir tonda
    yorumlanıp yorumlanmadığını ölçer.
    """
    print("\n--- 3. Semantik Tutarlılık (Semantic Consistency) ---")
    
    # Hata durumlarında beklenen tetikleyici kelimeler
    dramatic_keywords = ["inanılmaz", "felaket", "gözlerime", "şaka", "yıkım", "hata", "gaf", "inanılır"]
    
    blunder_df = df[df['input'].str.contains("Büyük Hata", case=False, na=False)]
    blunder_count = len(blunder_df)
    
    consistent_count = 0
    for output_text in blunder_df['output']:
        if any(kw in str(output_text).lower() for kw in dramatic_keywords):
            consistent_count += 1
            
    consistency_rate = (consistent_count / blunder_count) * 100 if blunder_count > 0 else 0
    print(f"'Büyük Hata' Etiketli Hamle Sayısı: {blunder_count}")
    print(f"Dramatik/Eleştirel Tonla Uyumlu Yorum Oranı: %{consistency_rate:.2f}")
    
    return consistency_rate

def plot_dataset_statistics(df):
    """Sunum için veri seti dağılım grafiklerini oluşturur."""
    print("\n[*] Sunum grafikleri oluşturuluyor...")
    sns.set_theme(style="whitegrid")
    
    # Aşama (Phase) Dağılımını çıkar (Açılış, Orta Oyun, Oyun Sonu)
    phases = ["Açılış", "Orta Oyun", "Oyun Sonu"]
    phase_counts = {phase: df['input'].str.contains(phase).sum() for phase in phases}
    
    plt.figure(figsize=(10, 5))
    sns.barplot(x=list(phase_counts.keys()), y=list(phase_counts.values()), palette="viridis")
    plt.title("Oyun Aşaması (Phase) Dağılımı", fontsize=14)
    plt.ylabel("Veri Sayısı")
    plt.show()

if __name__ == "__main__":
    file_name = "MASTER_TRAIN_DATA.json"
    
    try:
        dataset = load_dataset(file_name)
        calculate_lexical_diversity(dataset)
        check_tactical_alignment(dataset)
        check_semantic_consistency(dataset)
        plot_dataset_statistics(dataset)
        print("\n[+] Analiz başarıyla tamamlandı. Tüm sistemler eğitime hazır!")
    except FileNotFoundError:
        print(f"[!] HATA: '{file_name}' dosyası bulunamadı. Script ile aynı dizinde olduğundan emin ol.")