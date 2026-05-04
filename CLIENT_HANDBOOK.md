# Cardio Disease Network — Client Handbook

A practical, end-to-end guide for setting up, running, and using the **Cardio Disease Network** clinical decision support tool.

---

## 1. Project Overview

**Cardio Disease Network** is a Bayesian Network (BN) clinical decision support tool for cardiovascular risk assessment. It combines:

- A **deterministic Bayesian Network** (built with `pgmpy`, trained on the UCI heart disease dataset) that produces an explainable, mathematically grounded probability of heart disease from patient evidence.
- An **AI explanation layer** (Google Gemini) that translates the BN's mathematical output into clinician-readable narrative, supports interactive "what-if" treatment simulations, and acts as an independent clinical reviewer.
- A **React dashboard** that orchestrates patient input, displays the Bayesian Network, factor breakdown, verification metrics, and exports a PDF clinical report.

The system is delivered as two services:

| Service          | Stack                                    | Port |
|------------------|------------------------------------------|------|
| `backend-bayesian` | Python 3.11, FastAPI, pgmpy, Gemini SDK | 8000 |
| `frontend-ui`      | Node 18, React 19, React Flow, Recharts | 3000 |

---

## 2. Prerequisites

Install the following before you start:

| Tool             | Recommended version | Notes                                                |
|------------------|---------------------|------------------------------------------------------|
| **IntelliJ IDEA**| 2023.2+ (Ultimate)  | Required for the bundled Python + JavaScript modules |
| **Docker Desktop** | 4.x+              | Used by the recommended Docker Compose workflow      |
| **Python**       | 3.11 or newer       | Matches `backend-bayesian/Dockerfile` (`python:3.11-slim`) |
| **Node.js**      | 18 LTS or newer     | Matches `frontend-ui/Dockerfile` (`node:18-alpine`)  |
| **Git**          | 2.30+               | For cloning the repository                            |

A **Google Gemini API key** is required for AI-powered endpoints (`/ask-ai`, `/chat-ai`, `/ask-ai-general`). Optionally, a **PostgreSQL** database is needed for the `/save-record` endpoint.

---

## 3. Cloning the Repository

```bash
git clone https://github.com/JorjitDasoria/cardio-disease-network.git
cd cardio-disease-network
```

The repository contains two top-level modules — `backend-bayesian/` and `frontend-ui/` — plus a root `docker-compose.yml`.

---

## 4. IntelliJ IDEA Setup

### 4.1 Open the project

1. Launch **IntelliJ IDEA**.
2. Choose **File → Open…** and select the cloned `cardio-disease-network` directory.
3. IntelliJ will detect the existing `.idea/` configuration and the multi-module layout (`cardio-disease-network`, `backend-bayesian`, `frontend-ui`).

### 4.2 Recommended plugins

Install (or verify enabled) the following IntelliJ plugins via **Settings → Plugins**:

- **Python** (required for `backend-bayesian`)
- **Node.js** (required for `frontend-ui`)
- **Docker** (recommended, for managing Compose services from the IDE)
- **Database Tools and SQL** (recommended, to inspect SQLite/Postgres records)

Restart IntelliJ when prompted.

### 4.3 Configure the Python interpreter for `backend-bayesian`

1. Go to **File → Project Structure → Modules → backend-bayesian**.
2. Select the **Python** SDK and click **Add Interpreter → Add Local Interpreter…**.
3. Choose **Virtualenv Environment → New environment**.
   - **Base interpreter**: Python 3.11+
   - **Location**: `cardio-disease-network/backend-bayesian/.venv`
4. Click **OK** and wait for indexing.
5. Open the IntelliJ terminal and install backend dependencies:

   ```bash
   cd backend-bayesian
   pip install -r requirements.txt
   ```

### 4.4 Configure Node.js for `frontend-ui`

1. Go to **Settings → Languages & Frameworks → Node.js**.
2. Set **Node interpreter** to your local Node 18+ install.
3. Set **Package manager** to `npm`.
4. From the IntelliJ terminal, install frontend dependencies:

   ```bash
   cd frontend-ui
   npm install
   ```

---

## 5. Environment Variables

The application reads configuration from two `.env` files — one per module.

### 5.1 `backend-bayesian/.env`

Create `backend-bayesian/.env` with the following keys:

```env
# Google Gemini API key — required for /ask-ai, /chat-ai, /ask-ai-general
GEMINI_API_KEY=your-gemini-api-key-here

# PostgreSQL connection string — required for /save-record and /global-stats
# Example: postgresql://user:password@localhost:5432/cardio
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

These variables are loaded by `python-dotenv` in `backend-bayesian/src/main.py` and are also injected by Docker Compose via `env_file`.

> If `DATABASE_URL` is not set, the backend will start but log `Warning: No DATABASE_URL found.` and the record-saving / global-stats endpoints will not function.

### 5.2 `frontend-ui/.env`

The repository ships with a default `frontend-ui/.env`:

```env
REACT_APP_API_URL=http://127.0.0.1:8000
```

Change `REACT_APP_API_URL` if the backend is hosted elsewhere (e.g. behind a reverse proxy or on another machine). Create React App requires the `REACT_APP_` prefix for variables to be exposed to the browser.

> **Never commit real API keys.** Both `.env` files should be added to `.gitignore` once they contain real credentials.

---

## 6. Three Ways to Run the Application

### 6.1 Option A — Docker Compose (recommended)

From the repository root:

```bash
docker compose up --build
```

This builds both images and starts:

- `cardio_backend` on `http://localhost:8000`
- `cardio_frontend` on `http://localhost:3000`

