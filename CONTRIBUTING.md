# Contributing to DynaLinks

Thank you for your interest in contributing to DynaLinks! We welcome contributions from the community.

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 12+
- Redis 6+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- [just](https://github.com/casey/just) command runner (optional but recommended)

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/dynalinks.git
   cd dynalinks
   ```

2. **Set up development environment**
   ```bash
   # Using just (recommended)
   just setup
   
   # Or manually
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your local configuration
   ```

4. **Start local services**
   ```bash
   # Start PostgreSQL and Redis with Docker
   just docker-up
   
   # Initialize database schema
   just db-init
   ```

5. **Run the application**
   ```bash
   just run
   ```

6. **Run tests**
   ```bash
   just test
   ```

## Development Workflow

### Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, readable code
   - Follow existing code style and patterns
   - Add type hints where appropriate
   - Update documentation if needed

3. **Test your changes**
   ```bash
   # Run tests
   just test
   
   # Test manually
   curl -X POST "http://localhost:8000/api/v1/links/" \
     -H "Content-Type: application/json" \
     -d '{"fallback_url": "https://example.com"}'
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

### Code Style

- **Python**: Follow PEP 8 guidelines
- **Type hints**: Use type hints for function parameters and return values
- **Docstrings**: Add docstrings for public functions and classes
- **Error handling**: Use appropriate HTTP status codes and error messages
- **Async/await**: Use async patterns consistently

### Commit Messages

Use conventional commit format:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for test additions/changes
- `refactor:` for code refactoring
- `chore:` for maintenance tasks

## Types of Contributions

### Bug Reports

When reporting bugs, please include:
- Python version and OS
- Steps to reproduce the issue
- Expected vs actual behavior
- Error messages or logs
- Minimal code example if applicable

### Feature Requests

For new features:
- Describe the use case and motivation
- Provide examples of how it would be used
- Consider if it fits the project's scope and goals
- Check if similar functionality already exists

### Code Contributions

We welcome:
- Bug fixes
- New features (discuss in an issue first for larger features)
- Performance improvements
- Documentation improvements
- Test coverage improvements

### Documentation

Help improve:
- README and setup instructions
- API documentation
- Deployment guides
- Code comments and docstrings
- Examples and tutorials

## Testing

### Running Tests

```bash
# Run all tests
just test

# Run with coverage
pytest --cov=app

# Run specific tests
pytest tests/test_main.py::test_create_link -v
```

### Writing Tests

- Add tests for new features
- Test both success and error cases
- Use meaningful test names
- Mock external dependencies
- Aim for good test coverage

### Test Structure

```python
import pytest
from httpx import AsyncClient

@pytest.mark.anyio
async def test_create_link(client: AsyncClient):
    response = await client.post("/api/v1/links/", json={
        "fallback_url": "https://example.com"
    })
    assert response.status_code == 200
    data = response.json()
    assert "short_code" in data
```

## Deployment Testing

Test your changes work in different environments:

1. **Docker deployment**
   ```bash
   docker build -f Dockerfile.prod -t dynalinks:test .
   docker-compose -f docker-compose.yml up
   ```

2. **Kubernetes deployment** (if applicable)
   ```bash
   # Update image in k8s-manifests.yaml
   kubectl apply -f k8s-manifests.yaml
   ```

## Pull Request Process

1. **Update documentation** if your changes affect the API or deployment
2. **Add tests** for new functionality
3. **Ensure all tests pass**
4. **Update CHANGELOG.md** if adding significant features
5. **Create pull request** with:
   - Clear title and description
   - Reference related issues
   - List of changes made
   - Testing instructions

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Manual testing completed
- [ ] Documentation updated

## Related Issues
Closes #123
```

## Code Review

All submissions require review. We look for:
- Code quality and readability
- Proper error handling
- Security considerations
- Performance impact
- Test coverage
- Documentation completeness

## Community Guidelines

- Be respectful and inclusive
- Help others learn and grow
- Focus on constructive feedback
- Follow the code of conduct
- Ask questions if you're unsure

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Issues**: Create a GitHub Issue
- **Security**: Follow our Security Policy
- **Chat**: [Future: Discord/Slack link]

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes for significant contributions
- Given credit in documentation

Thank you for contributing to DynaLinks! 🚀
