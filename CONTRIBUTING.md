# Contributing to LogiSwarm

Thank you for your interest in contributing to LogiSwarm! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker and Docker Compose
- PostgreSQL 15+ (for local development)
- Redis 7+ (for local development)

### Getting Started

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/logiswarm.git
   cd logiswarm
   ```

2. Set up the backend:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

3. Set up the frontend:
   ```bash
   cd frontend
   npm install
   ```

4. Copy the environment template:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Start development services:
   ```bash
   docker-compose up -d postgres redis
   ```

## Development Workflow

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `refactor/description` - Code refactoring
- `docs/description` - Documentation updates

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Tests
- `chore:` - Maintenance tasks

Example: `feat(agents): add South Asia geo-agent`

### Code Style

#### Python (Backend)

- Use type hints for all function parameters and return types
- Follow PEP 8 style guide
- Use docstrings for public functions
- Maximum line length: 100 characters

Run linters before committing:
```bash
cd backend
ruff check app
mypy app --ignore-missing-imports
```

#### TypeScript/Vue (Frontend)

- Use Vue 3 Composition API
- Use TypeScript types
- CSS variables only (no hardcoded colors)
- Lazy-load route components

Run linters before committing:
```bash
cd frontend
npm run lint
npm run type-check
```

### Testing

#### Backend Tests

```bash
cd backend
pytest --cov=app --cov-report=html
```

Coverage should be at least 70%.

#### Frontend Tests

```bash
cd frontend
npm run test
```

### Pull Request Process

1. Create a feature branch from `main`
2. Make your changes, following code style guidelines
3. Add/update tests as needed
4. Ensure all tests pass
5. Update documentation if needed
6. Submit PR with description of changes

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] Commit messages follow conventional commits
- [ ] No hardcoded secrets or credentials

## Project Structure

```
logiswarm/
├── backend/
│   ├── app/
│   │   ├── actions/      # Action handlers (TMS, Slack, Email)
│   │   ├── agents/      # Geo-agent implementations
│   │   ├── api/         # FastAPI routes
│   │   ├── bus/         # Redis pub/sub
│   │   ├── db/          # Database models
│   │   ├── feeds/       # Data connectors
│   │   └── orchestrator/  # Swarm coordination
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/  # Vue components
│   │   ├── views/       # Page views
│   │   ├── stores/       # Pinia stores
│   │   └── router/       # Vue Router config
│   └── package.json
└── docker-compose.yml
```

## Questions?

Open an issue with the `question` label, or reach out to the maintainers.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.