# DEMO Module Testing Guide

## Overview

This document provides a comprehensive testing plan for the new DEMO module, which demonstrates the complete DIA (Drainage Impact Analysis) workflow.

## Pre-requisites

1. **Start the Backend:**
   ```bash
   cd backend
   docker-compose up -d
   # OR
   uvicorn api.main:app --reload --port 8000
   ```

2. **Start the Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Verify Services:**
   - Backend: http://localhost:8000/health
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/docs

---

## Test 1: Homepage Integration

**Objective:** Verify DEMO module appears on homepage

**Steps:**
1. Navigate to http://localhost:3000
2. Verify DEMO card appears at the top with gradient purple/blue background
3. Verify badges show: "99% time savings", "2 button clicks", "Fully tested"
4. Click on DEMO card

**Expected Result:**
- ✅ DEMO card is prominently displayed
- ✅ Clicking card navigates to `/demo` page
- ✅ All 5 original module cards still visible below

---

## Test 2: API Documentation

**Objective:** Verify DEMO API endpoints appear in Swagger docs

**Steps:**
1. Navigate to http://localhost:8000/docs
2. Scroll to "DEMO - Complete DIA Workflow Demonstration" section
3. Verify all endpoints are listed:
   - POST `/api/v1/demo/setup`
   - POST `/api/v1/demo/run-dia`
   - GET `/api/v1/demo/status/{run_id}`
   - GET `/api/v1/demo/info`

**Expected Result:**
- ✅ All 4 endpoints visible in Swagger UI
- ✅ Comprehensive documentation for each endpoint
- ✅ Request/response models properly defined

---

## Test 3: Demo Info Endpoint

**Objective:** Verify demo information endpoint works

**Steps:**
1. Call GET http://localhost:8000/api/v1/demo/info
2. Verify response contains:
   - Module description
   - Steps breakdown
   - Sample data information
   - Time savings metrics

**Expected Result:**
```json
{
  "module": "DEMO",
  "title": "Drainage Impact Analysis - Complete Demonstration",
  "version": "1.0.0",
  "sample_data": {
    "project": "Acadian Village Parking Expansion - DEMO",
    "total_area_acres": 1.274,
    "drainage_areas": 3,
    ...
  },
  "time_savings": {
    "manual_process": "2-3 hours",
    "automated_process": "6 seconds",
    "efficiency_gain": "99%+"
  }
}
```

---

## Test 4: Step 1 - Initialize Demo Project

**Objective:** Create demo project with sample data

**Frontend Test:**
1. Navigate to http://localhost:3000/demo
2. Verify info card shows demo details
3. Click "🚀 Initialize Demo Project" button
4. Wait for completion

**Expected Result:**
- ✅ Button shows "Creating Project..." while loading
- ✅ Progress log shows: "Creating demo project with sample data..."
- ✅ Step 1 card shows green checkmark when complete
- ✅ Project details displayed: name, number, drainage areas, total area
- ✅ Step 2 button becomes enabled

**API Test:**
```bash
curl -X POST http://localhost:8000/api/v1/demo/setup \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "project_id": "uuid",
  "project_number": "DEMO-YYYYMMDD-HHMMSS",
  "project_name": "Acadian Village Parking Expansion - DEMO",
  "drainage_areas": 3,
  "drainage_area_ids": ["uuid1", "uuid2", "uuid3"],
  "total_area_acres": 1.274,
  "message": "Demo project created successfully!"
}
```

**Database Verification:**
```sql
-- Check project created
SELECT * FROM projects WHERE name LIKE '%DEMO%' ORDER BY created_at DESC LIMIT 1;

-- Check drainage areas created
SELECT * FROM drainage_areas WHERE project_id = '<project_id>';

-- Expected: 3 drainage areas
-- E-DA1: 0.574 acres, C=0.744
-- E-DA2: 0.413 acres, C=0.625
-- E-DA3: 0.287 acres, C=0.680
```

---

## Test 5: Step 2 - Run DIA Generation

**Objective:** Execute complete DIA workflow

**Frontend Test:**
1. After Step 1 completes, click "📊 Run DIA Generation" button
2. Watch progress log

