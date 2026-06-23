\# Bond Analysis Dashboard



Bond Analysis Dashboard is a full-stack web application for monitoring, analyzing, and evaluating bonds in a personal Portfolio and Watchlist. The application is designed for educational and analytical purposes and does not provide investment advice or buy/sell recommendations.



The system allows users to create an account, verify their email, manage bonds, monitor market data, run backend-calculated financial analytics, refresh bond market data through AI-assisted public web research, and review risk/signal indications.



\---



\## Disclaimer



This application is for educational and analytical use only.



It does not provide financial, investment, legal, tax, or trading advice. Any buy/sell signals, risk indicators, yield calculations, price refreshes, or AI-researched market data must be reviewed manually before being used for any real-world investment decision.



AI-researched market data is not treated as an official live market feed. All AI-imported records keep transparency metadata such as source URL, retrieved timestamp, confidence level, review status, missing fields, and raw research payload.



\---



\## Main Features



\### Authentication and Account Security



\* User signup.

\* JWT-based login.

\* Email verification with temporary verification code.

\* Forgot password flow.

\* Password reset with temporary code.

\* Public dashboard preview for unauthenticated users.

\* Protected Portfolio, Watchlist, Discover Bonds, FX Rates, and Position pages.



\### Dashboard



\* Authenticated user dashboard.

\* Portfolio summary.

\* Bond count.

\* Portfolio value summary.

\* Risk and signal overview.

\* Public preview dashboard when the user is not logged in.



\### Portfolio



\* Add bonds to Portfolio.

\* Store user-specific bond positions.

\* Quantity and purchase price tracking.

\* Backend-calculated portfolio analytics.

\* FX-aware portfolio value conversion.

\* Weighted average YTM.

\* Weighted current yield.

\* Weighted modified duration.

\* Weighted risk score.

\* Currency exposure.

\* Estimated annual coupon income.

\* Interest rate stress test.

\* Per-bond risk and signal analysis.

\* AI-assisted market price refresh for Portfolio bonds.



\### Watchlist



\* Add bonds to Watchlist before buying.

\* Monitor bonds without owning them.

\* Backend-calculated Watchlist analytics.

\* FX-aware market price conversion.

\* Risk and signal analysis.

\* AI-assisted market price refresh for Watchlist bonds.

\* Source, last updated, confidence, and review status metadata.



\### Discover Bonds



\* Discovery page for finding bond candidates.

\* CSV-based discovery/import support.

\* OpenAI-backed AI discovery workflow.

\* AI-researched bond candidate import.

\* Candidate review before adding to Watchlist.

\* Existing Portfolio/Watchlist bonds are excluded from visible discovery candidates.



\### AI Market Research



The application supports AI-assisted public web research for:



\* Bond discovery.

\* Watchlist market data refresh.

\* Portfolio market data refresh.

\* Structured JSON import.

\* Source tracking.

\* Confidence tracking.

\* Review status tracking.

\* Missing field tracking.

\* Raw research payload storage.



Important AI research rules:



\* The AI must not invent values.

\* Missing values must remain null.

\* Every researched item must include at least one source URL.

\* AI-researched data is marked as needing review unless strongly verified.

\* The backend validates the structured JSON before importing it.

\* Market refresh data uses a stable internal source and daily quote date to avoid duplicate daily records.



\### FX Rates



\* Manual or central FX rate management.

\* FX-aware Portfolio and Watchlist calculations.

\* Base currency selection.

\* Missing FX warning handling.



\---



\## Technology Stack



\### Backend



\* Python

\* Django

\* Django REST Framework

\* PostgreSQL

\* Simple JWT authentication

\* Django email backend / SMTP email support

\* OpenAI Responses API for AI-assisted research

\* Django ORM

\* Decimal-based financial calculations

\* Django migrations



\### Frontend



\* React

\* Vite

\* React Router

\* Axios

\* CSS

\* Component-based UI structure



\### Database



\* PostgreSQL for local and production-ready development.

\* Django migrations for schema management.



\### AI Integration



\* OpenAI Responses API.

\* Web search tool integration.

\* Structured JSON schema validation.

\* Backend import validation before database write.



\### Email



\* Development option: Django console email backend.

\* Real email option: Gmail SMTP or another SMTP provider.

\* Gmail App Password is recommended when using Gmail SMTP.



\---



\## Project Structure



```text

bond-analysis-dashboard/

├── backend/

│   ├── accounts/

│   ├── analytics/

│   ├── bonds/

│   │   ├── ai\_research/

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



\---



\## Prerequisites



Before installing the application, make sure you have:



\* Python 3.11 or newer

\* Node.js 18 or newer

\* npm

\* PostgreSQL

\* Git

\* OpenAI API key

\* Gmail App Password or SMTP credentials, if real email sending is required



\---



\## Installation Guide



The following instructions assume Windows PowerShell and the project path:



```powershell

C:\\Users\\xrist\\Desktop\\bond-analysis-dashboard

```



\---



\## 1. Clone the Repository



```powershell

cd C:\\Users\\xrist\\Desktop



