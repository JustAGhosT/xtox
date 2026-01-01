# Testing Guide

## Running Tests

### Backend Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=xtox --cov-report=html

# Run specific test file
pytest tests/test_md_to_pdf.py

# Run with verbose output
pytest -v
```

### Frontend Tests

```bash
cd frontend
yarn test

# Run with coverage
yarn test --coverage

# Run in watch mode
yarn test --watch
```

## Test Structure

### Backend Tests

- **Location:** `tests/` and `xtox/azure-functions/tests/`
- **Framework:** pytest
- **Coverage Target:** 80%+

**Test Categories:**
- Unit tests: Individual functions/classes
- Integration tests: API endpoints
- Service tests: Business logic

### Frontend Tests

- **Location:** `xtox/frontend/src/__tests__/`
- **Framework:** Jest + React Testing Library
- **Coverage Target:** 70%+

**Test Categories:**
- Component tests: UI components
- Integration tests: User workflows
- API client tests: HTTP requests

## Writing Tests

### Backend Example

```python
import pytest
from xtox.backend.services import LatexService

@pytest.mark.asyncio
async def test_latex_conversion_success():
    latex_content = r"\documentclass{article}\begin{document}Test\end{document}"
    result = await LatexService.process_latex_file(latex_content, "test", False)
    assert result.success is True
    assert result.errors == []
```

### Frontend Example

```javascript
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders file upload button', () => {
  render(<App />);
  const uploadButton = screen.getByRole('button', { name: /choose file/i });
  expect(uploadButton).toBeInTheDocument();
});
```

## Test Data

- Test files: `test_data/`
- Fixtures: `tests/fixtures/`
- Mocks: Use unittest.mock or jest.mock

## Continuous Integration

Tests run automatically on:
- Pull requests
- Pushes to main branch
- Scheduled nightly runs

## Coverage Reports

- Backend: `htmlcov/index.html`
- Frontend: `coverage/lcov-report/index.html`

## Best Practices

1. **Test Isolation:** Each test should be independent
2. **Clear Names:** Test names should describe what they test
3. **Arrange-Act-Assert:** Structure tests clearly
4. **Mock External Dependencies:** Don't rely on external services
5. **Test Edge Cases:** Include error scenarios
6. **Keep Tests Fast:** Avoid slow operations in unit tests

## Integration Testing

For integration tests that require external services:

```bash
# Start test services
docker-compose -f docker-compose.test.yml up -d

# Run integration tests
pytest tests/integration/

# Cleanup
docker-compose -f docker-compose.test.yml down
```