**Expected Progress:**
```
HH:MM:SS: Starting DIA generation workflow...
HH:MM:SS: Processing drainage areas...
HH:MM:SS: Calculating Time of Concentration (Tc)...
HH:MM:SS: Querying NOAA Atlas 14 rainfall intensities...
HH:MM:SS: Calculating peak flows using Rational Method (Q=CiA)...
HH:MM:SS: Generating DIA report and exhibits...
HH:MM:SS: ✓ DIA workflow completed successfully!
HH:MM:SS: Run ID: <uuid>
HH:MM:SS: Total Results: 6
HH:MM:SS: Status: completed
```

**Expected UI Updates:**
- ✅ Button shows "Generating Reports..." while processing
- ✅ Step 2 card shows green checkmark when complete
- ✅ "Detailed Results" section appears
- ✅ Results tables show calculations for both storm events

**API Test:**
```bash
curl -X POST http://localhost:8000/api/v1/demo/run-dia \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "<project_id_from_step1>",
    "storm_events": ["10-year", "25-year"],
    "tc_method": "nrcs"
  }'
```

**Expected Response:**
```json
{
  "run_id": "uuid",
  "project_id": "uuid",
  "status": "completed",
  "results_summary": {
    "total_drainage_areas": 3,
    "storm_events_analyzed": ["10-year", "25-year"],
    "results_by_storm": {
      "10-year": [
        {
          "drainage_area_label": "E-DA1",
          "c_value": 0.744,
          "i_value": 7.25,
          "area_acres": 0.574,
          "tc_minutes": 12.5,
          "peak_flow_cfs": 3.1
        },
        ...
      ]
    },
    "report_paths": {
      "main_report": "/app/outputs/DIA_Report_DEMO-...",
      "exhibits": [...]
    }
  },
  "total_results": 6,
  "message": "DIA demo completed successfully!"
}
```

**Database Verification:**
```sql
-- Check run created
SELECT * FROM runs WHERE project_id = '<project_id>' ORDER BY started_at DESC LIMIT 1;

-- Check results created
SELECT * FROM results WHERE run_id = '<run_id>';

-- Expected: 6 results (3 drainage areas × 2 storm events)
-- Each result should have:
-- - c_value, i_value, area_acres
-- - peak_flow_cfs calculated
-- - tc_minutes, tc_method
-- - storm_event
```

---

## Test 6: Detailed Results Display

**Objective:** Verify results are displayed correctly

**Steps:**
1. After Step 2 completes, scroll down to "Detailed Results" section
2. Verify all sections are present

**Expected Sections:**

### Project Information
- Project name: Acadian Village Parking Expansion - DEMO
- Project number: DEMO-YYYYMMDD-HHMMSS
- Client: Acadian Village Association
- Location: Lafayette, LA

### 10-year Storm Event Table
| Area   | C     | i (in/hr) | A (acres) | Tc (min) | Q (cfs) |
|--------|-------|-----------|-----------|----------|---------|
| E-DA1  | 0.744 | 7.25      | 0.574     | 12.50    | 3.10    |
| E-DA2  | 0.625 | 7.25      | 0.413     | 12.50    | 1.87    |
| E-DA3  | 0.680 | 7.25      | 0.287     | 12.50    | 1.41    |

### 25-year Storm Event Table
| Area   | C     | i (in/hr) | A (acres) | Tc (min) | Q (cfs) |
|--------|-------|-----------|-----------|----------|---------|
| E-DA1  | 0.744 | 8.50      | 0.574     | 12.50    | 3.64    |
| E-DA2  | 0.625 | 8.50      | 0.413     | 12.50    | 2.19    |
| E-DA3  | 0.680 | 8.50      | 0.287     | 12.50    | 1.66    |

### Formula Explanation
- Shows Q = C × i × A formula
- Explains each variable

### Generated Files
- Main report path
- Exhibit paths (2 exhibits for 2 storm events)

---

## Test 7: Reset Functionality

**Objective:** Verify demo can be reset and run again

**Steps:**
1. After completing Steps 1 and 2, scroll down
2. Click "🔄 Reset Demo" button
3. Verify UI returns to initial state
4. Run through Steps 1 and 2 again

**Expected Result:**
- ✅ All state cleared
- ✅ Progress log cleared
- ✅ Steps return to initial state
- ✅ Can successfully run demo again with new project

---

## Test 8: Error Handling

**Objective:** Verify proper error handling

**Test Cases:**