git clone https://github.com/XristosAndreopo/bond-analysis-dashboard.git



cd C:\\Users\\xrist\\Desktop\\bond-analysis-dashboard

```



\---



\## 2. Backend Setup



Go to the backend folder:



```powershell

cd C:\\Users\\xrist\\Desktop\\bond-analysis-dashboard\\backend

```



Create a virtual environment:



```powershell

python -m venv .venv

```



Activate it:



```powershell

.\\.venv\\Scripts\\activate

```



Install Python dependencies:



```powershell

pip install -r requirements.txt

```



\---



\## 3. PostgreSQL Database Setup



Open PostgreSQL shell:



```powershell

\& "C:\\Program Files\\PostgreSQL\\18\\bin\\psql.exe" -U postgres

```



Create the database:



```sql

CREATE DATABASE bond\_analysis\_db;

```



Exit PostgreSQL:



```sql

\\q

```



\---



\## 4. Backend Environment File



Create:



```text

backend/.env

```



You can copy from:



```text

backend/.env.example

```



Example `.env`:



```env

\# ------------------------------------------------------------------

\# Django core settings

\# ------------------------------------------------------------------



DJANGO\_SECRET\_KEY=change-this-development-secret-key

DJANGO\_DEBUG=True

DJANGO\_ALLOWED\_HOSTS=localhost,127.0.0.1



\# ------------------------------------------------------------------

\# PostgreSQL database

\# ------------------------------------------------------------------



POSTGRES\_DB=bond\_analysis\_db

POSTGRES\_USER=postgres

POSTGRES\_PASSWORD=your-postgres-password

POSTGRES\_HOST=localhost

POSTGRES\_PORT=5432



\# ------------------------------------------------------------------

\# CORS

\# ------------------------------------------------------------------



CORS\_ALLOWED\_ORIGINS=http://localhost:5173,http://127.0.0.1:5173



\# ------------------------------------------------------------------

\# OpenAI API

\# ------------------------------------------------------------------



OPENAI\_API\_KEY=your-openai-api-key

OPENAI\_MODEL=gpt-5.5

OPENAI\_WEB\_SEARCH\_CONTEXT\_SIZE=low

OPENAI\_MAX\_OUTPUT\_TOKENS=8000

OPENAI\_REASONING\_EFFORT=low



\# ------------------------------------------------------------------

\# Email settings

\# ------------------------------------------------------------------



DJANGO\_EMAIL\_BACKEND=django.core.mail.backends.smtp.EmailBackend

EMAIL\_HOST=smtp.gmail.com

EMAIL\_PORT=587

EMAIL\_USE\_TLS=True

EMAIL\_USE\_SSL=False

EMAIL\_HOST\_USER=your-email@gmail.com

EMAIL\_HOST\_PASSWORD=your-gmail-app-password-without-spaces

DEFAULT\_FROM\_EMAIL=your-email@gmail.com



\# ------------------------------------------------------------------

\# Account security codes

\# ------------------------------------------------------------------



ACCOUNT\_SECURITY\_CODE\_EXPIRY\_MINUTES=15

ACCOUNT\_SECURITY\_CODE\_MAX\_ATTEMPTS=5

```



Important:



Do not commit `backend/.env`.



Use `backend/.env.example` for safe placeholder values.



\---



\## 5. Email Configuration



\### Development Email Option



For local testing without sending real emails:



```env

DJANGO\_EMAIL\_BACKEND=django.core.mail.backends.console.EmailBackend

DEFAULT\_FROM\_EMAIL=no-reply@bond-analysis-dashboard.local

```



With this option, verification and reset codes appear in the Django terminal.



\### Real Gmail SMTP Option



For real emails:



```env

DJANGO\_EMAIL\_BACKEND=django.core.mail.backends.smtp.EmailBackend

EMAIL\_HOST=smtp.gmail.com

EMAIL\_PORT=587

EMAIL\_USE\_TLS=True

EMAIL\_USE\_SSL=False

EMAIL\_HOST\_USER=your-email@gmail.com

EMAIL\_HOST\_PASSWORD=your-gmail-app-password-without-spaces

DEFAULT\_FROM\_EMAIL=your-email@gmail.com

```



For Gmail, use a Google App Password, not the normal Gmail password.



\---



\## 6. Run Backend Migrations



From the backend folder:



```powershell

cd C:\\Users\\xrist\\Desktop\\bond-analysis-dashboard\\backend



python manage.py makemigrations

python manage.py migrate

```



Create an admin user:



```powershell

python manage.py createsuperuser

```



Run backend checks:



```powershell

python manage.py check

python -m compileall accounts bonds portfolios analytics

```



Start the backend server:



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



\---



\## 7. Frontend Setup



Open a second PowerShell window.



Go to the frontend folder:



```powershell

cd C:\\Users\\xrist\\Desktop\\bond-analysis-dashboard\\frontend

```



Install dependencies:



```powershell

npm install

```



Run build check:



```powershell

npm run build

```



Start the frontend development server:



```powershell

npm run dev

```



Frontend URL:



```text

http://localhost:5173

