import bz2
import chess.pgn
import chess.engine
import json
import os

# --- AYARLAR ---
STOCKFISH_PATH = "/opt/homebrew/bin/stockfish" # Kendi yolunuza göre güncelleyin
PGN_PATH = "./dataset/lichess_db_standard_rated_2014-10.pgn.bz2"
OUT_PATH = "HARIKA_HAMLELER_VERISI.json"

TAS_DEGERLERI = {
    chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
    chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0
}

TAS_ISIMLERI_TR = {
    "pawn": "Piyon", "knight": "At", "bishop": "Fil",
    "rook": "Kale", "queen": "Vezir", "king": "Şah"
}

def analiz_et(tahta, hamle):
    taktikler = []
    tehditler = []
    
    if tahta.is_castling(hamle): taktikler.append("Rok")
    if tahta.is_en_passant(hamle): taktikler.append("Geçerken Alma")
    if hamle.promotion: taktikler.append("Terfi")
    if tahta.is_pinned(tahta.turn, hamle.from_square): taktikler.append("Açmazdan Kurtulma")

    tahta.push(hamle)
    to_sq = hamle.to_square
    
    if tahta.is_check():
        checkers = tahta.checkers()
        if to_sq not in checkers and not taktikler.count("Rok"):
            taktikler.append("Açarak Şah")
            
    attacks = tahta.attacks(to_sq)
    degerli_hedef_sayisi = 0
    
    for sq in attacks:
        target = tahta.piece_at(sq)
        if target and target.color == tahta.turn:
            tas_adi_en = chess.piece_name(target.piece_type)
            tehditler.append(TAS_ISIMLERI_TR.get(tas_adi_en, tas_adi_en).lower())
            if target.piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
                degerli_hedef_sayisi += 1
                
    if degerli_hedef_sayisi >= 2: taktikler.append("Çatal")

    for sq in chess.SQUARES:
        p = tahta.piece_at(sq)
        if p and p.color == tahta.turn and tahta.is_pinned(tahta.turn, sq):
            taktikler.append("Açmaz Oluşturma")
            break

    tahta.pop() 
    return list(set(taktikler)), list(set(tehditler))

def oyun_asamasi_bul(tahta):
    toplam_materyal = sum(TAS_DEGERLERI[p.piece_type] for p in tahta.piece_map().values() if p.piece_type != chess.PAWN)
    if tahta.fullmove_number <= 12: return "Açılış"
    return "Oyun Sonu" if toplam_materyal <= 15 else "Orta Oyun"

def potansiyel_harika_mi(tahta, hamle):
    """
    AKILLI BUDAMA (Heuristic Pruning):
    Motoru yormamak için sadece potansiyel taşıyan hamleleri Stockfish'e gönderir.
    Fedalar, şah çekmeler veya yüksek değerli taş hareketleri potansiyel taşır.
    """
    if tahta.is_capture(hamle): return True
    if tahta.gives_check(hamle): return True
    
    # Hareket eden taşın değerine bak (Piyon sürüşlerini azaltır)
    tas = tahta.piece_at(hamle.from_square)
    if tas and tas.piece_type in [chess.QUEEN, chess.ROOK, chess.KNIGHT, chess.BISHOP]:
        return True
    
    # Piyon terfisi veya rok gibi kritik hamleler
    if hamle.promotion or tahta.is_castling(hamle): return True
    
    return False

def hamle_kalitesi_ve_skor(engine, tahta, hamle):
    # DİKKAT: time=0.1 yerine depth=12 kullanarak hızı dramatik şekilde artırıyoruz.
    limit = chess.engine.Limit(depth=12) 
    
    info_before = engine.analyse(tahta, limit)
    score_before = info_before["score"].relative.score(mate_score=9900)
    
    tahta.push(hamle)
    info_after = engine.analyse(tahta, limit)
    score_after = -info_after["score"].relative.score(mate_score=9900)
    
    mutlak_skor = info_after["score"].white().score(mate_score=9900) / 100.0
    tahta.pop()
    
    diff = score_after - score_before
    
    if diff > 200: kalite = "Harika"
    elif diff > 50: kalite = "Mükemmel"
    elif diff < -300: kalite = "Büyük Hata"
    elif diff < -100: kalite = "Hata"
    else: kalite = "İyi"
    
    return kalite, round(mutlak_skor, 2)

