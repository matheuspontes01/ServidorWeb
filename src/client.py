from __future__ import annotations

import argparse
import socket
import sys
import tempfile
import webbrowser
from dataclasses import dataclass
from pathlib import Path


HEADER_SEPARATOR = b"\n\n"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080


class ProtocolError(Exception):
    """Raised when the server response does not match the expected protocol."""


@dataclass(frozen=True)
class ServerResponse:
    status: str
    content_type: str
    content_length: int
    body: bytes
    headers: dict[str, str]

    @property
    def is_text(self) -> bool:
        content_type = self.content_type.lower()
        return content_type.startswith("text/") or "charset=" in content_type

    @property
    def is_html(self) -> bool:
        return self.content_type.lower().startswith("text/html")


def normalize_path(request_path: str) -> str:
    request_path = request_path.strip() or "/"
    if not request_path.startswith("/"):
        request_path = f"/{request_path}"
    return request_path


def parse_headers(header_bytes: bytes) -> dict[str, str]:
    try:
        header_text = header_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProtocolError("Cabecalho da resposta nao esta em UTF-8") from exc

    headers: dict[str, str] = {}
    for line in header_text.splitlines():
        key, separator, value = line.partition(" ")
        if not separator:
            raise ProtocolError(f"Linha de cabecalho invalida: {line!r}")
        headers[key.upper()] = value.strip()
    return headers


def receive_response(client_socket: socket.socket) -> ServerResponse:
    data = b""

    while HEADER_SEPARATOR not in data:
        chunk = client_socket.recv(4096)
        if not chunk:
            raise ProtocolError("Conexao encerrada antes do fim do cabecalho")
        data += chunk

    header_bytes, body = data.split(HEADER_SEPARATOR, 1)
    headers = parse_headers(header_bytes)

    status = headers.get("STATUS")
    content_type = headers.get("CONTENT-TYPE", "application/octet-stream")
    content_length_text = headers.get("CONTENT-LENGTH")

    if not status:
        raise ProtocolError("Resposta sem cabecalho STATUS")
    if content_length_text is None:
        raise ProtocolError("Resposta sem cabecalho CONTENT-LENGTH")

    try:
        content_length = int(content_length_text)
    except ValueError as exc:
        raise ProtocolError("CONTENT-LENGTH invalido") from exc

    while len(body) < content_length:
        chunk = client_socket.recv(4096)
        if not chunk:
            raise ProtocolError("Conexao encerrada antes do corpo completo")
        body += chunk

    return ServerResponse(
        status=status,
        content_type=content_type,
        content_length=content_length,
        body=body[:content_length],
        headers=headers,
    )


def fetch(host: str, port: int, request_path: str, timeout: float = 10.0) -> ServerResponse:
    request_path = normalize_path(request_path)
    request = f"GET {request_path}\n".encode("utf-8")

    with socket.create_connection((host, port), timeout=timeout) as client_socket:
        client_socket.settimeout(timeout)
        client_socket.sendall(request)
        return receive_response(client_socket)


def print_response(response: ServerResponse) -> None:
    print(f"STATUS {response.status}")
    print(f"CONTENT-TYPE {response.content_type}")
    print(f"CONTENT-LENGTH {response.content_length}")
    print()

    if response.is_text:
        print(response.body.decode("utf-8", errors="replace"), end="")
        if not response.body.endswith(b"\n"):
            print()
        return

    print(response.body)


def save_body(response: ServerResponse, output_path: Path) -> None:
    output_path.write_bytes(response.body)
    print(f"Resposta salva em {output_path}")


def open_html_response(response: ServerResponse) -> Path:
    with tempfile.NamedTemporaryFile("wb", suffix=".html", prefix="servidor-web-", delete=False) as html_file:
        html_file.write(response.body)
        html_path = Path(html_file.name)

    webbrowser.open(html_path.resolve().as_uri())
    return html_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cliente TCP para o servidor web simplificado")
    parser.add_argument("path", nargs="?", default="/", help="Recurso solicitado, por exemplo / ou /hello.txt")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Endereco do servidor")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Porta do servidor")
    parser.add_argument("--timeout", type=float, default=10.0, help="Tempo maximo de espera em segundos")
    parser.add_argument("-o", "--output", type=Path, help="Arquivo para salvar o corpo da resposta")
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Nao abrir respostas HTML no navegador",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        response = fetch(args.host, args.port, args.path, args.timeout)
    except (OSError, ProtocolError) as exc:
        print(f"Erro ao acessar o servidor: {exc}", file=sys.stderr)
        return 1

    if args.output:
        print(f"STATUS {response.status}")
        print(f"CONTENT-TYPE {response.content_type}")
        print(f"CONTENT-LENGTH {response.content_length}")
        try:
            save_body(response, args.output)
        except OSError as exc:
            print(f"Erro ao salvar resposta: {exc}", file=sys.stderr)
            return 1
    elif response.status.startswith("200 ") and response.is_html and not args.no_browser:
        print(f"STATUS {response.status}")
        print(f"CONTENT-TYPE {response.content_type}")
        print(f"CONTENT-LENGTH {response.content_length}")
        try:
            html_path = open_html_response(response)
        except OSError as exc:
            print(f"Erro ao abrir HTML no navegador: {exc}", file=sys.stderr)
            return 1
        print(f"HTML aberto no navegador: {html_path}")
    else:
        print_response(response)

    return 0 if response.status.startswith("200 ") else 2


if __name__ == "__main__":
    raise SystemExit(main())
