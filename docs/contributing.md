# Contributing

Thank you for your interest in contributing to `flow-it-api`!

## Development Setup

1. Clone the repository.
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .[dev]
   ```
3. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Running Tests

Run the test suite with coverage:
```bash
pytest --cov=src --cov-report=term-missing
```

## Documentation

To preview the documentation locally:
```bash
mkdocs serve
```

## Submitting Changes

1. Create a new branch for your feature or bugfix.
2. Ensure all tests pass and linting is clean.
3. Submit a Pull Request to the `main` branch.
