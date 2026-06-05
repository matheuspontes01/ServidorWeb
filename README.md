# Servidor Web Simplificado - Parte 1

Nesta etapa do projeto, o foco é apenas a parte do servidor.

## Escopo mínimo

- Servidor TCP em Python
- Atendimento de múltiplos clientes com threads
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
- `www/`: arquivos estáticos servidos

## Execução

```bash
python3 -m src.server
```

O servidor escuta em `0.0.0.0:8080` por padrão.