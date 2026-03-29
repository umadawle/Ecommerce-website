# Ecommerce API — FastAPI + MySQL + MongoDB

A production-ready REST API built from the PRD requirements, implementing all 6 functional modules using **FastAPI**, **MySQL** (via SQLAlchemy + Alembic), and **MongoDB** (via Motor async driver).

---

## 📁 Folder Structure

```
ecommerce/
├── app/
│   ├── main.py                    # FastAPI app factory + lifespan
│   ├── api/
│   │   └── v1/
│   │       ├── router.py          # Aggregates all routers under /api/v1
│   │       ├── deps.py            # Shared FastAPI dependencies (get_current_user)
│   │       └── endpoints/
│   │           ├── auth.py        # POST /auth/login, /auth/refresh, /auth/social-login
│   │           ├── users.py       # POST /users/register, GET/PATCH /users/me, password ops
│   │           ├── products.py    # GET/POST /products, /products/search, /products/{id}
│   │           ├── cart.py        # GET/POST/PATCH/DELETE /cart, POST /cart/checkout
│   │           ├── orders.py      # GET /orders, /orders/{id}, /orders/{id}/track
│   │           └── payments.py    # POST /payments, GET /payments/{id}/receipt
│   ├── core/
│   │   ├── config.py              # Pydantic Settings from .env
│   │   ├── security.py            # JWT creation/decoding, password hashing
│   │   └── exceptions.py          # Custom HTTP exceptions
│   ├── db/
│   │   ├── mysql.py               # SQLAlchemy engine, session, Base
│   │   └── mongo.py               # Motor async MongoDB client + cart collection
│   ├── models/                    # SQLAlchemy ORM models (MySQL tables)
│   │   ├── user.py
│   │   ├── product.py
│   │   ├── order.py               # Order + OrderItem + OrderStatus enum
│   │   └── payment.py             # Payment + PaymentMethod + PaymentStatus enums
│   ├── schemas/                   # Pydantic request/response schemas
│   │   ├── user.py
│   │   ├── product.py
│   │   ├── cart.py                # CartItem, CartResponse, CheckoutRequest
│   │   ├── order.py
│   │   └── payment.py
│   └── services/                  # Business logic layer
│       ├── user_service.py
│       ├── product_service.py
│       ├── cart_service.py        # Async MongoDB operations
│       ├── order_service.py       # Checkout, history, tracking
│       └── payment_service.py
├── alembic/
│   ├── env.py                     # Migration environment (auto-detects models)
│   └── versions/                  # Auto-generated migration scripts
├── tests/                         # Pytest test directory
├── alembic.ini
├── requirements.txt
├── run.py                         # python run.py to start server
└── .env.example                   # Copy to .env and fill in values
```

---

## 🗂 Database Design

| Model | Database | Purpose |
|---|---|---|
| `User` | MySQL | Registration, auth, profile |
| `Product` | MySQL | Catalog, search, stock |
| `Order` + `OrderItem` | MySQL | Orders, line items, tracking |
| `Payment` | MySQL | Transaction records, receipts |
| Cart document | **MongoDB** | Flexible per-user cart (schema-free) |

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.11+
- MySQL 8.0+ running locally
- MongoDB 6.0+ running locally

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env with your MySQL and MongoDB credentials
```

### 4. Create MySQL database
```sql
CREATE DATABASE ecommerce_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. Run the server
```bash
python run.py
# OR
uvicorn app.main:app --reload
```

> Tables are auto-created on startup via `Base.metadata.create_all()`.  
> For production, use Alembic migrations instead (see below).

### 6. Open the interactive docs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🔐 Authentication Flow

```
POST /api/v1/users/register   →  Create account
POST /api/v1/auth/login       →  Get access_token + refresh_token
Authorization: Bearer <access_token>  →  All protected routes
POST /api/v1/auth/refresh     →  Exchange refresh_token for new access_token
```

---

## 📦 API Endpoints Summary

### Authentication
| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/auth/login` | Login (returns JWT) |
| POST | `/api/v1/auth/social-login` | Social OAuth login/register |
| POST | `/api/v1/auth/refresh` | Refresh access token |

### User Management
| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/users/register` | Register new user |
| GET | `/api/v1/users/me` | Get profile |
| PATCH | `/api/v1/users/me` | Update profile |
| POST | `/api/v1/users/me/change-password` | Change password |
| POST | `/api/v1/users/forgot-password` | Request reset link |
| POST | `/api/v1/users/reset-password` | Reset via token |

### Product Catalog
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/products/` | Browse (with category filter + pagination) |
| GET | `/api/v1/products/categories` | All categories |
| GET | `/api/v1/products/search?q=` | Keyword search |
| GET | `/api/v1/products/{id}` | Product detail |
| POST | `/api/v1/products/` | Create product (auth) |
| PATCH | `/api/v1/products/{id}` | Update product (auth) |
| DELETE | `/api/v1/products/{id}` | Deactivate product (auth) |

### Cart & Checkout
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/cart/` | View cart |
| POST | `/api/v1/cart/items` | Add item |
| PATCH | `/api/v1/cart/items/{product_id}` | Update quantity |
| DELETE | `/api/v1/cart/items/{product_id}` | Remove item |
| DELETE | `/api/v1/cart/` | Clear cart |
| POST | `/api/v1/cart/checkout` | Place order from cart |

### Orders
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/orders/` | Order history |
| GET | `/api/v1/orders/{id}` | Order details + confirmation |
| GET | `/api/v1/orders/{id}/track` | Delivery tracking |

### Payments
| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/payments/` | Initiate payment |
| GET | `/api/v1/payments/` | Payment history |
| GET | `/api/v1/payments/{id}/receipt` | Download receipt |

---

## 🗄 Alembic Migrations (Production)

```bash
# Generate a migration after model changes
alembic revision --autogenerate -m "describe change"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

---

## ⚙️ Key Design Decisions

| Decision | Reason |
|---|---|
| MySQL for structured data | Users, Products, Orders, Payments have fixed schemas with relational integrity |
| MongoDB for Cart | Cart items vary per user; flexible document structure avoids schema churn |
| Motor (async) for MongoDB | Non-blocking I/O for cart operations alongside FastAPI's async support |
| JWT access + refresh tokens | Short-lived access tokens + long-lived refresh for secure session management |
| Service layer pattern | Keeps endpoint files thin; business logic isolated and testable |
| Pydantic v2 schemas | Strict validation, serialization, and OpenAPI doc generation |
| Soft delete for products | Preserves historical order data integrity |
| Stock snapshot in OrderItem | Price/name at purchase time preserved even if product is later updated |
