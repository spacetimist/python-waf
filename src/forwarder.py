import requests

def forward_request(original_request, backend_host: str, backend_port: int, request_data: bytes = None):
    url = f"http://{backend_host}:{backend_port}{original_request.path}"
    if original_request.query_string:
        url += "?" + original_request.query_string.decode("utf-8", errors="replace")

    # salin headers tapi hapus header yang bisa konflik
    headers = {
        k: v for k, v in original_request.headers.items()
        if k.lower() not in ["host", "content-length", "transfer-encoding",
                              "accept-encoding"]
    }
    headers["Accept-Encoding"] = "identity"

    # teruskan cookie dari browser langsung ke backend
    cookie_header = original_request.headers.get("Cookie", "")
    if cookie_header:
        headers["Cookie"] = cookie_header

    try:
        # debug - log apa yang dikirim ke backend
        import logging
        fwd_logger = logging.getLogger("python_waf")
        fwd_logger.debug(f"Forwarding to: {url}")
        fwd_logger.debug(f"Forwarding headers: {headers}")
        fwd_logger.debug(f"Forwarding data: {original_request.get_data()}")
        
        response = requests.request(
            method=original_request.method,
            url=url,
            headers=headers,
            data=request_data,
            allow_redirects=False,
            timeout=10
        )

        return {
            "content": response.content,
            "status_code": response.status_code,
            "headers": dict(response.headers)
        }

    except requests.exceptions.ConnectionError:
        return {
            "content": b"Backend tidak dapat dijangkau.",
            "status_code": 502,
            "headers": {}
        }
    except requests.exceptions.Timeout:
        return {
            "content": b"Backend timeout.",
            "status_code": 504,
            "headers": {}
        }
    except Exception as e:
        return {
            "content": f"Error: {str(e)}".encode(),
            "status_code": 500,
            "headers": {}
        }