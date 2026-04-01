# AssemblPro - Votacao Eletronica Segura

Sistema de Votacao Eletronica Segura para Cooperativas, desenvolvido com FastAPI + SQLAlchemy.

## Tecnologias

- **Backend:** FastAPI, Uvicorn, SQLAlchemy (async com asyncpg)
- **Banco de Dados:** PostgreSQL
- **Autenticacao:** JWT + OTP (pyotp)
- **Templates:** Jinja2
- **Container:** Docker + Docker Compose
- **Proxy Reverso:** Traefik (producao)

## Estrutura do Projeto

```
assemblpro/
├── app/
│   ├── main.py              # Aplicacao FastAPI principal
│   ├── config.py            # Configuracoes (pydantic-settings)
│   ├── database.py          # Conexao com o banco de dados
│   ├── models/              # Modelos SQLAlchemy
│   ├── routers/             # Endpoints da API e views
│   ├── schemas/             # Schemas Pydantic
│   ├── services/            # Servicos (email, SMS, auditoria)
│   ├── templates/           # Templates Jinja2 (HTML)
│   └── utils/               # Utilitarios
├── static/                  # Arquivos estaticos (CSS, JS, imagens)
├── scripts/                 # Scripts auxiliares
├── run.py                   # Ponto de entrada da aplicacao
├── requirements.txt         # Dependencias Python
├── Dockerfile               # Imagem Docker
├── docker-compose.dev.yml   # Compose para desenvolvimento (sem Traefik)
├── docker-compose.prod.yml  # Compose para producao (com Traefik)
├── docker-compose.yml       # Compose ativo (ignorado pelo git)
└── .env                     # Variaveis de ambiente (ignorado pelo git)
```

## Configuracao

### 1. Variaveis de Ambiente

Crie o arquivo `.env` na raiz do projeto com as seguintes variaveis:

```env
APP_ENV=development
APP_NAME=AssemblPro - Votacao Eletronica Segura
APP_URL=http://localhost:8033

# Database
DATABASE_URL=postgresql+asyncpg://usuario:senha@host:5432/assemblpro
DATABASE_URL_SYNC=postgresql+psycopg2://usuario:senha@host:5432/assemblpro

# Seguranca
SECRET_KEY=sua_secret_key
JWT_SECRET_KEY=sua_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# Criptografia
ENCRYPTION_KEY=sua_encryption_key
```

### 2. Docker Compose

O projeto possui dois arquivos de compose versionados:

| Arquivo                    | Descricao                                             |
|----------------------------|-------------------------------------------------------|
| `docker-compose.dev.yml`   | Desenvolvimento - sem Traefik, sem rede proxy         |
| `docker-compose.prod.yml`  | Producao - com Traefik, HTTPS e rede proxy externa    |
| `docker-compose.yml`       | Arquivo ativo usado pelo Docker (ignorado pelo git)   |

O `docker-compose.yml` nao e versionado no git. Para utilizá-lo, copie o arquivo desejado:

```bash
# Para desenvolvimento
cp docker-compose.dev.yml docker-compose.yml

# Para producao
cp docker-compose.prod.yml docker-compose.yml
```

## Executando com Docker

### Desenvolvimento

```bash
# Usando o arquivo de dev diretamente
docker compose -f docker-compose.dev.yml up -d --build

# Ou copiando para docker-compose.yml
cp docker-compose.dev.yml docker-compose.yml
docker compose up -d --build
```

No modo desenvolvimento, a aplicacao roda na porta **8033** sem proxy reverso. Acesse em `http://localhost:8033`.

### Producao

```bash
# Usando o arquivo de prod diretamente
docker compose -f docker-compose.prod.yml up -d --build

# Ou copiando para docker-compose.yml
cp docker-compose.prod.yml docker-compose.yml
docker compose up -d --build
```

No modo producao, o Traefik atua como proxy reverso com:

- **URL:** `https://assemblpro.mediatize.com.br`
- **HTTP -> HTTPS:** Redirect automatico (301)
- **TLS:** Certificado Let's Encrypt
- **Rede:** `proxy` (externa, compartilhada com o Traefik)

### Comandos Uteis

```bash
# Ver logs do container
docker logs assemblpro

# Acompanhar logs em tempo real
docker logs -f assemblpro

# Parar o container
docker compose down

# Rebuild apos alteracao no requirements.txt
docker compose up -d --build

# Acessar o shell do container
docker exec -it assemblpro bash
```

## Executando sem Docker

```bash
# Criar e ativar virtualenv
python -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Executar
python run.py
```

A aplicacao estara disponivel em `http://localhost:8033`.

## Volumes Mapeados

O container nao copia o codigo-fonte. Os arquivos sao mapeados via volumes, permitindo que alteracoes no host sejam refletidas automaticamente (o Uvicorn roda com `reload=True`):

| Host                | Container                | Modo |
|---------------------|--------------------------|------|
| `./app`             | `/app/app`               | ro   |
| `./static`          | `/app/static`            | ro   |
| `./run.py`          | `/app/run.py`            | ro   |
| `./requirements.txt`| `/app/requirements.txt`  | ro   |
| `./.env`            | `/app/.env`              | ro   |

> **Nota:** Todos os volumes sao montados como somente leitura (`ro`). Caso precise de escrita (ex: uploads), altere o modo no compose.

## API

- **Health Check:** `GET /api/health`
- **Documentacao Swagger:** `GET /docs`
- **Documentacao ReDoc:** `GET /redoc`
