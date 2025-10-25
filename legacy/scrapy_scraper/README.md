# Scrapy Health Professional Scraper

This is a Scrapy-based implementation that solves the multi-threading session issues found in the `requests`-based scraper.

## Key Advantages

- **Proper session management**: Each doctor gets its own cookiejar, preventing session conflicts
- **Built-in concurrency**: Handles 4 concurrent requests safely
- **Auto-throttling**: Automatically adjusts speed to avoid overwhelming the server
- **Automatic retries**: Retries failed requests up to 3 times
- **Clean architecture**: Scrapy framework handles complexity

## Installation

```bash
cd scrapy_scraper
pip install -r requirements.txt
```

## Usage

**Run the spider:**
```bash
scrapy crawl health_professionals
```

**Adjust concurrency:**
Edit `settings.py` and change `CONCURRENT_REQUESTS`

**View logs:**
Scrapy provides detailed progress logs automatically

## How It Works

1. **Home page**: Extracts p_auth token
2. **Search**: Submits search for each letter prefix
3. **Pagination**: Crawls through result pages (currently limited to 3 for testing)
4. **Detail flow**: For each doctor:
   - Uses unique cookiejar to avoid session conflicts
   - Makes 5 sequential requests: open → info → dossier → diplomes → personne
   - Maintains session state throughout
5. **Data cleaning**: Pipeline extracts clean JSON from HTML
6. **Database**: Saves to SQLite with deduplication

## Database

- Location: `db/scrapy_health_professionals.db`
- Same schema as original scraper
- Clean JSON storage (no HTML bloat)

## Testing

The spider is currently configured to:
- Test with prefix 'a' only
- Limit to 3 pages per prefix
- Use 4 concurrent requests

To scrape all data, modify `health_spider.py`:
- Change `self.prefixes[:1]` to `self.prefixes` (line 32)
- Remove `response.meta['page'] < 3` limit (line 93)

## Configuration

Edit `settings.py`:
- `CONCURRENT_REQUESTS`: Number of parallel requests (default: 4)
- `DOWNLOAD_DELAY`: Delay between requests (default: 0.5s)
- `RETRY_TIMES`: Number of retries (default: 3)
- `AUTOTHROTTLE_*`: Auto-throttle settings

## Comparison with requests-based Scraper

| Feature | requests-based | Scrapy-based |
|---------|---------------|--------------|
| Single-threaded | ✓ Works perfect | ✓ Works perfect |
| Multi-threaded | ✗ Session conflicts | ✓ Works with cookiejar |
| Session management | Manual | Automatic per request |
| Retries | Manual | Built-in |
| Throttling | Manual delays | Auto-throttle |
| Progress tracking | Custom | Built-in stats |

## Architecture

```
scrapy_scraper/
├── scrapy.cfg          # Scrapy project config
├── settings.py         # Spider settings
├── items.py            # Data structure
├── pipelines.py        # Data cleaning and database
├── spiders/
│   └── health_spider.py  # Main spider logic
└── requirements.txt
```

## Output

Same as original scraper:
- All basic fields: RPPS, name, profession, org, address, phone, email
- All 4 detail tabs as clean JSON (99% smaller than raw HTML)
- SQLite database with deduplication

