# India CS Research

A research analytics platform for analyzing Computer Science research output of Indian institutes. Built with React + Flask + PostgreSQL.

## Project Overview

- **Frontend**: React + Vite (displays rankings and research metrics)
- **Backend**: Flask + SQLAlchemy (REST API serving data)
- **Database**: PostgreSQL (stores faculty rankings, paper counts, research domains)
- **Data Pipeline**: Python scripts to fetch from DBLP and compute research metrics

## Prerequisites

### Required
- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **PostgreSQL 12+** - [Download](https://www.postgresql.org/download/)

### Optional
- **Git** - for version control and collaboration

## Setup Instructions

### 1. Clone the repository (for team collaboration)
```bash
git clone <your-repo-url>
cd BTP
```

### 2. Backend Setup

#### 2a. Install Python dependencies
```bash
cd backend
pip install SQLAlchemy psycopg2-binary python-dotenv Flask Flask-CORS requests pandas
```

#### 2b. Create environment file
Copy `.env.example` to `.env` and fill in your PostgreSQL connection:
```bash
cp .env.example .env
```

Edit `backend/.env`:
```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/btp
```

**Note**: Replace `your_password` with your PostgreSQL password.

#### 2c. Create PostgreSQL database
Open PostgreSQL (pgAdmin or command line):
```sql
CREATE DATABASE btp;
```

#### 2d. Initialize database tables
From `backend/` directory:
```bash
python init_db.py
```

Output should show: `✅ Database tables created`

#### 2e. Load data into PostgreSQL
```bash
python load_data.py
```

Output should show: `✅ Loaded data into PostgreSQL`

#### 2f. Start the Flask backend
```bash
python api/app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

### 3. Frontend Setup

Open a **new terminal** and navigate to the project root:

#### 3a. Install Node dependencies
```bash
npm install
```

#### 3b. Start the development server
```bash
npm run dev
```

You should see:
```
Local:        http://localhost:5173/
```

### 4. Access the application
Open your browser and go to: `http://localhost:5173/`

You should see the India CS Rankings homepage with real data from PostgreSQL!

---

## How to Run Everything (Quick Reference)

### Terminal 1 - Backend
```bash
cd backend
python api/app.py
```

### Terminal 2 - Frontend
```bash
npm run dev
```

Both terminals need to be running simultaneously.

---

## Available API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /iiitd` | Get faculty rankings (name, papers, score) |
| `GET /iiitd/domains` | Get detailed domains, venues, and research areas |

---

## Data Pipeline (Optional)

To refresh research data from DBLP:

```bash
cd backend/scripts
python run_pipeline.py
```

Then reload the data:
```bash
cd backend
python load_data.py
```

---

## Project Structure

```
BTP/
├── backend/
│   ├── api/
│   │   └── app.py           # Flask API endpoints
│   ├── scripts/
│   │   ├── run_pipeline.py
│   │   ├── fetch_dblp.py
│   │   ├── extract_domains.py
│   │   └── ...
│   ├── data/
│   │   ├── processed/       # Generated JSON files
│   │   └── raw/             # Raw CSV files
│   ├── db.py                # SQLAlchemy engine
│   ├── models.py            # Database models
│   ├── init_db.py           # Create tables
│   ├── load_data.py         # Load JSON into DB
│   └── .env                 # Environment config (NOT in git)
├── src/
│   ├── pages/
│   │   ├── HomePage.jsx
│   │   ├── InstitutePage.jsx
│   │   └── ComparePage.jsx
│   ├── components/
│   └── App.jsx
├── package.json
└── README.md
```

---

## Collaboration Workflow

### For team development:
1. Each developer creates a branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make changes and test locally
3. Push to your branch
4. Create a Pull Request
5. Get code review and merge

### Important Notes:
- **Never commit `.env`** - it contains passwords
- **Never commit `node_modules/`** or `backend/__pycache__/`
- Always pull before starting work: `git pull origin main`

---

## Troubleshooting

### "Database connection refused"
- Check PostgreSQL is running
- Verify `DATABASE_URL` in `backend/.env` is correct
- Make sure database `btp` exists

### "Module not found: psycopg2"
```bash
pip install psycopg2-binary
```

### "No such file or directory: iiitd_domains.json"
- Run `python init_db.py` and `python load_data.py` from the `backend/` directory
- Check the file exists at `backend/data/processed/iiitd_domains.json`

### Frontend not loading data
- Make sure Flask backend is running on port 5000
- Check browser console for CORS errors
- Verify the database has data: `python load_data.py`

---

## Next Steps

- [ ] Run backend and frontend locally
- [ ] Explore the research rankings UI
- [ ] Add filters/search on the homepage
- [ ] Create comparison pages for different institutions
- [ ] Deploy to production

---

## Questions or Issues?

Check the Flask/React logs in the terminal for error messages. For PostgreSQL issues, refer to the [PostgreSQL docs](https://www.postgresql.org/docs/).
