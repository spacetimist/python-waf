import time
import yaml
from flask import Flask, request, Response, make_response

from src.logger import setup_logger, log_request
from src.analyzer import analyze_request, get_check_targets
from src.rule_loader import load_rules
from src.matcher import run_all_rules
from src.scoring import calculate_score
from src.decision import make_decision
from src.forwarder import forward_request


def create_app(config_path: str = "config/config.yaml") -> Flask:
    app = Flask(__name__)

    # muat konfigurasi
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # setup logger
    log_cfg = config.get("logging", {})
    logger = setup_logger(
        log_path=log_cfg.get("path", "logs/waf.log"),
        level=log_cfg.get("level", "INFO")
    )

    # muat ruleset
    rules_cfg = config.get("rules", {})
    sqli_rules = load_rules(rules_cfg.get("sqli", "rules/sqli.yaml"))
    xss_rules = load_rules(rules_cfg.get("xss", "rules/xss.yaml"))
    all_rules = sqli_rules + xss_rules

    logger.info(f"Ruleset dimuat: {len(sqli_rules)} aturan SQLi, "
                f"{len(xss_rules)} aturan XSS.")

    # ambil konfigurasi deteksi dan backend
    detection_cfg = config.get("detection", {})
    threshold = detection_cfg.get("threshold", 5)
    mode = config.get("server", {}).get("mode", "block")

    backend_cfg = config.get("backend", {})
    backend_host = backend_cfg.get("host", "127.0.0.1")
    backend_port = backend_cfg.get("port", 80)

    @app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE"])
    @app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
    def waf_handler(path):
        start_time = time.time()

        # simpan body request sebelum diproses
        request_data = request.get_data()
        
        # ekstrak bagian-bagian permintaan
        extracted = analyze_request(request)

        # cocokkan dengan semua aturan
        triggered = run_all_rules(all_rules, extracted, get_check_targets)

        # hitung skor total
        total_score = calculate_score(triggered)

        # buat keputusan
        decision = make_decision(total_score, threshold, mode)

        # hitung latensi
        latency_ms = (time.time() - start_time) * 1000

        # catat ke log
        request_info = {
            "src_ip": extracted.get("src_ip"),
            "method": extracted.get("method"),
            "uri": extracted.get("uri")
        }
        log_request(logger, request_info, triggered, total_score,
                    decision, latency_ms)

        # blokir jika keputusan blocked
        if decision == "blocked":
            return Response(
                response="403 Forbidden - Permintaan diblokir oleh WAF.",
                status=403,
                mimetype="text/plain"
            )

        # teruskan ke backend jika diizinkan
        result = forward_request(request, backend_host, backend_port, request_data)

        # debug sementara
        logger.debug(f"Backend status: {result['status_code']}")
        logger.debug(f"Backend headers: {result['headers']}")
        logger.debug(f"Request form data: {dict(request.form)}")
        logger.debug(f"Request cookies: {dict(request.cookies)}")

        # buang header yang bisa konflik sebelum dikembalikan ke client
        excluded_headers = [
        "content-encoding", "transfer-encoding",
        "connection", "content-length", "keep-alive"
        ]
        response_headers = {
            k: v for k, v in result["headers"].items()
            if k.lower() not in excluded_headers
        }

        # ganti URL backend di header Location dengan URL WAF
        if "Location" in response_headers:
            response_headers["Location"] = response_headers["Location"].replace(
                f"http://{backend_host}:{backend_port}",
                "http://localhost:8000"
            ).replace(
                f"http://{backend_host}",
                "http://localhost:8000"
            )

        resp = make_response(result["content"], result["status_code"])
        import re
        for k, v in response_headers.items():
            if k.lower() == "set-cookie":
                # split multiple cookies yang digabung dalam satu header
                cookies = re.split(r',\s*(?=[a-zA-Z]+=)', v)
                for cookie in cookies:
                    cookie = cookie.replace("; SameSite=Strict", "")
                    cookie = cookie.replace("; SameSite=Lax", "")
                    if "security=" in cookie:
                        cookie = re.sub(r"security=\w+", "security=low", cookie)
                    resp.headers.add("Set-Cookie", cookie)
            else:
                resp.headers[k] = v

        # debug cookie yang dikirim ke browser
        logger.debug(f"Response cookies sent to browser: {resp.headers.getlist('Set-Cookie')}")
        
        return resp

    return app