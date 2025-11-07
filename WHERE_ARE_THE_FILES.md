# Where Are The Files? - Quick Reference Guide

## 📁 Project Structure

```
LCR_Civil_Automations/
├── backend/                      # Python FastAPI Backend
│   ├── api/
│   │   ├── main.py              # Main FastAPI app ⭐
│   │   └── routes/              # API endpoint routes
│   │       ├── area_calculation.py
│   │       ├── spec_extraction.py  # ⭐ NEW: Web scraping endpoint
│   │       ├── dia_report.py
│   │       ├── qa_review.py
│   │       └── proposals.py
│   ├── services/                # Business logic
│   │   ├── module_a/            # Area Calculation
│   │   ├── module_b/            # Spec Extraction
│   │   │   ├── pdf_parser.py
│   │   │   ├── spec_extractor.py
│   │   │   ├── noaa_parser.py
│   │   │   └── web_scraper.py   # ⭐ NEW: Web scraping module
│   │   ├── module_c/            # DIA Report Generator
│   │   ├── module_d/            # Plan Review QA
│   │   └── module_e/            # Proposal Generator
│   ├── models/                  # Database models
│   ├── core/                    # Core utilities & settings
│   └── requirements.txt         # Python dependencies
│
├── frontend/                    # Next.js 14+ Frontend
│   ├── app/                     # Next.js App Router pages
│   │   ├── page.tsx            # Homepage
│   │   ├── module-a/page.tsx   # Module A UI
│   │   ├── module-b/page.tsx   # ⭐ NEW: Web scraping + specs viewer
│   │   ├── module-c/page.tsx   # Module C UI
│   │   ├── module-d/page.tsx   # Module D UI
│   │   └── module-e/page.tsx   # Module E UI
│   ├── components/ui/           # Reusable UI components
│   ├── lib/
│   │   └── api-client.ts       # ⭐ NEW: Web scraping API client
│   └── package.json
│
├── database/                    # Database initialization
│   └── init/                    # SQL initialization scripts
│
├── docker-compose.yml           # Docker setup for all services ⭐
├── .env.example                 # Environment variables template
│
├── README.md                    # Main project documentation
├── DEMO_GUIDE.md               # Original demo guide
├── TESTING_AND_DEMO_GUIDE.md   # ⭐ NEW: Complete testing guide
└── WHERE_ARE_THE_FILES.md      # ⭐ This file!
```

---

## 🔑 Key Files for Testing

### 1. Web Scraping (NEW!)

**Backend:**
- `/backend/services/module_b/web_scraper.py` - Web scraper implementation
- `/backend/api/routes/spec_extraction.py:413` - API endpoint

**Frontend:**
- `/frontend/app/module-b/page.tsx:83` - Web scraping UI component
- `/frontend/lib/api-client.ts:151` - API client method

**How to Test:**
1. Start application: `docker-compose up -d`
2. Go to: http://localhost:3000
3. Click "Module B" card
4. You'll see "🌐 Web Scraping" tab (active by default)
5. Click blue button to scrape

---

### 2. Specs Viewer (NEW!)

**Frontend:**
- `/frontend/app/module-b/page.tsx:198` - Specs viewer component

**How to Test:**
1. After web scraping, click "📊 View All Specs" tab
2. See all 62 specifications
3. Click stat cards to filter
4. Scroll through database

---

### 3. API Documentation

**File:** `/backend/api/main.py`
**URL:** http://localhost:8000/docs

**How to Test:**
1. Open browser: http://localhost:8000/docs
2. Try any endpoint with "Try it out" button
3. See request/response examples

---

### 4. Docker Configuration

**File:** `/docker-compose.yml`

**Services:**
- `database` - PostgreSQL 15 + PostGIS (port 5432)
- `backend` - FastAPI Python app (port 8000)
- `frontend` - Next.js app (port 3000)

