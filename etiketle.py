import bz2
import chess.pgn
import chess.engine
import json
import random

# --- AYARLAR ---
STOCKFISH_PATH = "/opt/homebrew/bin/stockfish"
PGN_PATH = "./dataset/lichess_db_standard_rated_2014-10.pgn.bz2"
OUT_PATH = "ETIKETLI_VERI.json"

TAS_DEGERLERI = {
    chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
    chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0
}

def analiz_et(tahta, hamle):
    """Taktik ve Motif Radarı"""
    taktikler = []
    tehditler = []
    
    if tahta.is_castling(hamle):
        taktikler.append("Rok")
    if tahta.is_en_passant(hamle):
        taktikler.append("Geçerken Alma")
    if hamle.promotion:
        taktikler.append("Terfi")
        
    if tahta.is_pinned(tahta.turn, hamle.from_square):
        taktikler.append("Açmazdan Kurtulma")

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
            tas_adi = chess.piece_name(target.piece_type)
            tehditler.append(tas_adi)
            
            if target.piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
                degerli_hedef_sayisi += 1
                
    if degerli_hedef_sayisi >= 2:
        taktikler.append("Çatal")

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

def hamle_kalitesi_ve_skor(engine, tahta, hamle):
    info_before = engine.analyse(tahta, chess.engine.Limit(time=0.1))
    score_before = info_before["score"].relative.score(mate_score=9900)
    
    tahta.push(hamle)
    info_after = engine.analyse(tahta, chess.engine.Limit(time=0.1))
    score_after = -info_after["score"].relative.score(mate_score=9900)
    
    mutlak_skor = info_after["score"].white().score(mate_score=9900) / 100.0
    tahta.pop()
    
    diff = score_after - score_before
    if diff < -300: kalite = "Blunder"
    elif diff < -100: kalite = "Mistake"
    elif diff > 200: kalite = "Brilliant"
    elif diff > 50: kalite = "Excellent"
    else: kalite = "Good Move"
    
    return kalite, round(mutlak_skor, 2)

def etiketle():
    dataset = []
    limit = 4000
    sayac = 0
    engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    print("🚀 Gelişmiş Taktik Radarı ve Akıllı Filtre Çalışıyor...")

    with bz2.open(PGN_PATH, "rt", encoding="utf-8") as f:
        while sayac < limit:
            oyun = chess.pgn.read_game(f)
            if oyun is None: break
            tahta = oyun.board()
            onceki_hamle_san = "Oyun Başlangıcı"
            
            for hamle_dugumu in oyun.mainline():
                if sayac >= limit: break
                hamle = hamle_dugumu.move
                tas = tahta.piece_at(hamle.from_square)
                if tas is None: continue
                
                move_san_str = tahta.san(hamle)
                taktikler, tehditler = analiz_et(tahta, hamle)
                asama = oyun_asamasi_bul(tahta)
                kalite, skor = hamle_kalitesi_ve_skor(engine, tahta, hamle)
                
                is_capture = tahta.is_capture(hamle)
                is_check = tahta.gives_check(hamle)
                turn_str = "Beyaz" if tahta.turn else "Siyah"
                fullmove_number = tahta.fullmove_number
                
                tahta.push(hamle)
                is_mate = tahta.is_checkmate()
                material_balance = sum(TAS_DEGERLERI.get(p.piece_type, 0) for p in tahta.piece_map().values() if p.color == chess.WHITE) - \
                                   sum(TAS_DEGERLERI.get(p.piece_type, 0) for p in tahta.piece_map().values() if p.color == chess.BLACK)
                
                ilginc_mi = False
                
                if taktikler or is_check or is_mate or is_capture or kalite in ["Blunder", "Brilliant", "Mistake", "Excellent"]:
                    ilginc_mi = True
                else:
                    if random.random() < 0.15: 
                        ilginc_mi = True
                
                if ilginc_mi:
                    etiketler = {
                        "move_san": move_san_str,
                        "piece": chess.piece_name(tas.piece_type),
                        "previous_move": onceki_hamle_san,
                        "eval_score": skor,
                        "phase": asama,
                        "tactical_motifs": taktikler,
                        "threatens": tehditler,
                        "move_quality": kalite,
                        "is_capture": is_capture,
                        "is_check": is_check,
                        "turn": turn_str,
                        "fullmove_number": fullmove_number,
                        "material_balance": material_balance,
                        "is_mate": is_mate
                    }
                    
                    dataset.append(etiketler)
                    sayac += 1
                    if sayac % 100 == 0: print(f"{sayac} hamle işlendi...")

                onceki_hamle_san = move_san_str

    engine.quit()
    with open(OUT_PATH, "w", encoding="utf-8") as out:
        json.dump(dataset, out, indent=4, ensure_ascii=False)
    print(f"\nİşlem bitti! 4000 hamlelik veri setin hazır: {OUT_PATH}")

if __name__ == "__main__":
    etiketle()