# 🚀 Quick Setup Guide for Recruiters

**Estimated Time: 5 minutes**

This guide helps you run the Aura Knowledge Pipeline demo on your Windows PC with minimal setup.

---

## Option 1: One-Click Setup (Recommended)

### Prerequisites
- **Python 3.10+** installed ([Download here](https://www.python.org/downloads/))
  - ⚠️ During installation, **check "Add Python to PATH"**

### Steps

1. **Double-click `run_demo.bat`** in the project folder

That's it! The script will:
- ✅ Clean up any previous database files
- ✅ Create a virtual environment
- ✅ Install all dependencies
- ✅ Generate mock data
- ✅ Start the API server
- ✅ Run the full pipeline
- ✅ Execute demo queries showing Aura's safety features

### Expected Output

You'll see output demonstrating 4 scenarios:
1. **Safe Query** - High-quality data, confident recommendation
2. **Shadow Stock Warning** - Detected inventory discrepancy
3. **Low Reliability** - Data too unreliable for autonomous action
4. **Stale Data** - Data too old, needs refresh

---

## Option 2: Manual Setup

If you prefer step-by-step control:

### Step 1: Open Command Prompt
Press `Win + R`, type `cmd`, press Enter.

### Step 2: Navigate to Project
```cmd
cd path\to\agentic-knowledge-engineering-data-pipeline
```

### Step 3: Create Virtual Environment
```cmd
python -m venv venv
venv\Scripts\activate
```

### Step 4: Install Dependencies
```cmd
pip install -r requirements.txt
```

### Step 5: Initialize Project
```cmd
python scripts/setup_project.py
```

This will also **generate the mock warehouse CSV** at:
`data\raw\warehouse_stock.csv`

### Step 6: Start API Server
Open a **new** Command Prompt window:
```cmd
cd path\to\agentic-knowledge-engineering-data-pipeline
venv\Scripts\activate
uvicorn mock_apis.main:app --port 8000
```
Keep this window open.

### Step 7: Run Pipeline
Back in the original window:
```cmd
python scripts/run_pipeline.py
```

### Step 8: Run Demo
```cmd
python scripts/demo_aura_queries.py
```

---

## What You're Seeing

### The Demo Demonstrates:

| Scenario | What Happens | Agent Response |
|----------|--------------|----------------|
| **Scenario 1: Normal Query (P001)** | On-shelf + in-transit inventory, no conflicts | 🟢 **SAFE** - Shows confidence + recommendation |
| **Scenario 2: Shadow Stock (P003)** | Logistics shows **delivered** but warehouse count is older | 🟡 **WARNING** - Manual verification recommended |
| **Scenario 3: Low Stock (P004)** | Very low on-shelf stock | 🟢 **SAFE** - **Urgent** reorder recommendation (no data issues) |
| **Scenario 4: Out of Stock (P005)** | Zero on-shelf inventory | 🟢 **SAFE** - **Urgent** reorder recommendation |

You’ll also see:
- **Inventory Summary** (parts tracked, total units, average reliability, warnings, urgent reorders)
- **Parts Requiring Attention**
  - Parts with data warnings (e.g., shadow stock)
  - Parts needing reorder (sorted by lowest stock)

### Key Innovation:
The pipeline doesn't just move data—it creates **trustworthy knowledge** with:
- Reliability scores (how much to trust each source)
- Conflict detection (when sources disagree)
- Safety guardrails (preventing bad autonomous decisions)

---

## Troubleshooting

### "Python is not recognized"
- Reinstall Python from [python.org](https://www.python.org/downloads/)
- **Check "Add Python to PATH"** during installation
- Restart Command Prompt after installation

### "Port 8000 already in use"
```cmd
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F
```
Then run the demo again.

### "ModuleNotFoundError"
Make sure virtual environment is activated:
```cmd
venv\Scripts\activate
```
Then reinstall:
```cmd
pip install -r requirements.txt
```

### "DuckDB file locked"
Close any other programs that might be using the database, or delete:
```cmd
del data\processed\aura.duckdb
```
Then run the demo again.

---

## Clean Restart

To start completely fresh:
```cmd
del data\processed\aura.duckdb
del aura_bronze.duckdb
python scripts/setup_project.py
```

Or simply run `run_demo.bat` again—it cleans up automatically.

---

## Questions?

**Author:** Seward Mupereri  
**Email:** sewardrichardmupereri@gmail.com

Feel free to reach out with any questions about the implementation!
