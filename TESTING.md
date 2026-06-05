# Testing Guide

This document describes how to run tests for both the frontend and backend of the Databricks DE Certification Study Companion.

## Frontend Testing

### Setup

The frontend uses **Vitest** (Vite-native testing framework) with React Testing Library for component testing.

```bash
cd frontend
npm install  # Install dependencies including Vitest
```

### Running Tests

#### Run tests in watch mode
```bash
npm test
```

#### Run tests once (CI mode)
```bash
npm test -- --run
```

#### Run tests with UI
```bash
npm test:ui
```

#### Run tests with coverage
```bash
npm test:coverage
```

### Writing Tests

Tests should be in the `src/` directory with the `.test.jsx` or `.spec.jsx` extension.

Example test:
```javascript
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import MyComponent from './MyComponent'

describe('MyComponent', () => {
  it('renders the component', () => {
    render(<MyComponent />)
    expect(screen.getByText(/expected text/i)).toBeDefined()
  })
})
```

### Test Files

- `src/App.test.jsx` — Tests for the main App component

---

## Backend Testing

### Setup

The backend uses **pytest** with async test support via pytest-asyncio.

```bash
cd backend
uv sync --all-extras  # Install dependencies including pytest
```

### Running Tests

#### Run all tests
```bash
uv run pytest
```

#### Run tests with verbose output
```bash
uv run pytest -v
```

#### Run tests with coverage
```bash
uv run pytest --cov=app tests/
```

#### Run specific test file
```bash
uv run pytest tests/test_health.py
```

#### Run specific test function
```bash
uv run pytest tests/test_health.py::test_root_health_endpoint
```

### Writing Tests

Tests should be in the `tests/` directory with the `test_*.py` naming pattern.

Use the `client` fixture from `conftest.py` for testing FastAPI endpoints:

```python
def test_my_endpoint(client):
    response = client.get("/api/my-endpoint")
    assert response.status_code == 200
    assert response.json()["success"] is True
```

### Test Files

- `tests/test_health.py` — Tests for health check endpoints

---

## Running All Tests

### From project root

```bash
# Frontend tests
cd frontend && npm test -- --run && cd ..

# Backend tests
cd backend && uv run pytest && cd ..
```

Or create a script to run both:

```bash
#!/bin/bash
echo "Running frontend tests..."
cd frontend && npm test -- --run || exit 1
cd ..

echo "Running backend tests..."
cd backend && uv run pytest || exit 1
cd ..

echo "All tests passed!"
```

---

## Test Architecture

### Frontend

- **Framework**: Vitest
- **Component Testing**: React Testing Library
- **Environment**: jsdom (simulated DOM)
- **File Pattern**: `*.test.jsx`

### Backend

- **Framework**: pytest
- **Async Support**: pytest-asyncio
- **API Testing**: FastAPI TestClient (in conftest.py)
- **File Pattern**: `test_*.py`

---

## Best Practices

### Frontend

1. Test user interactions, not implementation details
2. Use semantic queries (`getByRole`, `getByLabelText`, etc.)
3. Avoid testing internal state; focus on visible outputs
4. Mock external dependencies (API calls, etc.)

### Backend

1. Test endpoints with TestClient, not direct function calls
2. Use fixtures for setup/teardown (already in conftest.py)
3. Test both success and error paths
4. Keep tests independent and idempotent

---

## Troubleshooting

### Frontend

**Tests not finding components:**
- Ensure Vitest config has correct content glob patterns
- Check that components export correctly

**ESM/CJS issues:**
- Vitest works best with `"type": "module"` in package.json (already set)

### Backend

**Async test failures:**
- Ensure pytest-asyncio is installed: `uv sync --all-extras`
- Use `async def test_...()` for async tests
- Mark async fixtures with `@pytest.fixture` (handled by asyncio_mode = "auto")

**Import errors:**
- Ensure you're in the backend directory or using `uv run`
- Check PYTHONPATH includes the project root

---

## CI/CD Integration

For continuous integration, use:

**Frontend:**
```bash
npm ci && npm test -- --run
```

**Backend:**
```bash
uv sync --all-extras && uv run pytest
```

Both commands use deterministic installs and run tests in non-interactive mode.
