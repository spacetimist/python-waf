import requests

def forward_request(original_request, backend_host: str, backend_port: int):
    """
    Meneruskan permintaan yang diizinkan ke aplikasi backend
    dan mengembalikan responnya.
    """
    # bangun URL tujuan
    url = f"http://{backend_host}:{backend_port}{original_request.path}"
    if original_request.query_string:
        url += "?" + original_request.query_string.decode("utf-8", errors="replace")

    # salin headers tapi hapus header yang bisa konflik
    headers = {
        k: v for k, v in original_request.headers.items()
        if k.lower() not in ["host", "content-length", "transfer-encoding",
                              "accept-encoding"]
    }
    # nonaktifkan kompresi supaya response bisa dibaca langsung
    headers["Accept-Encoding"] = "identity"

    try:
        # gabungkan cookie dari header dan dari request.cookies
        cookie_header = original_request.headers.get("Cookie", "")
        if cookie_header:
            headers["Cookie"] = cookie_header

        response = requests.request(
            method=original_request.method,
            url=url,
            headers=headers,
            data=original_request.get_data(),
            allow_redirects=False,
            timeout=10
        )

        # kembalikan konten, status code, dan headers dari backend
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