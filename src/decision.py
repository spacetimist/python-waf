def make_decision(total_score: int, threshold: int, mode: str) -> str:
    """
    Membuat keputusan apakah permintaan diblokir atau diizinkan.

    mode "block"  → blokir jika skor >= threshold
    mode "detect" → selalu izinkan tapi tetap catat
    """
    if mode == "detect":
        return "allowed"

    if total_score >= threshold:
        return "blocked"

    return "allowed"