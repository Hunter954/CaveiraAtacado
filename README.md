# Caveira Atacado

Projeto de e-commerce MVP em **Python + Flask**, com frontend em **Jinja2/HTML/CSS/JS**, banco **PostgreSQL**, integração com **Mercado Pago**, consulta de **CEP automática via ViaCEP**, painel administrativo, carrinho, checkout e estrutura pronta para deploy no **Railway**.

## O que está incluído

- Home com identidade visual preto/vermelho inspirada no layout de referência
- Catálogo de produtos com busca, categoria e ordenação
- Página de produto com cálculo de frete por CEP
- Carrinho com cupom e frete
- Checkout com criação de pedido e redirecionamento para Mercado Pago
- Cadastro, login, logout e recuperação de senha por token
- Área do cliente com pedidos e endereços
- Painel administrativo para produtos, categorias, pedidos, clientes e cupons
- Upload de imagens preparado para volume persistente
- Seeds iniciais para catálogo e usuário administrador

## Stack

- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-Login
- PostgreSQL
- Mercado Pago SDK
- ViaCEP
- Railway

## Estrutura

```text
app/
  admin/
  services/
  utils/
  templates/
  static/
  models.py
  routes.py
run.py
requirements.txt
.env.example
README.md
```

## Como rodar localmente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask db init
flask db migrate -m "initial"
flask db upgrade
flask seed
python run.py
```

Acesse em `http://localhost:5000`.

## Credenciais seed

- Admin: `admin@caveiraatacado.com`
- Senha: `admin123`

Troque isso imediatamente em ambiente real.

## Variáveis de ambiente

Confira o arquivo `.env.example`. As principais são:

- `SECRET_KEY`
- `DATABASE_URL`
- `MERCADOPAGO_ACCESS_TOKEN`
- `MERCADOPAGO_PUBLIC_KEY`
- `MERCADOPAGO_WEBHOOK_SECRET`
- `UPLOAD_FOLDER`
- `BASE_URL`

## Mercado Pago

O projeto está configurado para criar uma **preference** no checkout e redirecionar o usuário para o fluxo do Mercado Pago.

### Observações importantes

- Para produção, valide o payload do webhook com mais rigor.
- Dependendo do produto/conta, cartão, PIX e boleto aparecem no Checkout Pro do Mercado Pago conforme a conta e configurações da integração.
- O webhook base está em `/webhooks/mercado-pago`.
- Recomenda-se complementar a rotina de sincronização com consulta da API do Mercado Pago no webhook para confirmação robusta do status.

## CEP automático

O preenchimento automático usa ViaCEP no endpoint interno:

- `GET /api/cep/<cep>`

O JavaScript preenche rua, bairro, cidade e UF automaticamente em checkout e endereços.

## Imagens em volume no Railway

Configure um volume e aponte `UPLOAD_FOLDER` para o diretório persistente montado, por exemplo:

```env
UPLOAD_FOLDER=/data/uploads
```

No Railway:

1. Crie o volume.
2. Monte o volume no serviço web.
3. Defina a variável `UPLOAD_FOLDER` apontando para o path persistente.
4. Garanta permissão de escrita no diretório.

## PostgreSQL no Railway

Use a `DATABASE_URL` fornecida pelo plugin do Postgres. O projeto já lê essa variável automaticamente.

## GitHub e deploy

1. Suba o projeto para um repositório.
2. Conecte o repositório ao Railway.
3. Adicione as variáveis de ambiente.
4. Configure o start command:

```bash
gunicorn run:app
```

5. Rode as migrations no ambiente.

## Pontos para evoluir depois

- permissões admin por papel
- cálculo de frete real por transportadora/correios
- consulta robusta do webhook Mercado Pago
- lista de desejos
- avaliações
- CMS institucional
- emissão fiscal e ERP

## Limitações conhecidas deste MVP

Este pacote entrega uma base funcional e organizada para subir no GitHub e evoluir. Ainda assim, para operação em produção com alto volume, vale reforçar:

- validações avançadas de formulário
- antifraude e regras de pagamento
- observabilidade/logging centralizado
- testes automatizados
- revisão de segurança e LGPD operacional
