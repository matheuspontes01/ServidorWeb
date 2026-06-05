from __future__ import annotations

import argparse
import html
import json
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

try:
    from .client import DEFAULT_HOST, DEFAULT_PORT, ProtocolError, ServerResponse, fetch
except ImportError:
    from client import DEFAULT_HOST, DEFAULT_PORT, ProtocolError, ServerResponse, fetch


DEFAULT_INTERFACE_HOST = "127.0.0.1"
DEFAULT_INTERFACE_PORT = 9000
STATIC_DIR = Path(__file__).resolve().parent / "browser_client_static"
CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
}


class BrowserClientHandler(BaseHTTPRequestHandler):
    target_host = DEFAULT_HOST
    target_port = DEFAULT_PORT
    timeout = 10.0

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)

        if parsed_url.path == "/":
            self._send_index()
            return

        if parsed_url.path == "/api/request":
            self._handle_request(parsed_url.query)
            return

        self._send_static(parsed_url.path)

    def _send_index(self) -> None:
        index_html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
        index_html = index_html.replace("__TARGET_HOST__", html.escape(self.target_host, quote=True))
        index_html = index_html.replace("__TARGET_PORT__", str(self.target_port))
        self._send_bytes(index_html.encode("utf-8"), CONTENT_TYPES[".html"])

    def _send_static(self, request_path: str) -> None:
        file_name = request_path.lstrip("/")
        static_path = (STATIC_DIR / file_name).resolve()

        try:
            static_path.relative_to(STATIC_DIR.resolve())
        except ValueError:
            self._send_json({"ok": False, "error": "Caminho invalido"}, HTTPStatus.BAD_REQUEST)
            return

        if not static_path.is_file():
            self._send_json({"ok": False, "error": "Rota nao encontrada"}, HTTPStatus.NOT_FOUND)
            return

        content_type = CONTENT_TYPES.get(static_path.suffix, "application/octet-stream")
        self._send_bytes(static_path.read_bytes(), content_type)

    def _handle_request(self, query: str) -> None:
        params = parse_qs(query)
        host = _first(params, "host", self.target_host).strip()
        path = _first(params, "path", "/").strip() or "/"

        try:
            port = int(_first(params, "port", str(self.target_port)))
        except ValueError:
            self._send_json({"ok": False, "error": "Porta invalida"}, HTTPStatus.BAD_REQUEST)
            return

        try:
            response = fetch(host, port, path, self.timeout)
        except (OSError, ProtocolError) as exc:
            self._send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_GATEWAY)
            return

        self._send_json(_response_payload(response))

    def _send_json(self, payload: dict[str, object], status: HTTPStatus = HTTPStatus.OK) -> None:
        self._send_bytes(json.dumps(payload).encode("utf-8"), "application/json; charset=utf-8", status)

    def _send_bytes(
        self,
        body: bytes,
        content_type: str,
        status: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _first(params: dict[str, list[str]], key: str, default: str) -> str:
    values = params.get(key)
    return values[0] if values else default


def _response_payload(response: ServerResponse) -> dict[str, object]:
    if response.is_text:
        body_text = response.body.decode("utf-8", errors="replace")
    else:
        body_text = repr(response.body)

    return {
        "ok": True,
        "status": response.status,
        "content_type": response.content_type,
        "content_length": response.content_length,
        "body_text": body_text,
        "is_html": response.is_html,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interface web para o cliente TCP")
    parser.add_argument("--listen-host", default=DEFAULT_INTERFACE_HOST, help="Endereco da interface web")
    parser.add_argument("--listen-port", type=int, default=DEFAULT_INTERFACE_PORT, help="Porta da interface web")
    parser.add_argument("--target-host", default=DEFAULT_HOST, help="Endereco padrao do servidor TCP")
    parser.add_argument("--target-port", type=int, default=DEFAULT_PORT, help="Porta padrao do servidor TCP")
    parser.add_argument("--timeout", type=float, default=10.0, help="Tempo maximo de espera em segundos")
    parser.add_argument("--no-open", action="store_true", help="Nao abrir a interface no navegador automaticamente")
    return parser.parse_args()


def serve(args: argparse.Namespace) -> None:
    BrowserClientHandler.target_host = args.target_host
    BrowserClientHandler.target_port = args.target_port
    BrowserClientHandler.timeout = args.timeout

    with ThreadingHTTPServer((args.listen_host, args.listen_port), BrowserClientHandler) as http_server:
        host, port = http_server.server_address
        url = f"http://{host}:{port}/"
        print(f"Interface do cliente ativa em {url}")
        print("Pressione Ctrl+C para encerrar.")

        if not args.no_open:
            webbrowser.open(url)

        try:
            http_server.serve_forever()
        except KeyboardInterrupt:
            print("\nInterface encerrada.")


def main() -> None:
    serve(parse_args())


if __name__ == "__main__":
    main()
