import json
import socket
import time

ADDRESS = ("127.0.0.1", 18080)
body = json.dumps({"messages": [{"role": "user", "content": "こんにちは"}],
                   "max_tokens": 16}, ensure_ascii=False).encode("utf-8")

def read_response(conn):
    response = bytearray()
    while True:
        chunk = conn.recv(65536)
        if not chunk:
            break
        response.extend(chunk)
    header, data = bytes(response).split(b"\r\n\r\n", 1)
    return header, data

for attempt in range(100):
    try:
        with socket.create_connection(ADDRESS, timeout=1):
            pass
        break
    except OSError:
        time.sleep(0.1)
else:
    raise RuntimeError("Test server failed to start")

header = (f"POST /v1/chat/completions HTTP/1.1\r\nHost: localhost\r\n"
          f"Content-Type: application/json\r\nContent-Length: {len(body)}\r\n").encode()

for expect_continue in (False, True):
    with socket.create_connection(ADDRESS, timeout=5) as conn:
        # Split both the HTTP headers and the UTF-8 body across TCP writes.
        conn.sendall(header[:13])
        time.sleep(0.1)
        tail = b"Expect: 100-continue\r\n" if expect_continue else b""
        conn.sendall(header[13:] + tail + b"\r\n")
        if expect_continue:
            interim = bytearray()
            while b"\r\n\r\n" not in interim:
                interim.extend(conn.recv(1024))
            assert bytes(interim) == b"HTTP/1.1 100 Continue\r\n\r\n", interim
        time.sleep(0.1)
        for offset in range(0, len(body), 7):
            conn.sendall(body[offset:offset+7])
            time.sleep(0.01)
        response_header, data = read_response(conn)
        assert response_header.startswith(b"HTTP/1.1 200 OK"), (response_header, data)
        assert json.loads(data)["choices"][0]["message"]["content"] == "日本語テスト"

with socket.create_connection(ADDRESS, timeout=5) as conn:
    conn.sendall(b"POST /v1/chat/completions HTTP/1.1\r\nContent-Length: -1\r\n\r\n")
    response_header, _ = read_response(conn)
    assert response_header.startswith(b"HTTP/1.1 400 Bad Request"), response_header

print("PASS: fragmented headers/body, UTF-8, Expect 100 Continue, invalid length")