The compose file mounts the source directories as volumes, so code changes hot-reload in both services. To stop:

```bash
docker compose down
```

### 6.2 Option B — Two manual terminals

**Terminal 1 — backend:**

```bash
cd backend-bayesian
pip install -r requirements.txt
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — frontend:**

```bash
cd frontend-ui
npm install
npm start
```

The React dev server opens `http://localhost:3000` automatically and proxies API calls to `REACT_APP_API_URL`.

### 6.3 Option C — IntelliJ Run Configurations

Create two run configurations under **Run → Edit Configurations…**:

1. **Backend (FastAPI / uvicorn)** — *Python* configuration
   - **Module**: `uvicorn`
   - **Parameters**: `src.main:app --host 0.0.0.0 --port 8000 --reload`
   - **Working directory**: `cardio-disease-network/backend-bayesian`
   - **Python interpreter**: the `backend-bayesian` venv from §4.3

2. **Frontend (React)** — *npm* configuration
   - **package.json**: `cardio-disease-network/frontend-ui/package.json`
   - **Command**: `start`
   - **Scripts**: `start`

Optionally add a third **Docker → Docker Compose** configuration pointing at `docker-compose.yml` to start everything with one click.

---

## 7. Login Credentials

The login screen uses simple hardcoded credentials for demo purposes:

| Field    | Value      |
|----------|------------|
| Username | `admin`    |
| Password | `password` |

> These credentials are defined in `frontend-ui/src/Login.js` and are intended for local development only. Replace them with a real authentication mechanism before any production deployment.

---

## 8. Application Usage Guide

After logging in, the dashboard is laid out as follows.

### 8.1 Patient data input

On the left-hand panel of the **Risk Calculator** page:

1. Enter the **patient name**.
2. Fill in the clinical evidence fields (age, sex, chest-pain type, resting BP, cholesterol, fasting blood sugar, resting ECG, max heart rate, exercise-induced angina, oldpeak ST depression, ST slope, number of major vessels, thalassemia).
3. Optionally pre-set treatment options (statin intensity, BP medication regimen, PCI). Treatments adjust the BN's base probability by published heuristics.

### 8.2 Analyze & save

- Click **Analyze** to call `POST /predict`. The dashboard displays:
  - Final disease probability (post-treatment) and risk level (`High` / `Low`).
  - Factor breakdown (Naive Bayes log-odds) categorising each feature as **Danger** or **Protective**.
  - The Bayesian Network visualisation (React Flow) with per-node probability colouring.
  - The Verification Panel showing accuracy / sensitivity / specificity for the current clinical scenario.
- Click **Save Record** to persist a snapshot of `{ patient_name, bn_score, ai_score }` via `POST /save-record`.

### 8.3 AI chat

- The AI panel calls `POST /ask-ai` for the initial grounded explanation, then `POST /chat-ai` for follow-up questions.
- The chat supports tool-calling: ask "what if we add high-intensity statins?" and the AI invokes `simulate_treatment` to recompute the probability dynamically.
- Use **Independent Clinical Reviewer** mode (`POST /ask-ai-general`) to ignore the BN math and get a contradiction check.

### 8.4 PDF export

- Click **Export PDF**. The frontend uses `html2canvas` to snapshot the dashboard (BN graph, factor breakdown, verification metrics, AI summary) and `jspdf` to assemble a multi-page clinical report named after the patient.

---

## 9. API Endpoints

All endpoints are served by `backend-bayesian` on port `8000`.

| Method | Path                  | Purpose                                                                 |
|--------|-----------------------|-------------------------------------------------------------------------|
| GET    | `/`                   | Health check — returns `{"status": "Bayesian Backend is running"}`.     |
| GET    | `/network-structure`  | Returns the BN's edge list / node list for graph rendering.             |
| GET    | `/advanced-network`   | Returns full network data (structure + per-node CPT probabilities).     |
| POST   | `/verify`             | Returns dynamic verification metrics (accuracy, sensitivity, specificity, clinical scenario probability) for the supplied evidence and treatments. |
| POST   | `/predict`            | Core inference. Returns `base_probability`, `disease_probability`, `risk_level`, `factor_breakdown`. |
| POST   | `/ask-ai`             | Grounded Gemini explanation tied to the BN's mathematical breakdown.    |
| POST   | `/chat-ai`            | Multi-turn AI chat; supports `simulate_treatment` tool-calling.         |
| POST   | `/ask-ai-general`     | Independent clinical reviewer mode (ignores BN math).                   |
| POST   | `/save-record`        | Persists `{patient_name, bn_score, ai_score}` to PostgreSQL.            |
| GET    | `/global-stats`       | Aggregate statistics across all saved records.                          |

