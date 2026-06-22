# Real Fix Plan - No BS

## Current Reality

### Ruff Errors: 193 total
- B904 (86): raise-without-from
- F401 (26): unused-import
- F405 (26): undefined-local-with-import-star-usage
- F841 (11): unused-variable
- F403 (9): undefined-local-with-import-star
- UP035 (8): deprecated-import
- Others (27): various issues

### Pytest: 183 failing tests
- Template tests failing
- Portmanteau tests failing (from **kwargs removal - need to fix)
- VM service tests failing
- Deep execution tests failing
- Monitoring tests (prometheus duplicate metrics)
- Networking tests failing

## Fix Order (By Impact)

### Phase 1: Fix Portmanteau Test Failures (HIGH PRIORITY)
Our **kwargs removal broke the tests - need to update them
- Update test mocks to match new signatures
- Fix parameter passing in tests

### Phase 2: Fix Critical Linting (QUICK WINS)
- F841: Remove unused variables (11)
- F401: Remove unused imports (26)  
- UP035: Update deprecated imports (8)
- W293/B007/etc: Minor fixes (10)

### Phase 3: Fix B904 raise-without-from (86 instances)
- Add `from e` to all raise statements
- Maintain error context

### Phase 4: Fix Star Imports (F403/F405 - 35 instances)
- Convert to explicit imports
- Update __init__.py files

### Phase 5: Fix Template Tests
- Fix template loading bug
- Update template tests

### Phase 6: Fix Service Layer Tests
- Fix VM service tests
- Fix networking tests
- Fix deep execution tests

### Phase 7: Fix Monitoring Duplicate Metrics
- Fix prometheus metric registration
- Ensure singleton pattern

## Starting Now

Working through Phase 1 first...