```



\---



\## 8. Main Application URLs



Frontend routes:



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



Backend API routes include:



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



\---



\## 9. Typical User Flow



\### Account Flow



```text

/signup

→ user creates account

→ verification code is sent by email

→ /verify-email

→ user verifies account

→ /login

→ user logs in

```



\### Forgot Password Flow



```text

/forgot-password

→ user enters email

→ reset code is sent by email

→ /reset-password

→ user enters email, code, new password and confirmation

→ /login

```



\### Portfolio Flow



```text

/portfolio

→ add bond to Portfolio

→ update market prices

→ review portfolio analytics

→ review risk/signal indications

→ review stress test

```



\### Watchlist Flow



```text

/watchlist

→ add bond to Watchlist

→ update market prices

→ review market data and risk/signal indications

→ move bond to Portfolio if needed

```



\### Discovery Flow



```text

/discover-bonds

→ run AI discovery or CSV discovery

→ review candidate bonds

→ add selected bond to Watchlist

```



\---



\## 10. AI Market Refresh Behavior



The application supports AI-assisted market refresh for:



```text

Watchlist

Portfolio

```



Market refresh behavior:



\* The backend collects active ISINs from the authenticated user's Portfolio or Watchlist.

\* The backend sends a structured market research request to OpenAI.

\* OpenAI uses public web search.

\* The response must follow the backend JSON schema.

\* The backend validates and imports the result.

\* New `BondMarketData` records are created or existing daily AI records are updated.

\* The frontend reloads the Portfolio or Watchlist page.



To avoid duplicate daily records, AI market refresh records use:



```text

source = ai\_research\_agent

quote\_date = current local date

```



The original AI-reported source name and quote date are preserved inside:



```text

research\_payload

source\_url

notes

```



\---



\## 11. Market Data Transparency



Every AI-researched market record stores:



```text

source

source\_url

retrieved\_at

confidence

needs\_review

review\_status

missing\_fields

research\_payload

notes

```



This is important because public bond data may be:



\* Delayed

\* Indicative

\* Broker-provided

\* Based on public snippets

\* Missing bid/ask

\* Missing YTM

\* Missing quote timestamp

\* Not an executable live institutional quote



\---



\## 12. Running Tests and Checks



Backend checks:



```powershell

cd C:\\Users\\xrist\\Desktop\\bond-analysis-dashboard\\backend



python manage.py check

python -m compileall accounts bonds portfolios analytics

```



Frontend build:



```powershell

cd C:\\Users\\xrist\\Desktop\\bond-analysis-dashboard\\frontend



npm run build

```



Git status:



```powershell

cd C:\\Users\\xrist\\Desktop\\bond-analysis-dashboard



git status

```



\---



\## 13. Git Workflow



Before committing, always check that `.env` is not staged:



```powershell

git status

```



If `backend/.env` appears as tracked or staged, remove it from Git index without deleting the local file:



```powershell

git rm --cached backend/.env

```



Typical commit commands:



```powershell

git add .

git commit -m "Add project README documentation"

```



Push:



```powershell

git push

```



\---



\## 14. Security Notes



Do not commit:



```text

backend/.env

frontend/.env

.env

API keys

SMTP passwords

Gmail App Passwords

PostgreSQL passwords

```



Safe files to commit:



```text

backend/.env.example

frontend/.env.example

README.md

.gitignore

```



\---



\## 15. Production Notes



Before production deployment:



\* Set `DJANGO\_DEBUG=False`.

\* Use a strong `DJANGO\_SECRET\_KEY`.

\* Configure real production `DJANGO\_ALLOWED\_HOSTS`.

\* Use a production PostgreSQL database.

\* Use a secure SMTP provider or transactional email provider.

\* Use HTTPS.

\* Review CORS settings.

\* Protect OpenAI API key.

\* Add logging and monitoring.

\* Add background job processing for long AI research tasks.

\* Add rate limiting for AI endpoints.

\* Add production static file handling.

\* Review all AI-imported data manually before relying on it.



\---



\## 16. Known Limitations



\* AI-researched bond data is not an official live feed.

\* Public bond market data can be incomplete or delayed.

\* Some public sources provide CUSIP instead of full ISIN.

\* Bid/ask prices may not be available from public sources.

\* Market required return may be unavailable.

\* FX conversion depends on available FX rates in the application.

\* Stress test uses modified duration and does not include convexity, credit spread shocks, liquidity shocks, or FX shocks.

\* The app does not provide investment advice.



\---



\## 17. Suggested Future Improvements



\* Background jobs for AI market refresh.

\* Scheduled daily refresh for Portfolio and Watchlist.

\* User-level refresh limits.

\* Better source ranking for market data.

\* Manual review/approval workflow for AI market records.

\* Export Portfolio and Watchlist to Excel.

\* More advanced stress testing.

\* Convexity calculations.

\* Credit spread shock scenarios.

\* Historical market data charts.

\* Deployment with Docker.

\* Production-ready CI/CD pipeline.



\---



\## License



This project is currently for educational and personal use.



\---



\## Author



Developed by Chris for educational bond analysis, portfolio monitoring, and AI-assisted financial data research.



