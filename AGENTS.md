# AGENTS.md

## General

- Keep changes small and focused
- Follow existing patterns
- Do not introduce new tools or dependencies without justification
- Update tests when behavior changes
- Prefer readability over cleverness
- Avoid breaking backward compatibility unless explicitly required
- All code must be deterministic and reproducible

---

## Security & Safety

- Never commit secrets, API keys, tokens, or credentials
- Use environment variables for configuration
- Validate all external inputs
- Avoid unsafe functions (`eval`, `exec`, shell=True)
- Sanitize user input for APIs and databases
- Follow principle of least privilege

---

## Python Agents

### Tooling

- **Package manager:** `uv`
- **Formatter:** `black` (default settings)
- **Linter:** `ruff` or `flake8` (if present in project)
- **Type checker:** `mypy`

### Code Rules

- Use **type hints** for all code
- Use the standard `logging` module (no `print()`)
- Prefer explicit error handling
- Avoid broad `except Exception`
- Functions must be small and single-purpose
- Use dataclasses or pydantic models for structured data

### Logging

- Use structured logs (JSON or consistent format)
- Log at appropriate levels: debug, info, warning, error, critical
- Do not log secrets or personal data

### Testing

- Use `pytest`
- Each feature must include tests
- Tests must be deterministic
- Prefer unit tests over integration tests unless required
- Target ≥80% coverage when possible

---

## Frontend Agents

### Tooling

- **Package manager:** `pnpm`
- **Build tool:** `Vite`
- **UI:** `shadcn/ui`
- **Formatter:** `prettier`

### Language & Style

- **TypeScript:** `strict: true`
- No `any` unless explicitly justified
- Single quotes
- No semicolons
- Prefer interfaces and union types
- Avoid implicit `any`

### Patterns

- Functional components and hooks only
- Prefer functional and immutable patterns
- Avoid class-based React components
- Use controlled components for forms
- Prefer composition over inheritance

### State & Data

- Avoid global state unless required
- Handle loading and error states explicitly
- No silent failures

---

## API & Schema Conventions

- All APIs must be versioned
- Use OpenAPI / schema definitions if applicable
- Validate request and response payloads
- Return meaningful error messages
- Never expose stack traces to frontend

---

## Documentation

- Public functions must have docstrings
- Complex logic must be commented
- README must be updated if behavior changes
- Provide usage examples when adding features

---

## Performance & Resource Usage

- Avoid unnecessary loops and API calls
- Cache expensive operations where applicable
- Do not block event loops
- Avoid memory leaks and unbounded data growth

---

## Environment & Configuration

- Use `.env` for configuration
- Never hardcode environment-specific values
- Provide `.env.example` for required variables
- Config must be validated at startup

---

## Version Control

- Clear, descriptive commit messages
- Do not commit secrets or build artifacts
- Use feature branches
- Squash commits when merging
- Reference issues or tickets when applicable

---

## CI / Quality Gates

- All tests must pass before merge
- Type checks must pass
- Build must succeed

---

## AI Agent Behavior

- Do not hallucinate APIs or libraries
- Ask for clarification if requirements are ambiguous
- Never remove functionality unless instructed
- Preserve backward compatibility
- Prefer minimal diffs
