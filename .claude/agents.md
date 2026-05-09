# Agent Development Standards

Rules for building and modifying LangGraph agents in `src/agents/`.

## Agent Structure

Every agent follows this pattern:

```python
from src.utils.llm import get_llm

class MyNewAgent:
    def __init__(self, ...):
        self.llm = get_llm(temperature=0.0)

    async def my_method(self, state: AgentState) -> dict:
        # 1. Extract relevant data from state
        # 2. Call LLM or execute logic
        # 3. Return dict with new state fields + "next" routing key
        return {"result": "...", "next": "next_node"}
```

## Node Registration

Every agent node must be registered in `src/agents/graph.py`:

```python
async def my_node(state: AgentState) -> dict:
    agent = MyNewAgent()
    return await agent.my_method(state)

builder.add_node("my_node", my_node)
builder.add_edge("previous_node", "my_node")
```

## State Schema Rules

1. All state fields must be defined in `src/agents/state.py`
2. Use `TypedDict` with `Annotated[list, add_messages]` for message accumulation
3. The `next` field must be a `Literal` union of all valid target nodes + `__end__`
4. Optional fields must have `| None` type annotation

```python
class AgentState(TypedDict):
    query: str
    messages: Annotated[list[AnyMessage], add_messages]
    next: Literal["node_a", "node_b", "__end__"] | None
    my_custom_field: str | None
```

## Agentic Pattern Reference

| Pattern | File | Implementation |
|---------|------|----------------|
| **Reflection** | `critic.py` | LLM reviews prior output, loops for N iterations |
| **Fan-out/fan-in** | `researcher.py` | `asyncio.gather()` across MCP servers |
| **Domain expert** | `portfolio_manager.py` | Specialized LLM prompt + deterministic allocation models |
| **Compliance gate** | `compliance.py` | Regex + LLM review, blocks non-compliant reports |
| **Human-in-the-loop** | `graph.py` | Optional node before `guard_output`, waits for approval |

## Routing Rules

1. The `next` field determines the next node in the graph
2. Use `builder.add_conditional_edges()` for branching logic
3. Reflection loops must track `iteration` count to prevent infinite loops

## Prompt Template Patterns

1. Always use `SystemMessage` + `HumanMessage` pattern
2. Specify output format explicitly (JSON structure, field descriptions)
3. Include examples for complex formats (few-shot)
4. Temperature: 0.0 for analytical agents, 0.1-0.2 for creative agents

```python
result = await self.llm.ainvoke([
    ("system", "You are a precise analyst. Output only valid JSON."),
    ("human", f"Analyze: {query}\n\nOutput: {{'score': float, 'reasoning': str}}"),
])
```