**How to Test:**
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop all services
docker-compose down
```

---

## 🧪 How to Test Each Module

### Module A: Area Calculation

**Files:**
- Backend: `/backend/services/module_a/area_calculator.py`
- Frontend: `/frontend/app/module-a/page.tsx`
- API Route: `/backend/api/routes/area_calculation.py`

**Test:**
1. Go to http://localhost:3000
2. Click "Module A" card
3. Click "Weighted C-Value Calculator" tab
4. Enter land use areas
5. Click "Calculate C-Value"

---

### Module B: Specification Extraction

**Files:**
- Backend Web Scraper: `/backend/services/module_b/web_scraper.py` ⭐
- Backend PDF Parser: `/backend/services/module_b/pdf_parser.py`
- Backend Spec Extractor: `/backend/services/module_b/spec_extractor.py`
- Backend NOAA Parser: `/backend/services/module_b/noaa_parser.py`
- Frontend: `/frontend/app/module-b/page.tsx` ⭐
- API Route: `/backend/api/routes/spec_extraction.py` ⭐

**Test:**
1. **Web Scraping** (NEW):
   - Go to Module B
   - Click "🌐 Web Scraping" tab
   - Click "Scrape All Sources" button
   - See 62 specifications loaded

2. **View All Specs** (NEW):
   - Click "📊 View All Specs" tab
   - Browse all specifications
   - Filter by type

3. **C-Values Query**:
   - Click "C-Values" tab
   - Enter jurisdiction
   - Click "Get C-Values"

4. **Rainfall Data**:
   - Click "Rainfall Data" tab
   - Enter duration and return period
   - Click "Query Intensity"

---

### Module C: DIA Report Generator

**Files:**
- Backend: `/backend/services/module_c/rational_method.py`
- Frontend: `/frontend/app/module-c/page.tsx`
- API Route: `/backend/api/routes/dia_report.py`

**Test:**
1. Go to Module C
2. Click "Tc Calculator" tab
3. Enter flow length, elevation change
4. Click "Calculate Tc"

---

### Module D: Plan Review & QA

**Files:**
- Backend: `/backend/services/module_d/plan_reviewer.py`
- Frontend: `/frontend/app/module-d/page.tsx`
- API Route: `/backend/api/routes/qa_review.py`

**Test:**
1. Go to Module D
2. Upload PDF file
3. Click "Run Compliance Check"

---

### Module E: Proposal Generator

**Files:**
- Backend: `/backend/services/module_e/proposal_generator.py`
- Frontend: `/frontend/app/module-e/page.tsx`
- API Route: `/backend/api/routes/proposals.py`

**Test:**
1. Go to Module E
2. Fill in client information
3. Fill in project information
4. Select services
5. Click "Generate Proposal"

---

## 🗄️ Database Files

**Schema:** `/database/init/01_schema.sql`
**Seed Data:** `/database/init/02_specs.sql`

**How to Access:**
```bash
# Connect to database
docker exec -it lcr_database psql -U postgres -d lcr_drainage

# View tables
\dt

# Query specs
SELECT * FROM specs LIMIT 10;

