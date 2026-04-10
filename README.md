# Caveira Atacado

Patch de deploy para Railway.

## Ajustes incluídos

- troca do driver PostgreSQL para `psycopg[binary]`, evitando o erro de `libpq.so.5`
- normalização automática da `DATABASE_URL` para SQLAlchemy usar `postgresql+psycopg://`
- `Procfile` com `web: gunicorn run:app`
- bootstrap automático do banco com `db.create_all()` no startup
- seed inicial automática para criar categorias, produtos de exemplo e admin quando o banco estiver vazio

## Railway

### Start Command

Se o Railway pedir start command manual, use:

```bash
gunicorn run:app
```

### Variáveis de ambiente mínimas

- `SECRET_KEY`
- `DATABASE_URL`
- `UPLOAD_FOLDER`
- `BASE_URL`
- `MERCADOPAGO_ACCESS_TOKEN`
- `MERCADOPAGO_PUBLIC_KEY`

### Variáveis novas deste patch

- `AUTO_CREATE_DB=true`
- `AUTO_SEED_DATA=true`

Essas duas opções permitem que o projeto suba no Railway mesmo sem rodar migration manual. Na primeira inicialização, as tabelas são criadas automaticamente.

## Login admin inicial

Quando `AUTO_SEED_DATA=true`, o sistema cria:

- usuário: `admin@caveiraatacado.com`
- senha: `admin123`

Troque essa senha assim que subir em produção.

## Observação

Esse patch resolve o erro de tabela inexistente como `relation "product" does not exist`, porque agora o app cria as tabelas automaticamente no boot quando o banco estiver vazio.
