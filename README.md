# LCR Civil Drainage Automation System

**Production-Ready Civil Engineering Automation Platform**

A comprehensive, modular automation system designed for LCR & Company to streamline drainage analysis, regulatory compliance, plan review, and proposal generation for civil engineering projects.

---

## 🎯 Project Overview

This system automates the most time-intensive tasks in civil engineering drainage design, reducing manual work from days to minutes while maintaining professional quality and regulatory compliance.

### Business Context
- **Client**: LCR & Company (Civil Engineering Firm)
- **Developer**: Dozier Tech
- **Total Contract Value**: $42,000
- **Timeline**: 15-18 weeks (5 modules delivered incrementally)
- **Primary Use Cases**: Municipal drainage projects, land development, DOT compliance

### Key Value Propositions
- **80% time savings** on drainage calculations and report generation
- **100% accuracy** on weighted C-value calculations and area computations
- **Instant regulatory compliance** with UDC and DOTD specifications
- **Automated QA** for plan sets (18+ sheet types)
- **Professional proposal generation** in minutes instead of hours

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Next.js 14+ Web Portal                    │
│            (TypeScript, Shadcn/UI, Tailwind CSS)            │
└────────────┬─────────────────────────────────┬──────────────┘
             │                                 │
             │ REST API                        │ WebSocket
             │                                 │
┌────────────┴─────────────────────────────────┴──────────────┐
│                  FastAPI Backend Services                   │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐        │
│  │Mod A │  │Mod B │  │Mod C │  │Mod D │  │Mod E │        │
│  │ Area │  │ Spec │  │ DIA  │  │  QA  │  │ Doc  │        │
│  │ Calc │  │Extract│  │Report│  │Review│  │ Gen  │        │
│  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ SQL + PostGIS
                      │
┌─────────────────────┴───────────────────────────────────────┐
│           PostgreSQL 15 + PostGIS Database                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  projects │ drawings │ drainage_areas │ results     │   │
│  │  runs │ specs │ qa_results │ proposals              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend:**
- Python 3.11
- FastAPI (async REST API framework)
- PostgreSQL 15 + PostGIS (geospatial database)
- LangChain (LLM-powered PDF parsing)
- Pandas (data manipulation)
- openpyxl (Excel automation)
- python-docx / ReportLab (document generation)
- PyPDF2 / pytesseract (PDF processing + OCR)

**Frontend:**
- Next.js 14+ with App Router
- TypeScript
- Shadcn/UI + Tailwind CSS
- Recharts (data visualization)
- React Hook Form + Zod (form validation)

**Deployment:**
- Docker + Docker Compose
- Nginx (reverse proxy)
- Azure / On-Premise flexible

**Development:**
- pytest (backend testing)
- Jest + React Testing Library (frontend testing)
- Black + isort (Python formatting)
- ESLint + Prettier (TypeScript formatting)

---

## 📦 Five Core Modules

### Module A: Automated Area Calculation Engine
**Deliverable Timeline**: 2 weeks | **Value**: $7,500

**Capabilities:**
- Parse Civil 3D polylines and survey CSV data
- Calculate impervious vs. pervious drainage areas
- Compute weighted runoff coefficients (C-values)
- Auto-populate Excel TOC (Time of Concentration) workbooks
- Export results to CSV + GeoJSON for GIS integration

**Key Files:**
- `backend/services/module_a/area_calculator.py` - Core calculation engine
- `backend/services/module_a/csv_parser.py` - Survey data parser
- `backend/services/module_a/excel_updater.py` - TOC workbook automation
- `backend/api/routes/area_calculation.py` - REST API endpoints

**Accuracy Requirements:**
- Area calculations: ±0.5%
- Weighted C-values: Exact (to 3 decimal places)

---

### Module B: UDC & DOTD Specification Extraction
**Deliverable Timeline**: 3 weeks | **Value**: $8,000

**Capabilities:**
- Parse Lafayette UDC and DOTD manuals (PDF → structured data)
- Extract runoff coefficients by land use type
- Extract rainfall intensity tables (NOAA Atlas 14)
- Extract Tc (Time of Concentration) limits and detention rules
- Searchable regulatory database with jurisdiction filtering

**Key Files:**
- `backend/services/module_b/pdf_parser.py` - LangChain-powered extraction
- `backend/services/module_b/spec_extractor.py` - Regulatory data extraction
- `backend/models/specs.py` - Database models
- `database/init/02_specs.sql` - Specs table schema

**Data Sources:**
- Lafayette UDC (Unified Development Code)
- DOTD Hydraulic Design Manual
- NOAA Atlas 14 rainfall data

---

