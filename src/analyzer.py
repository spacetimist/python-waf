import urllib.parse
import json

def analyze_request(request) -> dict:
    """
    Mengekstrak semua bagian relevan dari permintaan HTTP
    untuk diperiksa oleh Pattern Matching Engine.
    """
    extracted = {}

    # URI dan path
    extracted["uri"] = request.path or ""

    # query string (contoh: ?id=1&name=test)
    extracted["query_string"] = request.query_string.decode("utf-8", errors="replace")

    # parameter GET
    extracted["args"] = {k: v for k, v in request.args.items()}

    # parameter POST (form-data)
    extracted["form"] = {k: v for k, v in request.form.items()}

    # headers HTTP
    extracted["headers"] = {k: v for k, v in request.headers.items()}

    # cookies
    extracted["cookies"] = {k: v for k, v in request.cookies.items()}

    # user agent
    extracted["user_agent"] = request.headers.get("User-Agent", "")

    # request body (JSON atau raw)
    extracted["body"] = ""
    if request.content_type and "application/json" in request.content_type:
        try:
            body_data = request.get_json(silent=True)
            extracted["body"] = json.dumps(body_data) if body_data else ""
        except Exception:
            extracted["body"] = request.get_data(as_text=True)
    else:
        extracted["body"] = request.get_data(as_text=True)

    # info dasar request
    extracted["method"] = request.method
    extracted["src_ip"] = request.remote_addr

    return extracted


def get_check_targets(extracted: dict, targets: list) -> list:
    """
    Mengambil nilai yang akan diperiksa berdasarkan
    daftar target yang didefinisikan di ruleset.
    """
    values = []

    for target in targets:
        if target == "uri":
            values.append(extracted.get("uri", ""))
        elif target == "query_string":
            values.append(extracted.get("query_string", ""))
        elif target == "args":
            values.extend(extracted.get("args", {}).values())
        elif target == "form":
            values.extend(extracted.get("form", {}).values())
        elif target == "body":
            values.append(extracted.get("body", ""))
        elif target == "headers":
            values.extend(extracted.get("headers", {}).values())
        elif target == "cookies":
            values.extend(extracted.get("cookies", {}).values())
        elif target == "user_agent":
            values.append(extracted.get("user_agent", ""))

    return [v for v in values if v]  # buang nilai kosong