Request bodies for `POST` endpoints follow the `PredictionRequest` / `ChatRequest` / `SaveRecordRequest` Pydantic models defined in `backend-bayesian/src/main.py`.

---

## 10. Project Directory Structure

```
cardio-disease-network/
├── docker-compose.yml                  # Two-service Compose stack
├── cardio-disease-network.iml          # IntelliJ project module
├── .gitattributes
├── .gitignore
├── .idea/                              # IntelliJ project settings (shared)
│
├── backend-bayesian/                   # Python / FastAPI service
│   ├── Dockerfile                      # python:3.11-slim image
│   ├── .dockerignore
│   ├── requirements.txt                # fastapi, uvicorn, pgmpy, google-genai, …
│   ├── patient_records.db              # Local SQLite (development convenience)
│   ├── backend-bayesian.iml
│   └── src/
│       ├── main.py                     # FastAPI app, endpoints, AI tool-calling
│       ├── model_logic.py              # CardioBayesianModel, training, inference
│       ├── export_cpts.py              # Utility to dump CPTs for audit
│       ├── test_correlation.py         # Correlation diagnostics
│       ├── heart_disease_dataset.csv   # UCI training data (303 records)
│       ├── saved_model.pkl             # Trained BN snapshot
│       └── Model_CPTs_For_Client_Review.txt
│
└── frontend-ui/                        # React 19 dashboard
    ├── Dockerfile                      # node:18-alpine image
    ├── .dockerignore
    ├── .env                            # REACT_APP_API_URL
    ├── package.json
    ├── package-lock.json
    ├── README.md                       # CRA boilerplate notes
    ├── frontend-ui.iml
    ├── public/
    │   ├── index.html
    │   ├── manifest.json
    │   ├── robots.txt
    │   ├── Health.jpg
    │   └── logo192.png / logo512.png
    └── src/
        ├── index.js                    # React entrypoint
        ├── App.js / App.css            # Application shell
        ├── Login.js                    # Login screen (admin/password)
        ├── RiskCalculator.jsx          # Main dashboard
        ├── BayesianNetwork.jsx         # React Flow BN visualisation
        ├── ProbabilityNode.jsx         # Custom React Flow node
        ├── VerificationPanel.jsx       # Accuracy / sensitivity / specificity
        ├── graph_static.png            # Fallback static graph image
        ├── App.test.js / setupTests.js # Test scaffolding
        └── reportWebVitals.js
```

---

## 11. Troubleshooting

| Symptom                                                                 | Likely cause                                                            | Fix                                                                                                         |
|-------------------------------------------------------------------------|-------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| `Warning: No DATABASE_URL found.` on backend startup                    | `backend-bayesian/.env` is missing or `DATABASE_URL` is unset           | Create the `.env` file with a valid `DATABASE_URL`; restart the backend.                                    |
| `/ask-ai` or `/chat-ai` returns 500                                     | `GEMINI_API_KEY` invalid or unset                                       | Verify the key in `backend-bayesian/.env`; restart the backend; confirm quota in Google AI Studio.          |
| Frontend shows "Network Error" / CORS error                             | Backend not running or `REACT_APP_API_URL` mismatched                   | Start backend on `:8000`; confirm `frontend-ui/.env` matches; restart the React dev server (env vars are read once). |
| `pip install -r requirements.txt` fails on `pgmpy` / `psycopg2-binary`  | Python version mismatch or missing system build tools                   | Use Python 3.11+; on Linux install `build-essential` and `libpq-dev`; on Windows use Docker Compose instead.|
| React hot reload doesn't pick up changes inside Docker on Windows       | File-system events not propagated into the container                    | Already mitigated by `CHOKIDAR_USEPOLLING=true` in `docker-compose.yml`; rebuild with `docker compose up --build`. |
| `docker compose up` errors with "port already in use" on 3000 or 8000   | Another process is bound to the port                                    | Stop the other process or change the host port mapping in `docker-compose.yml`.                             |
| Login keeps failing                                                     | Wrong credentials                                                       | Use `admin` / `password` exactly as shown in §7 (case-sensitive).                                           |
| BN graph renders but all probabilities are 0.5 / blank                  | Model failed to train at startup                                        | Check backend logs for `Failed to start model:`; verify `heart_disease_dataset.csv` exists in `backend-bayesian/src/`. |
| PDF export is blank or cuts off                                         | Browser blocked `html2canvas` or content was off-screen                 | Scroll the dashboard fully into view, allow pop-ups, retry. Try a different browser (Chrome/Firefox).        |
| Records are not saved despite clicking **Save Record**                  | PostgreSQL not reachable from the backend                               | Check that the database in `DATABASE_URL` exists; ensure the `records` table was created on startup.        |

---

*For deeper architectural detail, see `backend-bayesian/src/model_logic.py` (Bayesian Network construction, discretization, Variable Elimination inference) and `frontend-ui/src/RiskCalculator.jsx` (dashboard orchestration, AI chat, PDF export).*