### Module C: Drainage Impact Analysis (DIA) Report Generator
**Deliverable Timeline**: 4 weeks | **Value**: $12,000

**Capabilities:**
- Generate complete DIA reports matching professional format (58+ pages)
- Implement Rational Method: **Q = CiA** (flow = coefficient × intensity × area)
- Calculate for 10, 25, 50, and 100-year storm events
- Pre-development vs. post-development comparison
- Auto-generate Exhibits 3A-3D (SSA runoff calculations)
- Include hydrographs, FIRM panels, NOAA Atlas 14 tables
- No-Net-Fill analysis for flood zones

**Key Files:**
- `backend/services/module_c/rational_method.py` - Q=CiA calculator
- `backend/services/module_c/report_generator.py` - Word/PDF report builder
- `backend/services/module_c/exhibit_generator.py` - Technical exhibits
- `backend/models/drainage_results.py` - Results database models

**Calculation Accuracy:**
- Time of Concentration (Tc): ±1.0 minute
- Flow rate (Q): ±2%

**Reference Output:** `project_context/Drainage Analysis Report - Acadiana High.pdf`

---

### Module D: Plan Review & QA Automation
**Deliverable Timeline**: 3 weeks | **Value**: $9,500

**Capabilities:**
- Automated compliance checking for plan sets (C-1 through C-18)
- OCR-based extraction of plan notes and specifications
- Validate presence of required notes (LPDES, LUS, DOTD, ASTM standards)
- Cross-reference drainage calculations with plan exhibits
- Generate QA report with pass/fail for each sheet type

**Key Files:**
- `backend/services/module_d/plan_reviewer.py` - OCR + validation engine
- `backend/services/module_d/compliance_checker.py` - Rules engine
- `backend/services/module_d/qa_report_generator.py` - QA PDF generator

**Validation Checks:**
- 25+ standard note requirements
- Drainage area labels match calculations
- Inlet/pipe sizing consistency
- Sheet completeness (C-1 to C-18)

---

### Module E: Proposal & Document Automation
**Deliverable Timeline**: 2 weeks | **Value**: $5,000

**Capabilities:**
- Auto-generate branded proposals with scope, timeline, pricing
- Create cover letters and submittal documents
- Merge LCR & Dozier Tech branding assets
- Template-based generation for consistent formatting

**Key Files:**
- `backend/services/module_e/proposal_generator.py` - Proposal engine
- `backend/services/module_e/templates/` - Word/PDF templates
- `backend/api/routes/documents.py` - Document generation API

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Git
- 8GB+ RAM (for PostgreSQL + PostGIS)

### Setup (5 minutes)

```bash
# Clone repository
git clone <repo-url>
cd LCR_Civil_Automations

# Copy environment configuration
cp .env.example .env

# Launch entire stack
docker-compose up -d

# Wait for database initialization (~30 seconds)
docker-compose logs -f database

# Verify all services are running
docker-compose ps
```

### Access Points
- **Web Portal**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:5432 (postgres/postgres)

### Run Tests
```bash
# Backend tests
docker-compose exec backend pytest

# Frontend tests
docker-compose exec frontend npm test

# Integration tests
docker-compose exec backend pytest tests/integration/
```

---

## 🗄️ Database Schema

```sql
-- Core tables
projects          # Client projects (name, location, type)
drawings          # CAD drawings linked to projects
drainage_areas    # Calculated areas with geometry (PostGIS)
results           # Drainage calculation results (Q, Tc, etc.)
runs              # Analysis runs (timestamp, user, parameters)
specs             # Regulatory specifications (UDC, DOTD)
qa_results        # Plan review QA results
proposals         # Generated proposal documents
```

**Key Relationships:**
- `drawings` → `projects` (many-to-one)
- `drainage_areas` → `drawings` (many-to-one)
- `results` → `runs` → `projects` (chain)
- `specs` → jurisdiction filtering

---

## 📊 Real Data Integration

This system uses **actual project data** from LCR & Company:

### Available Test Data
1. **Survey Data**: `project_context/2025-06-24 Topo Survey/*.csv`
   - Storm topology with northing, easting, elevation
   - 1000+ survey points for terrain modeling

2. **Excel Templates**: `project_context/25-020 TOC Calculation SUNSET PARK.xlsx`
   - Real Time of Concentration workbook
   - Flow path analysis tables

3. **Example DIA Report**: `project_context/Drainage Analysis Report - Acadiana High.pdf`
   - 58-page professional report (target output for Module C)
   - Exhibits 3A-3D with SSA calculations
   - No-Net-Fill analysis

4. **Plan Sets**:
   - `project_context/Acadiana High School/*.pdf`
   - `project_context/LJ Alleman/*.pdf`
   - Full civil engineering plan sets (C-1 to C-18 sheets)

