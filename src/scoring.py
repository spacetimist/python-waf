def calculate_score(triggered_rules: list) -> int:
    """
    Menjumlahkan skor dari semua aturan yang terpicu.
    """
    total = 0
    for rule in triggered_rules:
        total += rule.get("score", 1)
    return total


def summarize_triggered(triggered_rules: list) -> dict:
    """
    Membuat ringkasan aturan yang terpicu untuk keperluan
    logging dan analisis.
    """
    summary = {
        "count": len(triggered_rules),
        "total_score": calculate_score(triggered_rules),
        "rules": []
    }

    for rule in triggered_rules:
        summary["rules"].append({
            "id": rule.get("id"),
            "description": rule.get("description", ""),
            "severity": rule.get("severity", "medium"),
            "score": rule.get("score", 1)
        })

    return summary