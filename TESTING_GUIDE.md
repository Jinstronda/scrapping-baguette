# Testing Guide - Finding Optimal Worker Count

This guide explains how to test different worker counts to find the optimal configuration for your system and network.

## Quick Test Setup

1. **Edit `config.py`** to set the number of workers
2. **Run the scraper**: `python parallel_scraper.py`
3. **Check logs**: Review `logs/` folder for results

## Testing Different Worker Counts

### Test 1: Baseline (4 workers)
```python
# config.py
NUM_WORKERS = 4
PREFIXES = list('abcd')  # 4 prefixes for quick test
MAX_DOCTORS_PER_PREFIX = 0  # Unlimited
```

Run: `python parallel_scraper.py`

Expected results in `logs/scrape_*_4workers.log` and `logs/metrics_*_4workers.json`

### Test 2: Moderate Scaling (10 workers)
```python
# config.py
NUM_WORKERS = 10
PREFIXES = list('abcdefghij')  # 10 prefixes
```

### Test 3: High Scaling (20 workers)
```python
# config.py
NUM_WORKERS = 20
PREFIXES = list('abcdefghijklmnopqrst')  # 20 prefixes
```

### Test 4: Extreme Scaling (30 workers) 🚀
```python
# config.py
NUM_WORKERS = 30
PREFIXES = list('abcdefghijklmnopqrstuvwxyz')[:30]  # First 26 letters + 4 more
# Or use 2-letter combos:
# PREFIXES = [a+b for a in 'abc' for b in 'abcdefghij']  # 30 combos
```

## What to Monitor

### Success Metrics (from logs)
```
Success rate: 100.0%        ← Target: >95%
Detail completion: 95.5%    ← Target: >90%
Speed: 4.2 doctors/second   ← Higher is better
```

### Failure Indicators
```
Failed prefixes: 0/10       ← Should be 0
Success rate: 100.0%        ← Should be 100%
```

## Analyzing Results

### Compare JSON Metrics Files

```python
import json
import glob

# Load all metrics
metrics = []
for file in sorted(glob.glob('logs/metrics_*workers.json')):
    with open(file) as f:
        metrics.append(json.load(f))

# Compare
for m in metrics:
    workers = m['config']['num_workers']
    rate = m['results']['doctors_per_second']
    success = m['results']['success_rate']
    print(f"{workers:2d} workers: {rate:.2f} doctors/sec, {success:.1f}% success")
```

### Expected Output
```
 4 workers: 3.85 doctors/sec, 100.0% success
10 workers: 9.21 doctors/sec, 100.0% success
20 workers: 17.53 doctors/sec, 98.5% success  ← Some failures starting
30 workers: 24.12 doctors/sec, 92.3% success  ← More failures (rate limiting?)
```

## Finding the Sweet Spot

### Optimal Configuration Criteria
1. **Success rate** > 95%
2. **Detail completion rate** > 90%
3. **Speed** maximized within above constraints

### Example Decision
```
 4 workers: 100% success, 3.85 docs/sec  ✓ Safe baseline
10 workers: 100% success, 9.21 docs/sec  ✓ Good scaling
20 workers:  98% success, 17.5 docs/sec  ✓ Best tradeoff!
30 workers:  92% success, 24.1 docs/sec  ✗ Too many failures
```

**Winner**: 20 workers = 4.5x speedup with <2% failures

## Fine-Tuning

Once you find the sweet spot, fine-tune delays:

```python
# config.py
NUM_WORKERS = 20  # Your optimal count

# Experiment with delays
DELAY_BETWEEN_DOCTORS = 0.8   # Reduce from 1.0s
DELAY_BETWEEN_TABS = 0.4      # Reduce from 0.5s
```

**Warning**: Going too fast will trigger rate limiting!

## Quick Tests (Small Sample)

For rapid testing without scraping thousands of doctors:

```python
# config.py
NUM_WORKERS = 30
PREFIXES = ['xa', 'xb', 'xc']  # Rare prefixes = fewer doctors
MAX_DOCTORS_PER_PREFIX = 10    # Limit to 10 per prefix
```

This scrapes only ~30 doctors but tests if 30 workers cause failures.

## Logs Folder Structure

```
logs/
├── scrape_20241025_220530_4workers.log    ← Full console output
├── metrics_20241025_220530_4workers.json  ← Structured metrics
├── scrape_20241025_220845_10workers.log
├── metrics_20241025_220845_10workers.json
├── scrape_20241025_221203_20workers.log
├── metrics_20241025_221203_20workers.json
└── metrics_20241025_221520_30workers.json
```

## Reading Metrics JSON

```json
{
  "timestamp": "2024-10-25T22:05:30.123456",
  "config": {
    "num_workers": 4,
    "prefixes": ["a", "b", "c", "d"],
    "delay_between_doctors": 1.0
  },
  "results": {
    "total_doctors": 394,
    "detail_completion_rate": 95.4,
    "success_rate": 100.0,
    "doctors_per_second": 3.85
  },
  "by_prefix": [
    {
      "prefix": "a",
      "count": 96,
      "details_complete": 93,
      "duplicates": 2,
      "error": null
    }
  ]
}
```

## Troubleshooting

### High Failure Rate
- **Reduce workers**: Try 50% fewer
- **Increase delays**: `DELAY_BETWEEN_DOCTORS = 1.5`
- **Check network**: Ensure stable connection

### Low Detail Completion
- **Increase tab delays**: `DELAY_BETWEEN_TABS = 0.7`
- **Check logs**: Look for specific error messages

### Slow Performance
- **Increase workers**: But watch success rate!
- **Decrease delays**: Carefully, risk of rate limiting
- **Use more prefixes**: Ensure workers stay busy

## Recommended Testing Sequence

1. **Test 4 workers** (baseline, should always work)
2. **Test 10 workers** (moderate scaling)
3. **Test 20 workers** (high scaling)
4. **Test 30 workers** (extreme, may fail)
5. **Pick the highest worker count** with >95% success
6. **Fine-tune delays** for that count

## Next Steps

After finding optimal config:
- Update `config.py` with your best values
- Run full scrape with all prefixes: `PREFIXES = list('abcdefghijklmnopqrstuvwxyz')`
- Consider smart expansion for 100% coverage (see README.md)

Good luck! 🚀

