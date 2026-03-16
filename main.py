import yaml
from src.server import create_app

if __name__ == "__main__":
    with open("config/config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    server_cfg = config.get("server", {})
    host = server_cfg.get("host", "0.0.0.0")
    port = server_cfg.get("port", 8000)

    app = create_app()
    print(f"Python WAF berjalan di http://{host}:{port}")
    app.run(host=host, port=port, debug=False)