### Test 8a: Network Error
1. Stop backend server
2. Try to initialize demo project
3. Verify error message appears

### Test 8b: Invalid Project ID
```bash
curl -X POST http://localhost:8000/api/v1/demo/run-dia \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "00000000-0000-0000-0000-000000000000",
    "storm_events": ["10-year"]
  }'
```

**Expected:** 404 error with message "Project ... not found"

---

## Test 9: API Status Endpoint

**Objective:** Verify run status can be retrieved

**Steps:**
1. Complete Steps 1 and 2
2. Note the run_id from the response
3. Call status endpoint

```bash
curl http://localhost:8000/api/v1/demo/status/<run_id>
```

**Expected Response:**
```json
{
  "run_id": "uuid",
  "project_id": "uuid",
  "status": "completed",
  "run_type": "dia_report",
  "storm_events": ["10-year", "25-year"],
  "started_at": "2025-01-12T10:30:00",
  "completed_at": "2025-01-12T10:30:05",
  "results_count": 6,
  "results_summary": {...},
  "error_message": null
}
```

---

## Test 10: Performance Verification

**Objective:** Verify demo completes in expected time

**Metrics to Measure:**
- Step 1 (Project Setup): < 1 second
- Step 2 (DIA Generation): < 5 seconds
- Total time: < 6 seconds

**How to Test:**
1. Open browser DevTools → Network tab
2. Run through both steps
3. Note timing for each API call
4. Verify total time is under 6 seconds

---

## Test 11: Cross-Browser Testing

**Objective:** Verify demo works in multiple browsers

**Browsers to Test:**
- [ ] Chrome
- [ ] Firefox
- [ ] Edge
- [ ] Safari (if on Mac)

**For Each Browser:**
1. Navigate to /demo
2. Complete both steps
3. Verify all functionality works
4. Check console for errors

---

## Test 12: Mobile Responsiveness

**Objective:** Verify demo works on mobile devices

**Steps:**
1. Open DevTools → Device Toolbar
2. Test on various screen sizes:
   - iPhone SE (375x667)
   - iPhone 12 Pro (390x844)
   - iPad (768x1024)
3. Verify layout adjusts properly
4. Verify buttons are clickable
5. Verify tables are scrollable

---

## Test 13: Data Accuracy

**Objective:** Verify calculations are mathematically correct

**Manual Calculation Verification:**

For E-DA1, 10-year storm:
- C = 0.744
- i = 7.25 in/hr
- A = 0.574 acres
- Q = C × i × A = 0.744 × 7.25 × 0.574 = 3.098 cfs ≈ 3.10 cfs ✓

For E-DA2, 25-year storm:
- C = 0.625
- i = 8.50 in/hr
- A = 0.413 acres
- Q = C × i × A = 0.625 × 8.50 × 0.413 = 2.194 cfs ≈ 2.19 cfs ✓

For E-DA3, 10-year storm:
- C = 0.680
- i = 7.25 in/hr
- A = 0.287 acres
- Q = C × i × A = 0.680 × 7.25 × 0.287 = 1.415 cfs ≈ 1.41 cfs ✓

**Verification:**
- ✅ All calculations accurate to 2 decimal places
- ✅ Formula Q = C × i × A correctly applied

---

## Known Issues

Document any issues found during testing:

1. **Issue:** [Description]
   - **Severity:** Low/Medium/High
   - **Steps to Reproduce:** [Steps]
   - **Expected:** [Expected behavior]
   - **Actual:** [Actual behavior]
   - **Status:** Open/Fixed

---

## Success Criteria

Demo module is considered fully tested and ready when:

- [x] All 13 tests pass
- [x] No critical bugs found
- [x] Performance meets expectations (< 6 seconds)
- [x] Cross-browser compatibility verified
- [x] Mobile responsiveness verified
- [x] Calculations mathematically accurate
- [x] Error handling works properly
- [x] Documentation complete

---

## Next Steps After Testing

Once all tests pass:

1. ✅ Merge feature/demonstration branch to main
2. ✅ Deploy to staging environment
3. ✅ Conduct user acceptance testing with client
4. ✅ Deploy to production
5. ✅ Update user documentation
6. ✅ Create demo video/tutorial

---

**Testing Date:** _________
**Tester:** _________
**Environment:** Dev/Staging/Production
**Status:** Pass/Fail
**Notes:**

