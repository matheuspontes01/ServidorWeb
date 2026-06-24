from __future__ import annotations

import argparse
import mimetypes
import socket
import threading
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
WWW_DIR = BASE_DIR / "www"


@dataclass(frozen=True)
class Response:
    status_line: str
    content_type: str
    body: bytes


def sanitize_path(request_path: str) -> Path | None:
    request_path = request_path.strip()
    if not request_path.startswith("/"):
        return None

    relative = request_path.lstrip("/") or "index.html"
    candidate = (WWW_DIR / relative).resolve()

    try:
        candidate.relative_to(WWW_DIR.resolve())
    except ValueError:
        return None

    return candidate


def build_response(request_line: str) -> Response:
    request_line = request_line.strip()
    if not request_line:
        return Response("400 Bad Request", "text/plain; charset=utf-8", b"Empty request\n")

    parts = request_line.split()
    if len(parts) != 2 or parts[0].upper() != "GET":
        return Response(
            "400 Bad Request",
            "text/plain; charset=utf-8",
            b"Use: GET /arquivo\n",
        )

    file_path = sanitize_path(parts[1])
    if file_path is None:
        return Response("400 Bad Request", "text/plain; charset=utf-8", b"Invalid path\n")

    if not file_path.is_file():
        return Response("404 Not Found", "text/plain; charset=utf-8", b"Resource not found\n")

    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    body = file_path.read_bytes()
    return Response("200 OK", content_type, body)


def handle_client(client_socket: socket.socket, address: tuple[str, int]) -> None:
    try:
        with client_socket:
            client_socket.settimeout(10)
            data = client_socket.recv(4096)
            request_line = data.decode("utf-8", errors="replace").splitlines()[0] if data else ""
            thread_name = threading.current_thread().name
            print(f"[{thread_name}] Cliente {address[0]}:{address[1]} solicitou: {request_line or '<vazio>'}")
            response = build_response(request_line)

            header = (
                f"STATUS {response.status_line}\n"
                f"CONTENT-TYPE {response.content_type}\n"
                f"CONTENT-LENGTH {len(response.body)}\n"
                f"CLIENT {address[0]}:{address[1]}\n"
                "\n"
            ).encode("utf-8")
            client_socket.sendall(header + response.body)
    except IndexError:
        try:
            client_socket.sendall(
                b"STATUS 400 Bad Request\nCONTENT-TYPE text/plain; charset=utf-8\nCONTENT-LENGTH 13\n\nEmpty request\n"
            )
        except OSError:
            pass
    except (ConnectionError, OSError):
        pass


def serve(host: str, port: int) -> None:
    WWW_DIR.mkdir(exist_ok=True)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen(10)
        print(f"Servidor web simplificado ativo em {host}:{port}")

        while True:
            client_socket, address = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(client_socket, address), daemon=True)
            thread.start()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Servidor web simplificado com threads")
    parser.add_argument("--host", default="0.0.0.0", help="Endereço para escutar")
    parser.add_argument("--port", type=int, default=8080, help="Porta do servidor")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    serve(args.host, args.port)


if __name__ == "__main__":
    main()
