# Contributing to Ask IRA

## Development Setup

```bash
git clone https://github.com/your-org/ask-ira.git
cd ask-ira
pip install -e ".[dev,mcp,eval]"
cp .env.example .env
# Edit .env with your API keys
```

## Lint

```bash
ruff check src/ tests/ scripts/
```

## Test

```bash
pytest tests/ -v
pytest tests/ -v --cov=src --cov-report=term
```

## E2E Smoke Test

```bash
python test_e2e_smoke.py
```

## Adding an MCP Server

1. Create `src/mcp_servers/your_server.py` inheriting from `MCPServer`
2. Implement `async def handle(self, request: MCPRequest) -> MCPResponse`
3. Register in `src/mcp_servers/registry.py`
4. Add seed data to `data/loader.py` if needed

## Adding an Agent

1. Create `src/agents/your_agent.py` with the agent class
2. Add state fields to `src/agents/state.py`
3. Add node function to `src/agents/graph.py`
4. Wire edges in the graph builder
5. Update `src/agents/supervisor.py` for routing

## Adding Seed Data

1. Create `data/your_data.json` with the data
2. Add loader function in `data/loader.py`
3. Update `data/loader.load_all_seed_data()` to include it
4. Reference from MCP servers or seed script

## Commit Guidelines

- Use conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`
- Keep commits focused on single logical change
- Reference issues in commit body

## Pull Request Process

1. Branch from `main`
2. Add tests for new functionality
3. Ensure lint passes (`ruff check src/`)
4. Ensure all tests pass (`pytest tests/`)
5. Update documentation if needed
6. Create PR with description of changes

## Code of Conduct

Be respectful, constructive, and inclusive. Focus on the code, not the person.