5. **Business Documents**: `project_context/ALL BUSINESS DOCS/`
   - SOW (Statement of Work)
   - Technical architecture diagrams
   - Modular breakdown specifications

---

## 🧪 Testing Strategy

### Unit Tests (Backend)
- Each module has isolated tests in `backend/tests/unit/module_*/`
- Test coverage target: 90%+
- Fixtures for sample data in `backend/tests/fixtures/`

### Integration Tests
- End-to-end workflows in `backend/tests/integration/`
- Test with real project_context data
- Database rollback after each test

### Frontend Tests
- Component tests with React Testing Library
- E2E tests with Playwright (future enhancement)

### Quality Gates
```bash
# Must pass before merge
pytest --cov=backend --cov-report=term-missing --cov-fail-under=90
npm run test -- --coverage
black --check backend/
isort --check-only backend/
eslint frontend/
```

---

## 📚 Documentation

- **[API.md](docs/API.md)** - Complete API reference with examples
- **[USER_GUIDE.md](docs/USER_GUIDE.md)** - Step-by-step user workflows
- **[TESTING.md](docs/TESTING.md)** - Testing procedures and standards
- **[DEVELOPMENT.md](docs/DEVELOPMENT.md)** - Developer setup and guidelines
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Deep dive into system design

---

## 🔐 Security & Compliance

- Environment variables for secrets (`.env` file, never committed)
- Database backups automated daily
- User authentication (future: OAuth2 + JWT)
- Role-based access control (Admin, Engineer, Viewer)
- Audit logging for all calculations and document generation

---

## 🛠️ Development Workflow

### Branch Strategy
- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - New features
- `bugfix/*` - Bug fixes

### Commit Conventions
```
feat(module-a): add weighted C-value calculator
fix(module-c): correct Rational Method Tc calculation
docs(readme): update setup instructions
test(module-b): add LangChain PDF parser tests
```

### Code Review Checklist
- [ ] All tests passing
- [ ] Code coverage ≥90%
- [ ] Documentation updated
- [ ] Type hints added (Python) / TypeScript strict mode
- [ ] No hardcoded credentials or secrets
- [ ] Performance benchmarks acceptable

---

## 📈 Performance Benchmarks

| Operation | Target Time | Current |
|-----------|-------------|---------|
| Parse survey CSV (1000 points) | <2 seconds | TBD |
| Calculate weighted C-values (10 areas) | <1 second | TBD |
| Generate DIA report (4 storm events) | <30 seconds | TBD |
| PDF spec extraction (100-page manual) | <5 minutes | TBD |
| Plan review QA (18 sheets) | <3 minutes | TBD |

---

## 🚧 Roadmap

### Phase 1: Foundation (Weeks 1-2) ✅
- [x] Project structure
- [x] Docker environment
- [x] Database schema
- [x] README and documentation

### Phase 2: Core Modules (Weeks 3-12)
- [ ] Module A: Area Calculation Engine
- [ ] Module B: Spec Extraction
- [ ] Module C: DIA Report Generator
- [ ] Module D: Plan Review QA
- [ ] Module E: Proposal Automation

### Phase 3: Integration & Polish (Weeks 13-15)
- [ ] End-to-end integration tests
- [ ] Performance optimization
- [ ] User acceptance testing
- [ ] Deployment to production

### Future Enhancements (Post-Launch)
- Civil 3D Add-in (.NET integration)
- Real-time collaboration features
- Mobile app (React Native)
- AI-powered design recommendations
- Multi-jurisdiction support (expand beyond Lafayette)

---

## 🤝 Support & Contact

**Developer**: Dozier Tech
**Client**: LCR & Company
**Project Manager**: [Contact Info]

For technical issues or feature requests, contact the development team.

---

## 📄 License

Proprietary software developed for LCR & Company by Dozier Tech.
All rights reserved. (See contract: `project_context/ALL BUSINESS DOCS/Dozier_Tech_LCR_Company_Terms_SOW1_Final.pdf`)

---

## 🎓 References

- **Rational Method**: Q = CiA (FHWA Hydraulic Engineering Circular 22)
- **NOAA Atlas 14**: Precipitation-Frequency Atlas (rainfall intensity data)
- **Lafayette UDC**: Unified Development Code (local regulations)
- **DOTD Manual**: Louisiana Department of Transportation Hydraulic Design Manual
- **Civil 3D**: Autodesk Storm & Sanitary Analysis (SSA)

---

**Last Updated**: 2025-11-06
**Version**: 1.0.0-alpha
**Status**: Active Development 🚀
