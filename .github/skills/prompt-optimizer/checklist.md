# Prompt Optimization Checklist

Quick reference for evaluating and improving prompt files.

## Pre-Analysis

- [ ] Identify the node/agent this prompt serves
- [ ] Locate corresponding `state.py` to understand available keys
- [ ] Check `PROTOCOL.md` for relevant data structures
- [ ] Review related prompts for consistency
- [ ] Note current prompt token count

## Structure Review

- [ ] **Purpose**: Does the prompt clearly state its goal in the first line?
- [ ] **Context**: Is the execution context (when/where it runs) explained?
- [ ] **Sections**: Are logical sections clearly delineated with headers?
- [ ] **Flow**: Do instructions follow a logical sequence?
- [ ] **Formatting**: Are bullets, numbers, code blocks used appropriately?

## Instruction Quality

- [ ] **Specificity**: Are all instructions concrete and actionable?
- [ ] **Clarity**: Can each instruction be understood without ambiguity?
- [ ] **Completeness**: Do instructions cover all required tasks?
- [ ] **Imperative**: Are instructions in command form ("Extract", "Generate")?
- [ ] **Consistency**: Is terminology used consistently throughout?

## Input/Output Specs

- [ ] **Input format**: Is the expected input explicitly described?
- [ ] **Input types**: Are data types and structures specified?
- [ ] **Output format**: Is the output structure explicitly defined?
- [ ] **Output types**: Are return types clearly specified?
- [ ] **Examples**: Are input/output examples provided?

## State Management (LangGraph)

- [ ] **Read keys**: Are all accessed state keys listed with types?
- [ ] **Write keys**: Are produced state keys documented?
- [ ] **Key accuracy**: Do key names match `state.py` definitions?
- [ ] **Type alignment**: Do types match protocol definitions?
- [ ] **None handling**: Is nullable state handled appropriately?

## Error Prevention

- [ ] **Constraints**: Are all limitations explicitly stated?
- [ ] **Edge cases**: Are unusual scenarios addressed?
- [ ] **Prohibitions**: Is there a clear "do NOT" section?
- [ ] **Defaults**: Are default behaviors specified?
- [ ] **Validation**: Are validation rules included?

## Examples & Documentation

- [ ] **Example count**: Are there 2-3 examples minimum?
- [ ] **Example variety**: Do examples cover normal and edge cases?
- [ ] **Example accuracy**: Are all examples valid and tested?
- [ ] **Comments**: Are complex sections explained?
- [ ] **References**: Are related files/docs linked?

## Protocol Compliance

- [ ] **Data structures**: Do references match `PROTOCOL.md`?
- [ ] **Item/Entity refs**: Are they string lists (not full objects)?
- [ ] **Event structure**: Does it match the event schema?
- [ ] **Level data**: Does it align with Go agent output?
- [ ] **Type consistency**: Are types consistent across Python/TS/Go?

## Optimization Targets

- [ ] **Redundancy**: Remove duplicate instructions
- [ ] **Wordiness**: Simplify without losing clarity
- [ ] **Vagueness**: Replace fuzzy terms with specific ones
- [ ] **Irrelevance**: Remove unrelated context
- [ ] **Token efficiency**: Aim for 20-30% reduction if verbose

## Post-Optimization

- [ ] Test with relevant `run_*.py` script
- [ ] Verify output matches expected format
- [ ] Check for regressions in agent behavior
- [ ] Update related prompts for consistency
- [ ] Document changes in commit message

## Quality Metrics

Rate each aspect from 1-10:

| Aspect | Score | Notes |
|--------|-------|-------|
| Clarity |  /10 | Are instructions unambiguous? |
| Completeness |  /10 | Are all tasks covered? |
| Specificity |  /10 | Are instructions concrete? |
| Efficiency |  /10 | Is it concise without losing clarity? |
| Consistency |  /10 | Does terminology align with protocol? |

**Overall Score:** ___/50

- **40-50**: Excellent prompt, minor tweaks only
- **30-39**: Good prompt, some optimization opportunities
- **20-29**: Fair prompt, needs significant improvement
- **<20**: Poor prompt, requires major rewrite

## Common Anti-Patterns to Avoid

❌ **Vague actions**: "handle", "process", "deal with", "manage"  
✅ **Specific actions**: "extract", "parse", "filter", "transform"

❌ **Hedge words**: "might", "could", "possibly", "try to"  
✅ **Definitive**: "will", "must", "always", "never"

❌ **Undefined formats**: "return as structured data"  
✅ **Explicit formats**: "return JSON object with keys: {}"

❌ **Missing types**: "state['items']"  
✅ **Typed references**: "state['items'] (List[str])"

❌ **No examples**: Instructions only  
✅ **With examples**: Instructions + 2-3 examples

❌ **Nested complexity**: Deeply nested sections  
✅ **Flat structure**: Clear headers, scannable

❌ **Assumptions**: Expecting model to infer behavior  
✅ **Explicit**: State all expectations clearly

## Quick Optimization Recipe

1. **Add headers** for major sections
2. **Number steps** in task instructions
3. **Define output** with JSON schema or example
4. **Add 2 examples** (normal + edge case)
5. **List constraints** as bullets in "Do NOT" section
6. **Reference state keys** with types in context section
7. **Remove hedging** and vague language
8. **Test immediately** with run script

## Template

```markdown
# [Clear Purpose Statement]

## Context
Node: [node_name] in [subagent/main agent]
Triggered when: [condition]
State keys available:
- `state['key']` (Type): description

## Input Format
[Explicit specification]

## Task Instructions
1. [Action 1]: Description with specifics
2. [Action 2]: Description with specifics
3. [Action 3]: Description with specifics

## Output Format
```json
{
  "field": "type and example"
}
```

## Constraints
- [Must/Must not requirement]
- [Edge case handling]
- [Validation rule]

## Examples
### Example 1: [Normal Case]
Input: ...
Output: ...

### Example 2: [Edge Case]
Input: ...
Output: ...

## Protocol Alignment
[How this output is used downstream]
[References to protocol definitions]
```
