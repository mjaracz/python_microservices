# Python Microservices — Event-Driven Architecture (AMQP + FastAPI + RabbitMQ)

This repository contains a fully working **microservices-based system** built in Python, using:

- **FastAPI** as API Gateway
- **RabbitMQ (AMQP)** as event and RPC bus
- **MongoDB** for Posts service
- **PostgreSQL** for Users service
- **Shared internal Python package** for cross-cutting concerns
- **Async workers** (no exposed HTTP endpoints except the gateway)
- **Local development tooling** including hot-reload and per-service virtual environments

---

# Features

✔ Event-driven microservices  
✔ RPC via AMQP (Request/Reply)  
✔ REST + WebSocket API Gateway  
✔ Per-service database isolation  
✔ Clean repository pattern  
✔ Shared code packaged as a local Python library  
✔ Hot reload for local development (`watchfiles`)  
✔ Python `src/` layout (enterprise-grade packaging)

---

# 📦 1. Prerequisites

Before running the system, ensure that the following tools are installed on your machine:

## Python ≥ 3.10

Recommended installation methods:

- **Linux (Ubuntu)**
  ```bash
  sudo apt install python3 python3-venv python3-dev
  ```
- Docs: https://www.python.org/downloads/

## 🐋 Docker & Docker Compose

Required for running the external services:

- RabbitMQ
- MongoDB
- PostgreSQL

Installation links:

- Docker: https://docs.docker.com/get-docker/
- Docker Compose: https://docs.docker.com/compose/install/

## 🔧 Build essentials (Linux)

```bash
sudo apt install build-essential libpq-dev
```

---

# 2. Running the Project Locally (Step by Step)

The project includes a development script `run-local-dev.sh` that:

- creates a separate `.venv` for each microservice
- installs shared library locally
- installs microservice dependencies from `pyproject.toml`
- runs workers in watch-reload mode
- runs the API Gateway with auto-reload
- stores logs in `/logs` directory

## Step 1 — Start external infrastructure

```bash
docker compose up -d rabbitmq mongo_posts postgres_users
```

## Step 2 — Start microservices

```bash
./run-local-dev.sh
```

## Step 3 — Use the API Gateway

REST: `http://localhost:8000`  
WebSocket: `ws://localhost:8000/ws`

---

# 🏛 3. Architecture Overview

This system implements a **fully asynchronous microservices architecture** based on **RabbitMQ (AMQP)**.

```
                ┌────────────────────────────────────────┐
                │              API Gateway               │
                │     FastAPI • REST • WebSocket RPC     │
                └───────────────┬───────────────┬────────┘
                                │               │
                    RPC over AMQP               │
                                │               │
        ┌───────────────────────▼───────┐      │
        │             Posts              │      │
        │   async worker • MongoDB       │      │
        └────────────────────────────────┘      │
                                                │
        ┌────────────────────────────────┐      │
        │              Users             │◄─────┘
        │   async worker • PostgreSQL    │
        └────────────────────────────────┘
```

---

# 4. Communication Model

### ✔ Workers communicate **only through AMQP**

There are:

- no REST endpoints
- no WebSocket endpoints
- no direct network exposure

Workers = "pure event consumers".

## Event Flow — Example: Create Post

1. `api-gateway` receives request (REST or WS)
2. Gateway makes RPC call → `posts` via AMQP
3. `posts` worker consumes message
4. Worker stores data in MongoDB
5. Worker replies via AMQP
6. API Gateway returns response

---

# 5. API Gateway (The Only Exposed Entry Point)

API Gateway is responsible for:

- Authentication (JWT)
- REST interface
- WebSocket real-time communication
- RPC client to workers
- Metrics & observability middleware
- Error handling

All worker interactions happen **via AMQP RPC**.

---

# 6. Database Isolation

Each microservice has its own independent database instance:

| Service | Database   | Type  |
| ------- | ---------- | ----- |
| posts   | MongoDB    | NoSQL |
| users   | PostgreSQL | SQL   |

No shared database — each service owns its domain and data.

---

# 7. Directory Structure

```
root/
│
├── api-gateway/
│   ├── pyproject.toml
│   ├── src/api_gateway/
│   │   ├── app/main.py
│   │   ├── app/auth.py
│   │   ├── app/ws_manager.py
│   │   └── app/middleware/metrics_middleware.py
│
├── posts/
│   ├── pyproject.toml
│   ├── src/posts/
│   │   ├── app/main.py
│   │   ├── app/repository.py
│   │   └── app/models.py
│
├── users/
│   ├── pyproject.toml
│   ├── src/users/
│   │   ├── app/main.py
│   │   ├── app/repository.py
│   │   └── app/schemas.py
│
├── shared/
│   ├── pyproject.toml
│   ├── src/shared/
│   │   ├── messagebus/messagebus.py
│   │   └── database/{mongo.py, postgres.py}
│
├── docker-compose.yml
├── run-local-dev.sh
└── README.md
```

---

# 8. Shared Package

Located in `shared/`, installed using:

```bash
pip install -e shared/
```

Includes:

- MessageBus abstraction
- Repository utilities
- Shared DTOs
- AMQP RPC helpers
- Connection pooling helpers (Mongo + Postgres)

---

# 9. AMQP-Based Worker Communication

Workers communicate **exclusively** using RabbitMQ:

### Patterns Used:

- Topic exchanges
- RPC reply queues
- `@MessagePattern` decorator (MessageBus helper)

Workers never expose HTTP endpoints.

---

# 10. Why This Architecture?

This layout reflects modern microservices practices:

✔ isolated domains  
✔ isolated databases  
✔ async RPC  
✔ horizontal worker scaling  
✔ observability middleware  
✔ shared library for cross-service logic

---

# 🤝 Contributing

Pull requests welcome.

# 📄 License

MIT License.
