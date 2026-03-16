import logging
import json
import os
from datetime import datetime

def setup_logger(log_path: str, level: str = "INFO"):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    logger = logging.getLogger("python_waf")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # hindari duplikasi handler kalau dipanggil berkali-kali
    if logger.handlers:
        return logger

    # handler ke file
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))

    # handler ke terminal
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def log_request(logger, request_info: dict, triggered_rules: list, 
                total_score: int, decision: str, latency_ms: float):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "src_ip": request_info.get("src_ip", "-"),
        "method": request_info.get("method", "-"),
        "uri": request_info.get("uri", "-"),
        "triggered_rules": triggered_rules,
        "total_score": total_score,
        "decision": decision,
        "latency_ms": round(latency_ms, 3)
    }
    logger.info(json.dumps(log_entry, ensure_ascii=False))