def kaydet(dataset):
    """Checkpointing: Veriyi güvenle diske yazar."""
    with open(OUT_PATH, "w", encoding="utf-8") as out:
        json.dump(dataset, out, indent=4, ensure_ascii=False)

def etiketle():
    dataset = []
    
    # Eğer önceden kaydedilmiş veri varsa yükle (Script çökerse kaldığı yerden değil, en azından eski veriyi kaybetmemek için)
    if os.path.exists(OUT_PATH):
        try:
            with open(OUT_PATH, "r", encoding="utf-8") as f:
                dataset = json.load(f)
                print(f"Mevcut veri seti yüklendi. (Mevcut Kayıt: {len(dataset)})")
        except json.JSONDecodeError:
            print("Mevcut JSON dosyası bozuk, sıfırdan başlanıyor.")
            
    hedef_sayi = 1000 # Toplam ulaşmak istediğin "Harika/Mükemmel" hamle sayısı
    sayac = len(dataset)
    
    if sayac >= hedef_sayi:
        print("Hedef sayıya zaten ulaşılmış.")
        return

    engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    print("🚀 Optimize Edilmiş Taktik Radarı Başlatıldı...")

    with bz2.open(PGN_PATH, "rt", encoding="utf-8") as f:
        while sayac < hedef_sayi:
            oyun = chess.pgn.read_game(f)
            if oyun is None: break
            tahta = oyun.board()
            onceki_hamle_san = "Oyun Başlangıcı"
            
            for hamle_dugumu in oyun.mainline():
                if sayac >= hedef_sayi: break
                hamle = hamle_dugumu.move
                tas = tahta.piece_at(hamle.from_square)
                if tas is None: continue
                
                # AKILLI BUDAMA: Sadece potansiyel taşıyan hamleleri Stockfish'e gönder!
                if not potansiyel_harika_mi(tahta, hamle):
                    onceki_hamle_san = tahta.san(hamle)
                    tahta.push(hamle)
                    continue

                kalite, skor = hamle_kalitesi_ve_skor(engine, tahta, hamle)
                
                # SIKI FİLTRE: Sadece Harika veya Mükemmel hamleleri al
                if kalite not in ["Harika", "Mükemmel"]:
                    onceki_hamle_san = tahta.san(hamle)
                    tahta.push(hamle)
                    continue

                move_san_str = tahta.san(hamle)
                taktikler, tehditler = analiz_et(tahta, hamle)
                asama = oyun_asamasi_bul(tahta)
                
                is_capture = tahta.is_capture(hamle)
                is_check = tahta.gives_check(hamle)
                turn_str = "Beyaz" if tahta.turn else "Siyah"
                fullmove_number = tahta.fullmove_number
                
                tahta.push(hamle)
                is_mate = tahta.is_checkmate()
                
                yeme_str = "Evet" if is_capture else "Hayır"
                durum_str = "Mat" if is_mate else ("Şah" if is_check else "Normal")
                taktik_str = ", ".join(taktikler) if taktikler else "Yok"
                tehdit_str = ", ".join(tehditler) if tehditler else "Yok"
                tas_tr = TAS_ISIMLERI_TR.get(chess.piece_name(tas.piece_type), "Bilinmeyen")
                hamle_formati = f"{move_san_str} ({tas_tr})"
                
                input_string = (
                    f"Hamle No: {fullmove_number} | Sıra: {turn_str} | Önceki Hamle: {onceki_hamle_san} | "
                    f"Yapılan Hamle: {hamle_formati} | Aşama: {asama} | Kalite: {kalite} | Skor: {skor} | "
                    f"Taktikler: {taktik_str} | Tehditler: {tehdit_str} | Yeme: {yeme_str} | Durum: {durum_str}"
                )
                
                etiketler = {
                    "instruction": "Bir satranç spikeri gibi hamleyi teknik ve heyecanlı bir dille yorumla.",
                    "input": input_string,
                    "output": "" # LLM ile doldurulacak
                }
                
                dataset.append(etiketler)
                sayac += 1
                
                # CHECKPOINTING: Her 50 hamlede bir diske kaydet
                if sayac % 50 == 0:
                    kaydet(dataset)
                    print(f"✅ {sayac} harika/mükemmel hamle bulundu ve kaydedildi...")

                onceki_hamle_san = move_san_str

    engine.quit()
    kaydet(dataset) # Son kalanı da kaydet
    print(f"\nİşlem bitti! Mükemmel ve Harika hamlelik veri setin hazır: {OUT_PATH}")

if __name__ == "__main__":
    etiketle()