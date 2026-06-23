# 📊 Bond Analysis Dashboard

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge\&logo=python\&logoColor=white)
![Django](https://img.shields.io/badge/Django-REST%20Framework-092E20?style=for-the-badge\&logo=django\&logoColor=white)
![React](https://img.shields.io/badge/React-Vite-61DAFB?style=for-the-badge\&logo=react\&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-4169E1?style=for-the-badge\&logo=postgresql\&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-AI%20Research-412991?style=for-the-badge\&logo=openai\&logoColor=white)
![JWT](https://img.shields.io/badge/Auth-JWT-orange?style=for-the-badge)

A full-stack bond analysis platform for monitoring, researching, and evaluating bonds through a modern Portfolio and Watchlist dashboard.

The application combines traditional bond analytics, user-specific portfolio management, FX-aware calculations, email-secured authentication, and AI-assisted public web research for bond discovery and market data refresh.

> ⚠️ **Disclaimer:** This application is for educational and analytical purposes only.
> It does not provide investment advice, financial advice, legal advice, tax advice, or buy/sell recommendations.

---

## ✨ Overview

**Bond Analysis Dashboard** helps users organize and evaluate bonds through two main areas:

* **Portfolio** — bonds the user already owns.
* **Watchlist** — bonds the user monitors before buying.

The app calculates risk indicators, yield metrics, portfolio-level analytics, FX-aware values, stress-test scenarios, and AI-researched market refreshes. It also supports an AI discovery workflow that can search for bond candidates and import structured results for review.

AI-researched data is always stored with transparency metadata, including source URL, retrieval timestamp, confidence level, review status, missing fields, and raw research payload.

---

## 📌 Table of Contents

* [Core Features](#-core-features)
* [Technology Stack](#-technology-stack)
* [Application Architecture](#-application-architecture)
* [Main Modules](#-main-modules)
* [AI Research Workflow](#-ai-research-workflow)
* [Market Data Transparency](#-market-data-transparency)
* [Project Structure](#-project-structure)
* [Installation Guide](#-installation-guide)
* [Environment Variables](#-environment-variables)
* [Running the Application](#-running-the-application)
* [Useful Commands](#-useful-commands)
* [Security Notes](#-security-notes)
* [Known Limitations](#-known-limitations)
* [Future Improvements](#-future-improvements)

---

## 🚀 Core Features

### 🔐 Authentication & Account Security

* User signup.
* Email verification with temporary verification code.
* Login with JWT authentication.
* Forgot password flow.
* Password reset using a temporary code.
* Protected private routes.
* Public dashboard preview for non-authenticated users.

---

### 🏠 Dashboard

* Portfolio summary.
* Bond count.
* Risk overview.
* Signal overview.
* Public preview mode for guests.
* Private dashboard for authenticated users.

---

### 💼 Portfolio

The Portfolio section is designed for bonds already owned by the user.

Key features:

* Add bonds to Portfolio.
* Store quantity and purchase price.
* Calculate current position value.
* Calculate total portfolio value.
* Calculate weighted average YTM.
* Calculate weighted current yield.
* Calculate weighted modified duration.
* Calculate weighted risk score.
* Calculate currency exposure.
* Estimate annual coupon income.
* Run interest rate stress tests.
* Show risk and signal indicators.
* Refresh Portfolio market data through AI-assisted public web research.

---

### 👀 Watchlist

The Watchlist section is designed for bonds the user is monitoring before buying.

Key features:

* Add bonds to Watchlist.
* Monitor current market price.
* Monitor YTM and effective discount rate.
* View FX-aware converted price.
* View backend-calculated risk level.
* View backend-calculated signal.
* Refresh Watchlist market data through AI-assisted public web research.
* Display source, last update, confidence, and review status.

---

### 🔎 Discover Bonds

The Discover Bonds section helps users find candidate bonds.

Supported discovery flows:

* CSV-based discovery/import.
* OpenAI-backed AI discovery.
* Structured JSON import.
* Candidate review before adding to Watchlist.
* Exclusion of bonds already existing in Portfolio or Watchlist.
* Candidate-level preview risk and signal.

---

### 🌍 FX Rates

* FX-aware Portfolio calculations.
* FX-aware Watchlist calculations.
* Base currency selection.
* Missing FX rate warnings.
* Central FX rate management.

---

### 🤖 AI-Assisted Market Research

The application supports AI-assisted research for:

* Bond discovery.
* Watchlist market refresh.
* Portfolio market refresh.
* Manual structured JSON import.

AI research is performed through the backend. The frontend never directly calls OpenAI.

---

## 🧰 Technology Stack

### Backend

| Technology            | Purpose                               |
| --------------------- | ------------------------------------- |
| Python                | Backend programming language          |
| Django                | Main backend framework                |
| Django REST Framework | API layer                             |
| PostgreSQL            | Relational database                   |
| Simple JWT            | Token-based authentication            |
| Django ORM            | Database models and queries           |
| Django Email Backend  | Email verification and password reset |
| OpenAI Responses API  | AI-assisted bond research             |
| Decimal               | Financial precision calculations      |

---

### Frontend

| Technology   | Purpose             |
| ------------ | ------------------- |
| React        | Frontend framework  |
| Vite         | Frontend build tool |
| React Router | Client-side routing |
| Axios        | API client          |
| CSS          | Styling             |
| LocalStorage | JWT token storage   |

---

### AI & Data

| Component              | Purpose                           |
| ---------------------- | --------------------------------- |
| OpenAI Responses API   | AI research and structured output |
| Web Search Tool        | Public web data research          |
| JSON Schema            | Structured AI response validation |
| Backend Import Service | Safe database import              |
| Source Metadata        | Transparency and review tracking  |

---

## 🏗 Application Architecture

```text
┌──────────────────────────────┐
│          React Frontend       │
│  Dashboard / Portfolio / UI   │
└───────────────┬──────────────┘
                │
                │ Axios + JWT
                ▼
┌──────────────────────────────┐
│       Django REST API         │
│ Auth / Bonds / Portfolio      │
└───────────────┬──────────────┘
                │
                │ Django ORM
                ▼
┌──────────────────────────────┐
│          PostgreSQL           │
│ Bonds / Market Data / Users   │
└───────────────┬──────────────┘
                │
                │ Backend-only AI calls
                ▼
┌──────────────────────────────┐
│       OpenAI Responses API    │
│  Web Search + Structured JSON │
└──────────────────────────────┘
```

---

## 🧩 Main Modules

```text
backend/
├── accounts/        # Signup, email verification, password reset, current user
├── analytics/       # Portfolio analytics, watchlist analytics, stress tests
├── bonds/           # Bond models, market data, FX rates, discovery, AI research
├── config/          # Django settings and root URLs
├── portfolios/      # User Portfolio and Watchlist models/views/serializers
└── manage.py

frontend/
├── src/api/         # Axios API functions
├── src/auth/        # Token and user storage helpers
├── src/components/  # Shared UI components
├── src/layouts/     # App layout and sidebar
├── src/pages/       # Dashboard, Portfolio, Watchlist, Auth pages
├── src/routes/      # Protected route logic
├── src/styles/      # Global styles
└── src/utils/       # Formatters and helpers
```

---

## 🤖 AI Research Workflow

### 1. AI Discovery

```text
User clicks Discover
→ Frontend sends filters to Django
→ Django builds strict AI prompt
→ OpenAI searches public web sources
→ OpenAI returns structured JSON
→ Django validates JSON
→ Django imports valid BondCandidate rows
→ User reviews candidates
→ User adds selected bond to Watchlist
```

---

### 2. Watchlist Market Refresh

```text
User clicks Update Prices in Watchlist
→ Django collects active Watchlist ISINs
→ OpenAI researches market data
→ Django validates structured JSON
→ Django creates/updates BondMarketData
→ Watchlist reloads
→ Risk/signal values refresh
```

---

### 3. Portfolio Market Refresh

```text
User clicks Update Prices in Portfolio
→ Django collects active Portfolio ISINs
→ OpenAI researches market data
→ Django validates structured JSON
→ Django creates/updates BondMarketData
→ Portfolio reloads
→ Portfolio value, risk, signal, stress test refresh
```

---

## 🧾 Market Data Transparency

AI-researched market data is **not** treated as an official live market feed.

Every AI-researched market record stores:

```text
source
source_url
retrieved_at
confidence
needs_review
review_status
missing_fields
research_payload
notes
```

This allows the user to see:

* Where the data came from.
* When it was retrieved.
* Whether the data needs review.
* Which fields were missing.
* Whether values were calculated or carried forward.
* Whether a public source was delayed, indicative, or incomplete.

---

## 🛡 AI Data Safety Rules

The AI research workflow follows strict rules:

* Do not invent ISINs.
* Do not invent prices.
* Do not invent yields.
* Do not invent ratings.
* Do not invent maturities.
* Do not invent source URLs.
* Missing values must remain `null`.
* Every item must include at least one source URL.
* AI-researched records are marked as `NEEDS_REVIEW`.
* Backend validates all AI output before database import.

---

## 📁 Project Structure

```text
bond-analysis-dashboard/
├── backend/
│   ├── accounts/
│   ├── analytics/
│   ├── bonds/
│   │   ├── ai_research/
│   │   ├── analytics/
│   │   ├── discovery/
│   │   └── ...
│   ├── config/
│   ├── portfolios/
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── components/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── routes/
│   │   ├── styles/
│   │   └── utils/
│   ├── package.json
│   └── vite.config.js
│
├── .gitignore
└── README.md
```

---

## ✅ Prerequisites

Before installing the app, make sure you have:

* Python 3.11+
* Node.js 18+
* npm
* PostgreSQL
* Git
* OpenAI API key
* Gmail App Password or SMTP credentials, if real email sending is required

---

# ⚙️ Installation Guide

The following instructions assume Windows PowerShell.

Default project path:

```powershell
C:\Users\xrist\Desktop\bond-analysis-dashboard
```

---

## 1. Clone the Repository

```powershell
cd C:\Users\xrist\Desktop

git clone https://github.com/XristosAndreopo/bond-analysis-dashboard.git

cd C:\Users\xrist\Desktop\bond-analysis-dashboard
```

---

## 2. Backend Setup

Go to the backend folder:

```powershell
cd C:\Users\xrist\Desktop\bond-analysis-dashboard\backend
```

Create virtual environment:

```powershell
python -m venv .venv
```

Activate virtual environment:

```powershell
.\.venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

---

## 3. PostgreSQL Setup

Open PostgreSQL shell:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres
```

Create database:

```sql
CREATE DATABASE bond_analysis_db;
```

Exit PostgreSQL:

```sql
\q
```

---

## 4. Backend Environment File

Create:

```text
backend/.env
```

You can copy the safe template from:

```text
backend/.env.example
```

Example:

```env
# ------------------------------------------------------------------
# Django core settings
# ------------------------------------------------------------------

DJANGO_SECRET_KEY=change-this-development-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# ------------------------------------------------------------------
# PostgreSQL database
# ------------------------------------------------------------------

POSTGRES_DB=bond_analysis_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-postgres-password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# ------------------------------------------------------------------
# CORS
# ------------------------------------------------------------------

CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# ------------------------------------------------------------------
# OpenAI API
# ------------------------------------------------------------------

OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-5.5
OPENAI_WEB_SEARCH_CONTEXT_SIZE=low
OPENAI_MAX_OUTPUT_TOKENS=8000
OPENAI_REASONING_EFFORT=low

# ------------------------------------------------------------------
# Email settings
# ------------------------------------------------------------------

DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password-without-spaces
DEFAULT_FROM_EMAIL=your-email@gmail.com

# ------------------------------------------------------------------
# Account security codes
# ------------------------------------------------------------------

ACCOUNT_SECURITY_CODE_EXPIRY_MINUTES=15
ACCOUNT_SECURITY_CODE_MAX_ATTEMPTS=5
```

---

## 5. Email Configuration

### Console Email for Development

Use this when you only want verification/reset codes to appear in the Django terminal:

```env
DJANGO_EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=no-reply@bond-analysis-dashboard.local
```

---

### Real Gmail SMTP

Use this when you want real email delivery:

```env
DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password-without-spaces
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

> For Gmail, use a Google App Password. Do not use your normal Gmail password.

---

## 6. Run Backend Migrations

```powershell
cd C:\Users\xrist\Desktop\bond-analysis-dashboard\backend

python manage.py makemigrations
python manage.py migrate
```

Create admin user:

```powershell
python manage.py createsuperuser
```

Run backend checks:

```powershell
python manage.py check
python -m compileall accounts bonds portfolios analytics
```

Start backend server:

```powershell
python manage.py runserver
```

Backend URL:

```text
http://127.0.0.1:8000
```

API base URL:

```text
http://127.0.0.1:8000/api
```

---

## 7. Frontend Setup

Open a second PowerShell window.

```powershell
cd C:\Users\xrist\Desktop\bond-analysis-dashboard\frontend
```

Install dependencies:

```powershell
npm install
```

Run build check:

```powershell
npm run build
```

Start frontend server:

```powershell
npm run dev
```

Frontend URL:

```text
http://localhost:5173
```

---

## 🌐 Main Frontend Routes

```text
/dashboard
/login
/signup
/verify-email
/forgot-password
/reset-password
/portfolio
/watchlist
/discover-bonds
/fx-rates
/positions/new
/positions/:positionId
```

---

## 🔌 Main API Routes

```text
/api/auth/token/
/api/auth/token/refresh/

/api/accounts/signup/
/api/accounts/verify-email/
/api/accounts/resend-verification-code/
/api/accounts/forgot-password/
/api/accounts/reset-password/
/api/accounts/me/

/api/dashboard/
/api/portfolio/
/api/watchlist/
/api/positions/<id>/

/api/ai-research/discover/
/api/ai-research/watchlist-market-refresh/
/api/ai-research/portfolio-market-refresh/
/api/ai-research/import-discovery/
/api/ai-research/import-market/

/api/discover-bonds/
/api/discover-bonds/run/
/api/discover-bonds/upload-csv/
/api/discover-bonds/provider-status/

/api/fx-rates/
/api/fx-rates/update/
```

---

## 🧪 Typical Test Flow

### Account Flow

```text
/signup
→ create account
→ receive verification code
→ /verify-email
→ verify account
→ /login
→ login successfully
```

---

### Forgot Password Flow

```text
/forgot-password
→ enter email
→ receive reset code
→ /reset-password
→ enter email, code, new password, confirm password
→ login with new password
```

---

### Watchlist Flow

```text
/watchlist
→ add or monitor bonds
→ Update Prices
→ review market price, YTM, risk, signal, source, confidence
```

---

### Portfolio Flow

```text
/portfolio
→ add owned bonds
→ Update Prices
→ review updated value, YTM, risk, signal, exposure, stress test
```

---

## 🧮 Financial Analytics

The backend calculates:

* Current yield.
* Yield to maturity when enough data exists.
* Modified duration.
* Risk score.
* Risk level.
* Final signal.
* Portfolio value.
* Weighted average YTM.
* Weighted current yield.
* Weighted modified duration.
* Currency exposure.
* Estimated coupon income.
* Interest rate stress test.

---

## 📉 Interest Rate Stress Test

The Portfolio includes an interest rate stress test based on modified duration.

It estimates how the Portfolio value may change under parallel interest rate shocks.

Current limitations:

* Does not include convexity.
* Does not include credit spread shocks.
* Does not include liquidity shocks.
* Does not include FX shocks.
* Uses available modified duration and current position value.

---

## 🧪 Useful Commands

Backend check:

```powershell
cd C:\Users\xrist\Desktop\bond-analysis-dashboard\backend

python manage.py check
python -m compileall accounts bonds portfolios analytics
```

Frontend build:

```powershell
cd C:\Users\xrist\Desktop\bond-analysis-dashboard\frontend

npm run build
```

Git status:

```powershell
cd C:\Users\xrist\Desktop\bond-analysis-dashboard

git status
```

Commit README:

```powershell
git add README.md
git commit -m "Add professional project README"
```

---

## 🔒 Security Notes

Never commit:

```text
backend/.env
frontend/.env
.env
API keys
SMTP passwords
Gmail App Passwords
PostgreSQL passwords
DJANGO_SECRET_KEY
```

Safe to commit:

```text
README.md
.gitignore
backend/.env.example
frontend/.env.example
```

If `.env` was staged accidentally:

```powershell
git rm --cached backend/.env
```

---

## 🚢 Production Checklist

Before production deployment:

* Set `DJANGO_DEBUG=False`.
* Use a strong production `DJANGO_SECRET_KEY`.
* Configure production `DJANGO_ALLOWED_HOSTS`.
* Use production PostgreSQL.
* Configure secure SMTP or transactional email provider.
* Use HTTPS.
* Review CORS settings.
* Protect OpenAI API key.
* Add logging.
* Add monitoring.
* Add rate limiting for AI endpoints.
* Add background jobs for long AI tasks.
* Add backup strategy.
* Review AI-imported records manually.

---

## ⚠️ Known Limitations

* AI-researched bond data is not an official live feed.
* Public bond market data may be delayed or incomplete.
* Some sources expose CUSIP instead of full ISIN.
* Bid/ask prices may not be publicly visible.
* Market required return may be unavailable.
* FX conversion depends on stored FX rates.
* Stress testing is simplified.
* The app does not provide investment advice.

---

## 🧭 Suggested Future Improvements

* Scheduled daily Portfolio refresh.
* Scheduled daily Watchlist refresh.
* Background task queue with Celery or Django-Q.
* User-level refresh limits.
* Manual review screen for AI-researched data.
* Historical market data charts.
* Export Portfolio to Excel.
* Export Watchlist to Excel.
* Advanced convexity analytics.
* Credit spread shock scenarios.
* Liquidity risk model.
* Docker setup.
* CI/CD pipeline.
* Production deployment guide.

---

## 📄 License

This project is currently intended for educational and personal use.

---

## 👤 Author

Developed by **Chris** for educational bond analysis, portfolio monitoring, and AI-assisted financial data research.
