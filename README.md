# Minipedia

Aplicação Flask simples para gerenciar coleção de miniaturas de carros.

## Rotas
- `/` página inicial
- `/login`, `/register`, `/logout`
- `/colecao` (protegida)
- `/colecao/add` (POST)
- `/colecao/delete/<id>`

## Credenciais padrão
Admin criado automaticamente: `admin@miniaturas.local` / `admin`

## Execução local
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export FLASK_ENV=production
python app.py
```

## Render.com
- Defina `DATABASE_URL` (PostgreSQL) e opcionalmente `SECRET_KEY`.
- Comando de start: `waitress-serve --host=0.0.0.0 --port=$PORT app:app` (já incluso no `Procfile`).
- A aplicação cria as tabelas e o admin no startup.
