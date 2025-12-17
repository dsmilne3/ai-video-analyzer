## Testing Overview

The project includes a comprehensive test suite covering unit tests, integration tests, and end-to-end validation.

### Test Suite Summary

**48 total tests** covering:
- **Unit tests (40)**: Happy paths, input validation, error handling, rubric formats, results persistence, provider switching, transcription components, edge cases
- **Integration tests (8)**: End-to-end pipelines, rubric lifecycle, provider handling, error paths, UI smoke, live provider opt-in

## Running Tests

### Quick Test Commands

```bash
# Run all tests with summary
pytest -q

# Run all tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_comprehensive.py -v

# Run specific test
pytest tests/test_comprehensive.py::test_validate_rubric_valid_old_format -v
```

### Browser E2E (Playwright)
- Requirement: Install Playwright and browsers before running any E2E tests.
  - Activate venv and install:
    - `source activate.sh`
    - `pip install playwright pytest-playwright`
    - `playwright install chromium`
  - Or use venv binaries directly (no activation):
    - `./activate.sh`
    - `venv/bin/pip install playwright pytest-playwright`
    - `venv/bin/playwright install chromium`
- Verify install:
  - `playwright --version` (or `venv/bin/playwright --version`)
  - `python -c "import playwright; print(playwright.__version__)"`
- Test location and marker:
  - E2E tests live in [tests/e2e](tests/e2e) and use the `e2e` marker registered in [pytest.ini](pytest.ini).
- Run E2E tests:
  - `venv/bin/python -m pytest -m e2e tests/e2e -v`
  - Debug: `venv/bin/python -m pytest -m e2e tests/e2e -v --headed --slowmo 500`
- Notes:
  - Use stable selectors (`get_by_role`, `get_by_label`) and add `data-testid` for critical elements.
  - Streamlit reruns can cause flakiness; prefer `wait_for_selector` and `wait_for_load_state('networkidle')` after actions.

### Test Files

#### Unit Tests
- **`tests/test_evaluator.py`**: Core evaluation and feedback generation (3 tests)
- **`tests/test_comprehensive.py`**: Comprehensive test suite (36 tests)
  - Happy path tests (4)
  - Input validation tests (10)
  - Error handling tests (3)
  - Rubric format tests (4)
  - Results persistence tests (3)
  - Provider switching tests (3)
  - Transcription component tests (5)
  - Edge cases (4)
- **`tests/test_chunking_fix.py`**: Integration test for chunked evaluation (1 test)

#### Integration Tests
- **`tests/integration/test_e2e_file_pipeline.py`**: File → transcript → evaluation → save results
- **`tests/integration/test_url_download_pipeline.py`**: URL pipeline simulation (no network)
- **`tests/integration/test_rubric_lifecycle.py`**: Create → validate → list → evaluate
- **`tests/integration/test_provider_handling.py`**: No key fallback, API failure graceful handling
- **`tests/integration/test_results_persistence.py`**: Timestamped filenames and reloadability
- **`tests/integration/test_error_paths.py`**: Partial pipeline failures, dependency guidance
- **`tests/integration/test_ui_smoke.py`**: Headless Streamlit app startup verification
- **`tests/integration/test_provider_live.py`**: Opt-in live provider test (requires API keys)
- **`tests/run_end_to_end_demo.py`**: Full pipeline with real transcription and API calls

## Test Coverage Areas

### 1. Input Validation (High Priority)
Validates rubric structure, criteria weights, scale values, and thresholds:
- Missing required keys
- Empty criteria lists
- Duplicate criterion IDs
- Invalid weights (not summing to 1.0)
- Invalid scale ranges
- Invalid threshold values
- Both old (flat) and new (hierarchical) formats

### 2. Error Handling (High Priority)
Ensures graceful degradation and fallback mechanisms:
- Nonexistent rubric files → fallback to default
- Malformed JSON → graceful handling
- Missing API keys → system still functions
- API failures → fallback to heuristic scoring

### 3. Rubric Format Variations (High Priority)
Tests both supported rubric formats:
- Flat format (old): criteria array with weights
- Hierarchical format (new): categories with nested criteria
- Edge cases: single criterion, many criteria (15+)

### 4. Results Persistence (Medium Priority)
Verifies result saving and file management:
- JSON format output validation
- Timestamp-based no-overwrite behavior
- Auto-creation of results directory

### 5. Provider Switching (Medium Priority)
Tests both LLM providers produce valid results:
- OpenAI initialization and evaluation
- Anthropic initialization and evaluation
- Valid result structure from both providers

### 6. Transcription Components (Medium Priority)
Validates audio processing setup:
- Whisper model loading (with fallback)
- Translation flag settings
- Vision flag settings
- Supported format definitions
- Temporary directory creation

### 7. Edge Cases
Handles special scenarios:
- Empty transcripts
- Very short transcripts
- Special characters and Unicode
- Verbose mode
- Progress callbacks

## Test Markers

Tests are organized using pytest markers for easy filtering:

- **`integration`**: Slower tests with real dependencies (ffmpeg, yt-dlp, app startup)
- **`ui_smoke`**: Lightweight UI smoke tests for Streamlit
- **`provider_live`**: Opt-in tests requiring live API keys

### Running By Marker

```bash
# Unit tests only (fast)
pytest -m "not integration" -q

# Integration tests only
pytest -m integration -v

# UI smoke tests
pytest -m "integration and ui_smoke" -v

# Provider live tests (requires API keys)
export OPENAI_API_KEY=sk-...  # or ANTHROPIC_API_KEY
pytest -m "integration and provider_live" -v

# Exclude slow tests
pytest -m "not integration and not provider_live" -v
```

## Running Specific Test Categories

```bash
# Input validation tests
pytest tests/test_comprehensive.py -k "validate" -v

# Error handling tests
pytest tests/test_comprehensive.py -k "error or invalid or missing" -v

# Rubric format tests
pytest tests/test_comprehensive.py -k "rubric" -v

# Results persistence tests
pytest tests/test_comprehensive.py -k "save_results" -v

# Provider tests
pytest tests/test_comprehensive.py -k "provider" -v
```

## End-to-End Testing

For full pipeline validation with real API calls:

```bash
# Requires valid API key in environment
python tests/run_end_to_end_demo.py
```

This test:
- Uses real Whisper transcription
- Makes actual LLM API calls
- Validates complete evaluation flow
- Tests chunking behavior with large rubrics

## Test Development Guidelines

### When to Add Tests
- New features or functionality
- Bug fixes (add regression test)
- Edge cases discovered in production
- New rubric format or validation rules

### Test Best Practices
- Mock external dependencies (APIs) for unit tests
- Test both success and failure paths
- Use descriptive test names
- Include docstrings explaining test purpose
- Group related tests with comments
- Avoid brittle assertions (test structure, not exact values)

### Running Tests in CI/CD

```bash
# Fast unit tests only (no API calls)
pytest tests/test_evaluator.py tests/test_comprehensive.py -q

# With coverage report
pytest tests/ --cov=src --cov-report=html
```