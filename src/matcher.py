import re
import urllib.parse
import html
import base64

def apply_transform(value: str, transforms: list) -> str:
    """
    Menerapkan transformasi pada nilai sebelum pencocokan,
    misalnya lowercase, URL decode, HTML decode.
    """
    for transform in transforms:
        if transform == "lowercase":
            value = value.lower()
        elif transform == "url_decode":
            value = urllib.parse.unquote_plus(value)
        elif transform == "html_decode":
            value = html.unescape(value)
        elif transform == "remove_whitespace":
            value = re.sub(r"\s+", "", value)
        elif transform == "base64_decode":
            try:
                if '=' in value and not value.startswith('PH'):
                    parts = value.split('=', 1)
                    if len(parts) > 1:
                        value = parts[1]
                value = value.replace(' ', '+')
                clean = re.sub(r'[^A-Za-z0-9+/=]', '', value)
                if len(clean) < 20:
                    pass
                else:
                    padding = 4 - len(clean) % 4
                    if padding != 4:
                        clean += "=" * padding
                    decoded = base64.b64decode(clean).decode("utf-8", errors="ignore")
                    value = decoded
            except Exception as e:
                print(f"[DEBUG] error={e}")
                pass
    return value


def match_rule(rule: dict, values: list) -> bool:
    """
    Mencocokkan satu aturan terhadap daftar nilai target.
    Mengembalikan True jika ada nilai yang cocok.
    """
    operator = rule.get("operator", "regex")
    transforms = rule.get("transform", [])
    pattern = rule.get("pattern", "")
    compiled = rule.get("compiled_pattern")

    for value in values:
        # terapkan transformasi dulu
        transformed = apply_transform(str(value), transforms)

        if operator == "regex":
            if compiled and compiled.search(transformed):
                return True
            elif not compiled and re.search(pattern, transformed, re.IGNORECASE):
                return True
        elif operator == "contains":
            if pattern.lower() in transformed.lower():
                return True
        elif operator == "equals":
            if pattern.lower() == transformed.lower():
                return True

    return False


def run_all_rules(rules: list, extracted: dict, get_targets_fn) -> list:
    """
    Menjalankan semua aturan terhadap permintaan yang sudah diekstrak.
    Mengembalikan daftar aturan yang terpicu.
    """
    triggered = []

    for rule in rules:
        targets = rule.get("target", [])
        values = get_targets_fn(extracted, targets)

        if match_rule(rule, values):
            triggered.append({
                "id": rule.get("id"),
                "description": rule.get("description", ""),
                "severity": rule.get("severity", "medium"),
                "score": rule.get("score", 1),
                "tags": rule.get("tags", [])
            })

    return triggered
