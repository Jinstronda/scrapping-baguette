# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment Setup

**Conda Environment**: Always use `turing0.1`
```bash
conda activate turing0.1
```

**Dependencies**: Install via pip
```bash
pip install -r requirements.txt
```

## Core Commands

### Running the Scraper
```bash
# Default: 4 workers, default DB path
python -m scraper.main

# Custom configuration
python -m scraper.main --threads 8 --db db/custom.db

# Testing with limited scope
python tests/test_3_pages.py
python tests/test_one_doctor_complete.py
```

### Database Operations
```bash
# Check database contents
python tests/check_db.py db/test_data.db

# Verify data quality
sqlite3 db/test_data.db "SELECT COUNT(*) FROM professionals"
sqlite3 db/test_data.db "SELECT COUNT(*) FROM professionals WHERE situation_data IS NOT NULL"
```

### Testing Individual Components
```bash
# Test parser extraction
python tests/test_parser_extraction.py

# Test single doctor workflow
python tests/test_single_doctor_workflow.py

# Test with multiple workers
python tests/test_20_workers.py
```

## Architecture Overview

### Critical Data Flow Issue
**IMPORTANT**: There's a known bug in multi-threaded mode where contact information (address, phone, email) is not properly persisted. Single-threaded scraping works correctly.

**Root Cause**: In `scraper/worker.py` lines 256-277:
1. First upsert (line 262) saves basic card data including contact info
2. Second upsert (line 277) saves ONLY `rpps` + 4 detail fields
3. The second upsert creates a partial dict without contact fields
4. Despite COALESCE logic in database.py, contact info may be lost

**Investigation Status**: Sequential thinking analysis in progress. The COALESCE SQL should preserve existing values when new values are NULL, but empirical evidence shows 175 records with only 2 addresses, 0 phones, 1 email in multi-threaded runs.

### Work Distribution Pattern
- **Queue initialization**: Shuffled alphabet (a-z) to balance load
- **Prefix expansion**: When result set > 3 pages, prefix splits (a → aa, ab, ac...az)
- **Thread-local sessions**: Each worker maintains its own HTTP session
- **Thread-local DB connections**: Each worker gets independent SQLite connection via `threading.local()`

### Key Request Sequence Per Doctor
1. Extract `p_auth` token from home page
2. POST search form with prefix
3. GET pagination (pages 2-10)
4. POST `DetailsPPAction` to open doctor detail
5. POST `infoDetailPP` to get situation tab (returns HTML)
6. POST `detailsPPDossierPro`, `detailsPPDiplomes`, `detailsPPPersonne` for remaining tabs

### Module Responsibilities
- **config.py**: Static configuration (threads, delays, URLs, headers)
- **database.py**: SQLite schema + thread-safe upsert with COALESCE logic
- **session.py**: HTTP session factory, retry wrappers, random delays (50-150ms)
- **parser.py**: BeautifulSoup extractors for search results and detail pages
  - Lines 121-133: Extract address/phone/email from search result cards
  - Looks for divs with classes: `adresse`, `tel`, `mssante`
- **content_extractor.py**: Converts raw HTML detail tabs → structured JSON
- **worker.py**: Core scraping logic (search, paginate, fetch details, upsert)
- **coordinator.py**: Thread pool + work queue (producer-consumer pattern)
- **logger.py**: Thread-aware structured logging (`[T-{thread_id}]` format)

### Database Schema
Table `professionals` (RPPS as PRIMARY KEY):
- Basic fields: `name`, `profession`, `organization`, `address`, `phone`, `email`, `finess`, `siret`
- Detail fields: `situation_data`, `dossier_data`, `diplomes_data`, `personne_data` (JSON strings)
- Timestamps: `created_at`, `updated_at`

**Upsert Strategy**: `INSERT ... ON CONFLICT(rpps) DO UPDATE SET field=COALESCE(excluded.field, field)`
- Should preserve existing non-NULL values when new value is NULL
- Intended to support incremental updates from multiple threads

## Code Patterns and Constraints

### Function Size Limits
From Cursor rules (`.cursor/rules/main.mdc`):
- Functions: <25 lines (strict requirement from user preferences)
- Files: <500 lines (split at 400)
- Classes: <200 lines

### DRY Enforcement
Before writing any function:
1. Search codebase for existing implementations
2. Check for similar logic in other modules
3. If 70%+ similar, reuse/extend existing code
4. Extract shared logic immediately when duplication detected

### Testing Philosophy
- Evidence-based: Verify with actual test runs, not assumptions
- Use SequentialThinking MCP for complex debugging
- Always test single-threaded vs multi-threaded behavior separately
- Check database state after runs to verify data persistence

## Common Issues and Debugging

### Multi-Threading Data Loss
**Symptom**: Contact info (address/phone/email) missing in multi-threaded runs but present in single-threaded
**Investigation**:
- Parser logic is correct (verified by single-thread success)
- Likely issue in worker.py detail_update dict construction
- May require reworking the two-step upsert pattern

**Debug Approach**:
```bash
# Run single-threaded (works correctly)
python -m scraper.main --threads 1 --db db/single.db

# Run multi-threaded (shows data loss)
python -m scraper.main --threads 4 --db db/multi.db

# Compare results
sqlite3 db/single.db "SELECT COUNT(*) FROM professionals WHERE address IS NOT NULL"
sqlite3 db/multi.db "SELECT COUNT(*) FROM professionals WHERE address IS NOT NULL"
```

### HTML Structure Changes
If parser stops working:
1. Capture sample HTML: Save response.text to file in tests/
2. Run tests/check_html.py to verify structure
3. Check for class name changes: `contenant_resultat`, `nom_prenom`, `adresse`, `tel`, `mssante`
4. Update parser.py selectors accordingly

### Rate Limiting
If seeing connection errors:
1. Increase delays in config.py: `MIN_DELAY_SECONDS`, `MAX_DELAY_SECONDS`
2. Reduce thread count: `--threads 2`
3. Check logs for HTTP status codes (429 = rate limited)

## Performance Characteristics

### Expected Throughput
- Single worker: ~2-3 doctors/second
- 4 workers: ~8-12 doctors/second
- 20 workers: ~40-60 doctors/second (tested successfully)
- 100 workers: ~200-300 doctors/second (theoretical)

### Bottlenecks
1. Network latency (50-150ms forced delays for politeness)
2. Detail fetching: 5 HTTP requests per doctor × delay
3. SQLite file-level locking (minimal with thread-local connections)

### Resource Usage
- Per-worker memory: ~10MB (session + parser)
- 100 workers: ~1GB total
- Database growth: ~500MB per 100k doctors

## Development Notes

### When Modifying Parser
1. Always test against real HTML samples in tests/
2. Update both single-doctor tests and multi-doctor tests
3. Verify all 4 detail tabs extract correctly
4. Check data completeness: run check_all_fields.py after changes

### When Modifying Worker Logic
1. Test with --threads 1 first (simpler debugging)
2. Then test with --threads 4 to verify thread safety
3. Monitor logs for upsert confirmations
4. Query database afterward to verify no data loss

### When Tuning Performance
1. Profile first: Add timing logs around suspected bottlenecks
2. Check if delays can be reduced (risk: rate limiting)
3. Test worker scaling: 1 → 4 → 10 → 20
4. Monitor for diminishing returns or server pushback

## Key Cursor Rules to Follow
- Functions must be <25 lines
- Search for existing implementations before writing new code
- Use SequentialThinking MCP for complex analysis
- Evidence-based development: verify claims with tests
- Reconfirm assumptions with tests before proceeding
