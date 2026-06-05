# Servidor Web Simplificado

Projeto com um servidor TCP simplificado e um cliente de linha de comando.

## Escopo

- Servidor TCP em Python
- Atendimento de múltiplos clientes com threads
- Cliente TCP em Python
- Interface do cliente no navegador
- Recurso estático simples na pasta `www/`

## Protocolo de comunicação

O cliente envia uma linha no formato:

```text
GET /arquivo
```

Respostas previstas:

- `200 OK`
- `400 Bad Request`
- `404 Not Found`

## Estrutura

- `src/`: código do servidor
- `src/client.py`: cliente de linha de comando
- `src/browser_client.py`: cliente com interface no navegador
- `src/browser_client_static/`: HTML, CSS e JavaScript da interface
- `www/`: arquivos estáticos servidos

## Executar o servidor

```bash
python3 -m src.server
```

O servidor escuta em `0.0.0.0:8080` por padrão.

Também é possível informar endereço e porta:

```bash
python3 -m src.server --host 127.0.0.1 --port 8080
```

## Executar o cliente

Em outro terminal, solicite a página inicial:

```bash
python3 -m src.client /
```

Quando a resposta for HTML, o cliente abre o conteúdo no navegador padrão.

Ou solicite um arquivo específico:

```bash
python3 -m src.client /hello.txt
```

Para imprimir o HTML no terminal em vez de abrir o navegador:

```bash
python3 -m src.client / --no-browser
```

Para salvar apenas o corpo da resposta em um arquivo:

```bash
python3 -m src.client /hello.txt --output resposta.txt
```

## Executar a interface no navegador

Com o servidor em execucao, abra a interface visual:

```bash
python3 -m src.browser_client
```

Ela inicia uma pagina local em `http://127.0.0.1:9000/`.
Na interface, informe o arquivo desejado, por exemplo `/` ou `/index.html`, e clique em `Buscar`.
Se a resposta for HTML, o conteudo aparece renderizado na previa da pagina.
