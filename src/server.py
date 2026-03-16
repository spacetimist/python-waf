import time
import yaml
from flask import Flask, request, Response

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
        result = forward_request(request, backend_host, backend_port)

        # buang header yang bisa konflik sebelum dikembalikan ke client
        excluded_headers = [
            "content-encoding", "transfer-encoding",
            "connection", "content-length"
        ]
        response_headers = {
            k: v for k, v in result["headers"].items()
            if k.lower() not in excluded_headers
        }

        return Response(
            response=result["content"],
            status=result["status_code"],
            headers=response_headers
        )

    return app