# Exit
\q
```

---

## 📝 Documentation Files

1. **Main README**: `/README.md`
   - Project overview
   - Architecture
   - Quick start

2. **Testing Guide**: `/TESTING_AND_DEMO_GUIDE.md` ⭐
   - Complete testing instructions
   - Step-by-step demos
   - Troubleshooting

3. **Demo Guide**: `/DEMO_GUIDE.md`
   - Original demo guide
   - API examples

4. **This File**: `/WHERE_ARE_THE_FILES.md` ⭐
   - Quick reference
   - File locations

---

## 🔧 Configuration Files

**Backend:**
- `/backend/requirements.txt` - Python dependencies
- `/backend/pytest.ini` - Test configuration
- `/backend/core/settings.py` - App settings

**Frontend:**
- `/frontend/package.json` - Node dependencies
- `/frontend/next.config.js` - Next.js config
- `/frontend/tailwind.config.ts` - Tailwind CSS config
- `/frontend/tsconfig.json` - TypeScript config

**Environment:**
- `/.env.example` - Environment variables template

**To set up environment:**
```bash
cp .env.example .env
# Edit .env with your settings
```

---

## 🚀 Startup Commands

### Full Stack (Recommended)
```bash
docker-compose up -d
```

### Backend Only
```bash
cd backend
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```

### Frontend Only
```bash
cd frontend
npm install
npm run dev
```

### Database Only
```bash
docker-compose up -d database
```

---

## 🔍 Where to Find Specific Features

### Web Scraping Implementation

**Backend Logic:**
- Main scraper class: `/backend/services/module_b/web_scraper.py:16`
- Lafayette UDC scraper: `/backend/services/module_b/web_scraper.py:23`
- DOTD scraper: `/backend/services/module_b/web_scraper.py:118`
- NOAA scraper: `/backend/services/module_b/web_scraper.py:183`

**API Endpoint:**
- Route: `/backend/api/routes/spec_extraction.py:413`
- URL: POST `/api/v1/spec-extraction/scrape-web-sources`

**Frontend:**
- UI Component: `/frontend/app/module-b/page.tsx:83`
- API Call: `/frontend/lib/api-client.ts:151`

---

### Specifications Database Viewer

**Frontend:**
- Viewer component: `/frontend/app/module-b/page.tsx:198`
- Filter logic: `/frontend/app/module-b/page.tsx:222`
- Stats calculation: `/frontend/app/module-b/page.tsx:226`

**Backend:**
- Search endpoint: `/backend/api/routes/spec_extraction.py:157`
- URL: GET `/api/v1/spec-extraction/search`

---

### C-Values Calculation

**Backend:**
- Weighted C calculator: `/backend/services/module_a/area_calculator.py`
- API endpoint: `/backend/api/routes/area_calculation.py`

**Frontend:**
- UI: `/frontend/app/module-a/page.tsx`

---

### Rainfall Intensity Queries

**Backend:**
- NOAA parser: `/backend/services/module_b/noaa_parser.py`
- Interpolation logic: `/backend/services/module_b/noaa_parser.py:interpolate_intensity`
- API endpoint: `/backend/api/routes/spec_extraction.py:220`

**Frontend:**
- UI: `/frontend/app/module-b/page.tsx` (Rainfall tab)

---

## 📊 Data Files

### Scraped Data (Generated by Web Scraper)

**Lafayette UDC C-Values:**
- 17 land use types
- Source: `/backend/services/module_b/web_scraper.py:30`

**DOTD Specifications:**
- 5 standard values
- Source: `/backend/services/module_b/web_scraper.py:125`

**NOAA Atlas 14:**
- 40 rainfall intensity data points
- Source: `/backend/services/module_b/web_scraper.py:191`

---

## 🐛 Log Files

**Docker Logs:**
```bash
# Backend logs
docker-compose logs -f backend

# Frontend logs
docker-compose logs -f frontend

# Database logs
docker-compose logs -f database

# All logs
docker-compose logs -f
```

**Application Logs:**
- Backend: Stdout (view with docker logs)
- Frontend: Browser console (F12 → Console)

---

## 💡 Quick Tips

### Find a specific function:
```bash
# Search all Python files
grep -r "def function_name" backend/

# Search all TypeScript files
grep -r "function_name" frontend/
```

### Find an API endpoint:
```bash
# List all routes
grep -r "@router\." backend/api/routes/
```

### Find a UI component:
```bash
# Search frontend
grep -r "ComponentName" frontend/
```

### Check what's running:
```bash
# Docker services
docker-compose ps

# Ports in use
sudo netstat -tulpn | grep LISTEN
```

---

## 🎯 Most Important Files for Demo

1. `/TESTING_AND_DEMO_GUIDE.md` - Complete testing guide
2. `/frontend/app/module-b/page.tsx` - Web scraping UI
3. `/backend/services/module_b/web_scraper.py` - Scraper implementation
4. `/backend/api/main.py` - Main API entry point
5. `/docker-compose.yml` - Full stack setup

---

## 📞 Need Help?

1. **Check logs**: `docker-compose logs -f`
2. **Restart services**: `docker-compose restart`
3. **Check API docs**: http://localhost:8000/docs
4. **Read testing guide**: `/TESTING_AND_DEMO_GUIDE.md`

---

**Last Updated**: 2025-11-07
**Version**: 2.0.0
**Status**: ✅ Everything is working and ready to demo!
