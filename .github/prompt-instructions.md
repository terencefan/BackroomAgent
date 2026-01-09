# Prompt Engineering Guidelines for `.prompt` Files

本文档为 `BackroomAgent` 项目中所有 `.prompt` 文件的编写、维护和优化提供标准化指南。

## 目录
- [核心原则](#核心原则)
- [标准结构](#标准结构)
- [文件命名与位置](#文件命名与位置)
- [内容规范](#内容规范)
- [质量检查清单](#质量检查清单)
- [常见反模式](#常见反模式)

---

## 核心原则

### 1. 分离关注点 (Separation of Concerns)
- **绝对禁止**在 Python 代码中硬编码 Prompt 文本
- 所有 Prompt 必须存储为独立的 `.prompt` 文件
- 使用 `load_prompt()` 或 `_load_system_prompt()` 工具动态加载

### 2. 结构化优于自由文本
- 使用明确的分段结构（`# Role`, `## Goal`, `### Rules`）
- 优先使用列表、表格、JSON Schema 等结构化格式
- 避免大段落的散文式描述

### 3. 机器可读性
- 输出格式必须**明确约束**（JSON/XML/特定文本格式）
- 必须提供完整的 Schema 定义或示例
- 使用 `format_rules_generator.prompt` 生成严格的格式约束

---

## 标准结构

对于主 Agent (`backroom_agent`) 的复杂任务，**必须**使用 XML 标签风格的结构。这种结构能更好地被大模型解析，防止指令混淆。

```xml
<system_instruction>
  <role>
  [AI 的身份定位：专家类型、职责范围]
  </role>

  <responsibilities>
  [核心任务目标与职责列表]
  1. ...
  2. ...
  </responsibilities>

  <rules>
    <rule_group_name>
      [具体的处理规则或游戏机制]
      <sub_rule>...</sub_rule>
    </rule_group_name>
  </rules>

  <output_requirements>
    <format_constraint>
      [CRITICAL: 强制性格式要求，如无 Markdown，纯 JSON]
    </format_constraint>
    
    <json_schema>
      [JSON 结构模板]
    </json_schema>

    <field_details>
      [字段详细说明与填充逻辑]
    </field_details>
  </output_requirements>

  <examples>
    <input_example>...</input_example>
    <output_example>...</output_example>
  </examples>
</system_instruction>
```

### 简单任务替代方案 (Markdown)
对于 Go Agent 模板或简单的单一任务 Prompt，可以使用 Markdown 标题结构：

```markdown
# Role
...
# Goal
...
# Processing Rules
...
```

### 结构说明

| 标签/章节 | 必需性 | 用途 |
|---|---|---|
| `<role>` | **必需** | 定义身份与核心目标 |
| `<responsibilities>` | 推荐 | 列举具体责任清单 |
| `<rules>` | **必需** | 包含所有业务逻辑和判定规则 |
| `<output_requirements>` | **必需** | 定义输出格式、Schema 和约束 |
| `<examples>` | 推荐 | 提供 Few-Shot 示例 |

---

## 文件命名与位置

### 命名规范
- **描述性**：使用动词+名词结构（如 `extract_items.prompt`, `generate_json.prompt`）
- **小写+下划线**：遵循 `snake_case` 命名（不使用 camelCase 或 kebab-case）
- **避免缩写**：优先完整单词（`suggestion_agent.prompt` > `sugg_agt.prompt`）

### 目录结构
```
backroom_agent/
├── prompts/                      # 主 Agent 的 Prompts
│   ├── dm_agent.prompt           # DM 主控逻辑
│   ├── init_summary.prompt       # 初始化摘要
│   └── game_context_to_script.prompt
│
└── subagents/
    ├── level/
    │   └── prompts/              # Level Agent 专属 Prompts
    │       ├── generate_json.prompt
    │       ├── extract_entities.prompt
    │       └── extract_items.prompt
    │
    ├── event/
    │   └── prompts/
    │       └── event_agent.prompt
    │
    └── suggestion/
        └── prompts/
            └── suggestion_agent.prompt

go_agent/
└── agent/
    └── prompt/                   # Go Agent 专属 Prompts
        ├── generate_json.prompt
        ├── extract_entities.prompt
        └── ex<role>`)
✅ **Good (XML Style)**:
```xml
<role>
你是在“后室（The Backrooms）”世界观下的生存恐怖文字冒险游戏的地下城主（DM）。
你的目标是为玩家提供身临其境、充满悬念且机制完善的游戏体验。
</role>
```

❌ **Bad**:
```markdown
# Role
你是一个帮助用户的 AI 助手。
```

**原则**:
- 使用 XML 标签包裹
- 具体化领域专业知识
- 明确核心目标

---

### 2. 职责描述 (`<responsibilities>`)
✅ **Good**:
```xml
<responsibilities>
1. **叙事描述**：使用第二人称（“你...”），强调感官细节。
2. **游戏逻辑**：根据游戏状态可靠地仲裁玩家行动。
3. **节奏控制**：在探索、紧张感和遭遇战之间保持平衡。
</responsibilities>
```

---

### 3. 处理规则 (`<rules>`)

#### 规则结构
```xml
<rules>
  <vitals>
    <hp>如果 HP 降至 0，玩家死亡。描述一个可怕的死亡场景。</hp>
    <sanity>
      <description>核心叙事指标，遭遇实体时降低。</description>
      <levels>
        <high>描述应客观、冷静。</high>
        <low>描述幻觉，环境逐渐扭曲。</low>
      </levels>
    </sanity>
  </vitals>

  <mechanic_action_resolution>
    <goal>所有行动必须构建概率事件表 (Event Table)。</goal>
    <dice_types>
      <d20>标准互动、战斗。</d20>
      <d100>极罕见事件。</d100>
    </dice_types>
  </mechanic_action_resolution>
</rules>
```

#### 关键要素
- **层级化**：使用嵌套标签组织复杂规则
- **语义化**：标签名称应反映规则主题（如 `<vitals>`, `<sanity>`）

---

### 4. 输出格式 (`<output_requirements>`)

#### 强制性约束
```xml
<output_requirements>
  <format_constraint>
    **CRITICAL**: 输出必须是**纯 JSON 文本**。无 Markdown 标记 (即不要 ```json)，无额外文本。
  </format_constraint>

  <json_schema>
  {
    "message": "string",
    "event": "object"
  }
  </json_schema>
</output_requirements># Output Structure
```typescript
{
  level_id: string;                    // 例如 "Level 0"
  atmosphere: {
    visuals: string[];                 // 视觉元素列表
    audio: string[];                   // 听觉元素
  };
  factions?: Array<{                   // 可选字段
    name: string;
    alignment: "友善" | "中立" | "敌对";
  }>;
}
```
```

---

### 5. 模板变量处理

#### Python Prompts (使用 Jinja2/f-string 风格)
```markdown
# Input Context
玩家输入: {user_message}
当前层级: {current_level}
生命值: {vitals.hp}
```

加载方式:
```python
from backroom_agent.utils.common import load_prompt

prompt_template = load_prompt("dm_agent")
prompt = prompt_template.format(
    user_message=msg,
    current_level=state["level"],
    vitals=state["vitals"]
)
```

#### Go Prompts (使用 Go Template 风格)
```markdown
# Input Text
{{.InputText}}

# Current Level
层级 ID: {{.LevelID}}
危险等级: {{.DangerClass}}
```

加载方式:
```go
tmpl := template.Must(template.ParseFiles("prompt/generate_json.prompt"))
var buf bytes.Buffer
tmpl.Execute(&buf, map[string]interface{}{
    "InputText": rawHTML,
    "LevelID": "Level 0",
})
```

---

## 质量检查清单

在提交 Prompt 文件前，确保通过以下检查：

### ✅ 结构完整性
- [ ] 包含 `# Role`, `# Goal`, `# Processing Rules`, `# Output Format`
- [ ] 每个规则都有编号和清晰的标题
- [ ] 输出格式有明确的 Schema 或结构定义

### ✅ 逻辑一致性
- [ ] 输入/输出数据流逻辑清晰
- [ ] 规则之间无矛盾（如同时要求"必须填充"和"可为空"）
- [ ] 边界条件明确（缺失数据如何处理）

### ✅ 可测试性
- [ ] 提供至少一个完整的输入/输出示例
- [ ] 示例涵盖边界情况（如空数据、异常格式）
- [ ] 输出格式可被程序验证（如 JSON 可被解析）

### ✅ 维护性
- [ ] 使用标准化的章节结构
- [ ] 规则使用列表而非大段落
- [ ] 复杂逻辑有注释说明

### ✅ 跨组件一致性
- [ ] 如果 Prompt 定义了数据结构，确保在 `PROTOCOL.md` 中有对应定义
- [ ] Python 和 Go 的相同逻辑 Prompt 保持结构一致
- [ ] 输出的 JSON 结构与 Pydantic 模型 (`protocol.py`) 匹配

---

## 常见反模式

### ❌ 反模式 1: 硬编码在代码中
```python
# 错误示例
prompt = """
你是一个游戏主持人。
请分析以下内容...
"""
```

**解决方案**: 创建 `prompts/analyze_content.prompt` 并用 `load_prompt()` 加载。

---

### ❌ 反模式 2: 模糊的输出约束
```markdown
# Output Format
请输出 JSON 格式的结果。
```

**问题**: 
- 未指定是否允许 Markdown 包裹
- 未定义字段结构
- 未说明必需字段

**解决方案**:
```markdown
# Output Format
## Format Constraints
**CRITICAL**: 输出必须是纯 JSON，无 Markdown 包裹。

## Schema
```json
{
  "items": [
    {
      "id": "string (必需)",
      "name": "string (必需)",
      "quantity": "number (默认 1)"
    }
  ]
}
```
```

---

### ❌ 反模式 3: 角色定义过于宽泛
```markdown
# Role
你是一个乐于助人的 AI。
```

**问题**: 未指定领域专业知识，导致输出质量低。

**解决方案**:
```markdown
# Role
你是一位专精于**恐怖游戏叙事设计**的编剧 AI，擅长根据环境线索生成悬念感十足的剧情事件。
```

---

### ❌ 反模式 4: 规则列表过长无结构
```markdown
# Rules
1. 做 A
2. 做 B
3. 做 C
... (50 条规则)
```

**问题**: 难以维护和理解优先级。

**解决方案**: 使用分组和优先级标记
```markdown
# Processing Rules
## Critical Rules (必须遵守)
1. **[MUST]** 输出必须是有效的 JSON
2. **[MUST]** 不得编造输入中未提及的信息

## Optimization Rules (建议遵守)
3. **[SHOULD]** 优先提取高频出现的物品
4. **[MAY]** 对模糊描述进行合理推断
```

---

### ❌ 反模式 5: 缺少输入/输出示例
```xml
<role>提取物品列表</role>
<!-- 缺少 <examples> -->
```

**问题**: 开发者和 AI 对"物品"的理解可能不一致。

**解决方案**: 提供完整示例
```xml
<examples>
  <input_example>
  {
    "text": "玩家在房间里发现了一瓶杏仁水和一把手电筒。"
  }
  </input_example>

  <output_example>
  {
    "items": [
      {"id": "almond_water", "name": "杏仁水", "quantity": 1},
      {"id": "flashlight", "name": "手电筒", "quantity": 1}
    ]
  }
  </output_example>
</examples>

---

## 优化工具

### 1. Prompt 结构化优化
如果有一段非结构化的指令文本，创建一个临时 Prompt 文件，使用 XML 结构化：

```xml
<role>你是一位 Prompt Engineering 专家。</role>
<goal>将用户提供的非结构化指令重组为符合本项目标准的 XML 风格 `.prompt` 文件。</goal>
<input>{paste_unstructured_instructions}</input>
```

### 2. 格式约束生成
对于复杂的 JSON/SQL 输出，使用 `<json_schema>` 标签明确定义：

```xml
<role>你是数据格式规范专家。</role>
<goal>生成严格的 JSON Schema。</goal>
<input>
用户需求: 需要一个包含玩家属性（力量、敏捷、体质）和背包物品列表的数据结构。
</input>
```

---

## 版本控制与审查

### 提交前检查
1. **运行测试**: 使用 `scripts/` 中的 Agent 运行脚本验证 Prompt 是否按预期工作
   ```bash
   python scripts/run_level_agent.py  # 测试 Level Agent Prompts
   python scripts/run_agent.py        # 测试主 DM Agent
   ```

2. **Schema 验证**: 确保输出的 JSON 结构与 `PROTOCOL.md` 和 `protocol.py` 一致

3. **Peer Review**: 复杂的 Prompt（如主 DM 逻辑）需要至少一位其他开发者审查

### 更新协议
当 Prompt 的输出格式发生变更时，必须同步更新：
1. `PROTOCOL.md` - 数据协议文档
2. `backroom_agent/protocol.py` - Pydantic 模型
3. `frontend/src/types.ts` - TypeScript 类型定义（如果影响前端）

---

## 参考资源

### 内部文档
- [`PROTOCOL.md`](../PROTOCOL.md) - 跨组件数据协议
- [`backroom_agent/README.md`](../backroom_agent/README.md) - Agent 架构说明

### 相关工具
- `backroom_agent/utils/common.py::load_prompt()` - Python Prompt 加载器
- `go_agent/agent/` - Go Prompt 模板系统

### 示例 Prompts
- 主 Agent: [`backroom_agent/prompts/dm_agent.prompt`](../backroom_agent/prompts/dm_agent.prompt)
- Level Agent: [`backroom_agent/subagents/level/prompts/generate_json.prompt`](../backroom_agent/subagents/level/prompts/generate_json.prompt)
- Event Agent: [`backroom_agent/subagents/event/prompts/event_agent.prompt`](../backroom_agent/subagents/event/prompts/event_agent.prompt)

---

**最后更新**: 2026-01-09  
**维护者**: BackroomAgent Team
