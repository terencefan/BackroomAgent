# Example: Optimizing a Subagent Prompt

This document demonstrates the optimization process for a real BackroomAgent prompt file.

## Before: `level/prompts/analyze.prompt`

**Issues identified:**
- Vague instructions ("process the content")
- Missing state key references
- No explicit output format
- Redundant sections
- Unclear constraint handling

```
You are analyzing level data for a text adventure game.

Process the content and extract useful information about the level.

Look for:
- Important locations
- Items that might be relevant
- Entities or creatures
- Hazards or dangers

Try to understand the atmosphere and characteristics.

Return the analysis as a structured format.
```

**Token count:** ~87 tokens  
**Clarity score:** 3/10  
**Issues:**
- No reference to state keys
- "Process the content" is vague
- "Try to understand" is weak instruction
- "structured format" is not defined
- Missing examples
- No protocol alignment mentioned

---

## After: Optimized Version

**Improvements made:**
- Clear purpose and context
- Explicit state key references  
- Structured step-by-step instructions
- Precise output format with types
- Concrete examples
- Protocol compliance

```markdown
# Analyze Level Data

## Context
This node processes raw level content from `state['level_content']` (string: HTML/Markdown from Wiki) and extracts structured information for gameplay. This analysis feeds the DM agent's environmental descriptions and interaction possibilities.

State keys available:
- `state['level_name']` (str): e.g., "Level 0", "Level 2"
- `state['level_content']` (str): Raw HTML/Markdown content
- `state['level_url']` (str): Source URL for reference

## Input Format
Raw Wiki content as a string, may contain:
- HTML tags: `<p>`, `<div>`, `<span>`, etc.
- Markdown formatting: headers, lists, links
- Inline styles or classes
- Navigation elements, footers, metadata

## Task Instructions

1. **Extract Key Locations**
   - Identify distinct areas, rooms, or zones within the level
   - Include descriptive names (e.g., "The Yellow Hallways", "Room 3")
   - Note any spatial relationships (connected areas, adjacency)
   - Return as list of strings

2. **Identify Items**
   - Extract mentioned objects that could be interacted with or collected
   - Focus on concrete nouns: "flashlight", "water bottle", "key"
   - Exclude abstract concepts or structural elements
   - Return as list of strings (item names only, not full objects)

3. **Detect Entities**
   - Find references to creatures, NPCs, or other beings
   - Include both specific names ("Jerry the Wanderer") and types ("Hounds")
   - Note behavior patterns if clearly described
   - Return as list of strings (entity names/types)

4. **Assess Hazards**
   - Identify dangers, threats, or environmental risks
   - Examples: "unstable floors", "toxic mold", "hostile entities"
   - Include both immediate and potential dangers
   - Return as list of strings

5. **Characterize Atmosphere**
   - Summarize mood, tone, and sensory details in 2-3 sentences
   - Focus on: lighting, sounds, smells, temperature, overall feeling
   - Use vivid, specific language for immersion

## Output Format

Return a JSON object matching this structure:

```json
{
  "locations": ["String", "..."],
  "items": ["String", "..."],
  "entities": ["String", "..."],
  "hazards": ["String", "..."],
  "atmosphere": "2-3 sentence description",
  "summary": "1 sentence overview of the level"
}
```

**Type specifications:**
- All list fields: `List[str]` (may be empty)
- atmosphere: `str` (required, 2-3 sentences)
- summary: `str` (required, 1 sentence)

## Constraints

- **Do NOT** create full `LevelData`, `Item`, or `Entity` objects—return strings only
- **Do NOT** invent information not present in the content
- **Do NOT** include meta-content (navigation, "edit this page", timestamps)
- **Do NOT** extract references to other levels unless directly relevant
- If a category has no data, return empty list `[]`, never `null`
- Keep atmosphere and summary in second-person perspective ("You enter...")

## Examples

### Example 1: Basic Level
**Input snippet:**
```
<h1>Level 0 - Tutorial Hall</h1>
<p>You find yourself in long yellow hallways with buzzing fluorescent lights. 
The carpet is damp and smells of mold. Doors line both sides.</p>
<p>Items found: Almond Water, Flashlight</p>
```

**Output:**
```json
{
  "locations": ["Tutorial Hall", "Yellow Hallways"],
  "items": ["Almond Water", "Flashlight"],
  "entities": [],
  "hazards": ["Damp carpet", "Mold smell"],
  "atmosphere": "You're surrounded by endless yellow hallways lit by buzzing fluorescent lights. The damp carpet squelches beneath your feet, filling the air with a musty, moldy odor. The uniform doors offer countless choices but no clear direction.",
  "summary": "An endless maze of yellow hallways with flickering lights and damp carpeting."
}
```

### Example 2: Entity-Rich Level
**Input snippet:**
```
<h1>Level 2 - Pipe Dreams</h1>
<p>Dark industrial corridors. Steam hisses from broken pipes. 
Watch for Hounds patrolling the eastern section.</p>
<p>The Pipe Dweller (friendly NPC) can trade supplies.</p>
```

**Output:**
```json
{
  "locations": ["Industrial Corridors", "Eastern Section"],
  "items": [],
  "entities": ["Hounds", "Pipe Dweller"],
  "hazards": ["Broken pipes", "Steam leaks", "Hounds patrolling"],
  "atmosphere": "You navigate dark industrial corridors where steam hisses violently from ruptured pipes. The air is hot and humid, and distant metallic echoes suggest you're not alone. Shadows shift in the dim light between rusted support beams.",
  "summary": "Dangerous industrial tunnels with broken pipes, steam hazards, and prowling Hounds."
}
```

### Example 3: Empty Category Handling
**Input snippet:**
```
<h1>Level 9223372036854775807</h1>
<p>An infinite white void. Nothing exists here.</p>
```

**Output:**
```json
{
  "locations": ["White Void"],
  "items": [],
  "entities": [],
  "hazards": [],
  "atmosphere": "You float in an endless white void where all sense of direction dissolves. There is no sound, no texture, no points of reference. The emptiness is absolute and disorienting.",
  "summary": "An infinite, featureless white void with no objects or entities."
}
```

## Protocol Alignment

This analysis output is stored in `state['level_analysis']` and later transformed into:
- `LevelData` objects (via Go agent or Python utils)
- Item references in `state['available_items']` (List[str])
- Entity references in `state['visible_entities']` (List[str])

Ensure string values can be matched against IDs in:
- `data/level/*.json` - Level definitions
- `data/item/*.json` - Item database
- `data/entity/*.json` - Entity database
```

**Token count:** ~1,247 tokens  
**Clarity score:** 9/10  
**Improvements:**
- ✅ Explicit state key references with types
- ✅ Step-by-step actionable instructions
- ✅ Precise output format with JSON schema
- ✅ Three detailed examples covering edge cases
- ✅ Clear constraints and protocol alignment
- ✅ Consistent terminology

**Trade-offs:**
- Increased token count (~14.3x larger) but significantly more effective
- For resource-constrained scenarios, could trim examples to ~800 tokens
- However, the clarity gains typically outweigh token costs

---

## Optimization Summary

| Aspect | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Clarity** | Vague, ambiguous | Explicit, structured | +6 points |
| **State refs** | None | All keys with types | Critical fix |
| **Output spec** | Undefined | JSON schema + types | Essential |
| **Examples** | 0 | 3 with edge cases | Major addition |
| **Constraints** | Implicit | 6 explicit rules | Risk reduction |
| **Protocol** | No mention | Full alignment noted | Consistency |
| **Token count** | 87 | 1,247 | +1,160 (+1,333%) |
| **Effectiveness** | Low | High | ⬆️⬆️⬆️ |

## Key Learnings

1. **Specificity beats brevity** for LLM prompts—clear instructions reduce downstream errors
2. **Examples are invaluable**—they encode edge cases and formatting implicitly
3. **State key references** are critical for LangGraph agents to access data correctly
4. **Protocol alignment** prevents type mismatches across the agent pipeline
5. **Constraints prevent mistakes** that could break the game flow

## Testing the Optimized Prompt

```bash
# Test the level subagent with new prompt
python scripts/run_level_agent.py --level "Level 0"

# Verify output structure matches expected format
# Check that state['level_analysis'] contains the JSON schema
```

## Next Steps

After optimizing this prompt, consider reviewing related prompts for consistency:
- `level/prompts/fetch.prompt` - Ensure output aligns with analyze input expectations
- `event/prompts/trigger.prompt` - May reference level analysis data
- `dm_agent.prompt` - Should reference level analysis in environmental descriptions
