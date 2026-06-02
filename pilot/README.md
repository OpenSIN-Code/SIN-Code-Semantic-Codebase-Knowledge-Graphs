# SCKG Pilot Evaluation

## Objective
Measure the practical utility of the Semantic Codebase Knowledge Graph.

## Metrics

### 1. Build Time
- Target: < 10 seconds for 1000 files
- Measure: `python pilot/evaluate.py /path/to/repo`

### 2. Query Speed
- Target: < 100ms per query
- Compare: Graph vs grep

### 3. Result Quality
- Target: 90% relevance (top 5 results)
- Manual review by developer

### 4. Maintenance Cost
- Target: < 5% of dev time
- Measure: Time to rebuild after changes

## Running the Pilot

```bash
# On a test repo
cd /path/to/test-repo
python /path/to/sckg/pilot/evaluate.py .

# Check results
cat sckg-pilot-results.json
```

## Expected Results

| Repo Size | Build Time | Query Time | Speedup vs Grep |
|-----------|-----------|------------|-----------------|
| Small (<100 files) | < 2s | < 50ms | 2-5x |
| Medium (100-1000) | < 5s | < 100ms | 5-10x |
| Large (1000+) | < 10s | < 200ms | 10-20x |

## Decision Criteria

Pilot is SUCCESS if:
- Build time < 10s for 1000 files
- Query speedup > 5x vs grep
- Developer satisfaction > 4/5

Pilot is FAILURE if:
- Build time > 30s
- Query slower than grep
- Results < 50% relevant
