---
name: prompt-optimizer
description: Analyzes and optimizes prompt files for LLM agents. Use this skill when working with .prompt files, improving agent instructions, enhancing prompt clarity, or debugging agent behavior. Helps with prompt engineering, structure optimization, and LangGraph agent prompt management.
---

# Prompt Optimizer Skill

This skill helps you analyze, optimize, and improve prompt files for LLM-based agents, with specific support for LangGraph agent architectures.

## When to Use This Skill

Use this skill when you need to:
- Analyze existing `.prompt` files in `backroom_agent/prompts/` or subagent prompt directories
- Improve prompt clarity, structure, or effectiveness
- Debug agent behavior by examining and refining prompts
- Create new prompts following best practices
- Ensure prompts are properly structured for LangGraph nodes
- Optimize token usage while maintaining instruction quality
- Validate prompt consistency across subagents

## Optimization Framework

### 1. Prompt Analysis Checklist

When analyzing a prompt file, evaluate:

**Clarity & Structure**
- [ ] Clear purpose statement at the beginning
- [ ] Logical section organization with headers
- [ ] Unambiguous instructions (no vague terms)
- [ ] Proper use of formatting (bullets, numbering, code blocks)

**Specificity**
- [ ] Concrete examples provided where needed
- [ ] Clear input/output format specifications
- [ ] Explicit constraints and boundaries
- [ ] Specific terminology definitions

**Completeness**
- [ ] All required context provided
- [ ] Edge cases addressed
- [ ] Error handling instructions included
- [ ] Output format fully specified

**Efficiency**
- [ ] No redundant instructions
- [ ] Concise language without losing clarity
- [ ] Relevant context only (no extraneous information)
- [ ] Optimal length for the task complexity

**Agent-Specific (LangGraph)**
- [ ] State key references are accurate
- [ ] Node-specific instructions are clear
- [ ] Context passing between nodes is explicit
- [ ] Type expectations match protocol definitions

### 2. Common Issues to Fix

**Vague Instructions**
- ❌ "Process the data appropriately"
- ✅ "Extract entity names from the text using Named Entity Recognition, returning a list of strings"

**Missing Context**
- ❌ "Generate a response"
- ✅ "Generate a response in second-person perspective (you/your), incorporating the player's current location from state['current_location']"

**Ambiguous Output Format**
- ❌ "Return the results"
- ✅ "Return a JSON object with keys: 'success' (boolean), 'message' (string), 'data' (list of dicts)"

**Redundant Information**
- ❌ Repeating the same instruction in multiple sections
- ✅ State once clearly, reference if needed later

**Over-complicated Structure**
- ❌ Deeply nested sections with overlapping content
- ✅ Flat, scannable structure with clear headers

### 3. Best Practices

#### Structure Template
```
# [Primary Goal/Purpose]

## Context
[Brief description of when/how this prompt is used]
[Reference to state keys available]

## Input Format
[Exact specification of expected inputs]

## Task Instructions
1. [Step-by-step numbered instructions]
2. [Each step should be actionable]
3. [Use imperative mood: "Extract", "Generate", "Return"]

## Output Format
[Exact specification with examples]

## Constraints
- [Explicit limitations]
- [What NOT to do]

## Examples
### Example 1: [Scenario]
Input: ...
Output: ...

### Example 2: [Edge Case]
Input: ...
Output: ...
```

#### Language Guidelines
- **Use imperative mood**: "Extract entities" not "You should extract entities"
- **Be specific**: "Return 3-5 suggestions" not "Return some suggestions"
- **Avoid hedge words**: "might", "could", "possibly", "maybe"
- **Use consistent terminology**: Define terms once, use them consistently
- **Provide examples**: Show, don't just tell

#### State Key References (for LangGraph agents)
When referencing state keys in prompts:
- Use exact key names from `state.py` files
- Include type information: `state['player_inventory'] (List[Item])`
- Note if keys might be None/empty: `state['active_events'] (List[Event], may be empty)`
- Group references by the node that produces them

### 4. Optimization Process

**Step 1: Understand the Node's Role**
- What is the node's single responsibility?
- What state does it read?
- What state does it produce?
- How does it fit in the graph flow?

**Step 2: Analyze Current Prompt**
- Run through the analysis checklist above
- Identify specific issues using the common issues list
- Note token count and complexity

**Step 3: Draft Improvements**
- Restructure for clarity using the template
- Simplify language while adding specificity
- Add missing examples or constraints
- Remove redundancy

**Step 4: Validate**
- Check alignment with `state.py` definitions
- Ensure protocol compliance (refer to `PROTOCOL.md`)
- Verify examples are accurate
- Confirm output format matches expected types

**Step 5: Document Changes**
- List what was improved and why
- Note any assumptions or decisions made
- Suggest related prompts to review for consistency

## Working with BackroomAgent Prompts

For the BackroomAgent project specifically:

### Directory Structure
```
backroom_agent/
├── prompts/
│   ├── dm_agent.prompt              # Main DM agent system prompt
│   ├── game_context_to_script.prompt
│   └── init_summary.prompt
└── subagents/
    ├── event/
    │   └── prompts/
    │       ├── analyze.prompt
    │       ├── execute.prompt
    │       └── trigger.prompt
    ├── level/
    │   └── prompts/
    │       ├── analyze.prompt
    │       └── fetch.prompt
    └── suggestion/
        └── prompts/
            ├── analyze.prompt
            └── generate.prompt
```

### Protocol Alignment
Always cross-reference prompts with:
- `PROTOCOL.md` - Source of truth for data structures
- `backroom_agent/protocol.py` - Pydantic models
- `backroom_agent/state.py` - Main agent state
- `backroom_agent/subagents/*/state.py` - Subagent states

### Consistency Rules
- All prompts should use consistent terminology from the protocol
- Item/Entity references should align with the "lists of strings" pattern
- Event triggers should reference the event schema structure
- Level data should match the Go agent's output structure

## Example Optimization

See [example-optimization.md](./example-optimization.md) for a detailed before/after example of optimizing a prompt file.

## Tips

- **Test prompts**: Use `scripts/run_*.py` to test agent behavior after changes
- **Version control**: Keep the original prompt commented out temporarily
- **Incremental changes**: Optimize one section at a time and test
- **Context awareness**: Consider what the model has already seen before this prompt
- **Token efficiency**: Aim for 20-30% reduction without losing clarity
- **Readability**: A human should be able to understand the prompt without context

## Related Resources

- [PROTOCOL.md](/PROTOCOL.md) - Data structure definitions
- [Subagent README](/backroom_agent/subagents/README.md) - Subagent architecture
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/) - Graph concepts
