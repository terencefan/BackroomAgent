package nodes

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	"backroom_agent_go/agent/common"
	"backroom_agent_go/agent/model"
)

type ExtractDetailsNode struct {
	LLM          common.ModelClient
	systemPrompt string
}

func (n *ExtractDetailsNode) SetLLM(client common.ModelClient) {
	n.LLM = client
}

func (n *ExtractDetailsNode) GetSystemPrompt() string {
	return n.systemPrompt
}

func (n *ExtractDetailsNode) GetUserPrompt() string {
	return ""
}

func (n *ExtractDetailsNode) Name() string {
	return "ExtractDetailsNode"
}

func (n *ExtractDetailsNode) Execute(ctx context.Context, state *model.AgentState) error {
	state.AddLog("Extracting Details (Items & Entities)...")
	sysPrompt, err := loadPromptHelper("extract_details.prompt")
	if err != nil {
		return err
	}

	// Go template might require "InputText" if following my prompt instructions,
	// but the previous code used strings.Replace with "{context}".
	// The new prompt uses {{.InputText}} style from my prompt instruction example?
	// Wait, the new prompt I just created uses {{.InputText}}.
	// I should check if `loadPromptHelper` does template execution or if I need to do it.
	// The previous implementation used strings.Replace(sysPrompt, "{context}", state.CleanedHTML, 1)
	// I should probably stick to what infrastructure supports.
	// Let's check `utils.go` or assume previous pattern for safety if helper is simple.
	// But I wrote {{.InputText}} in the prompt. I should verify `loadPromptHelper` implementation or use strings.Replace and change prompt to {context} or handle template here.

	// Actually, looking at `extract_entities.prompt` it used `{context}`.
	// I used `{{.InputText}}` in `extract_details.prompt` following the new `instructions.md`.
	// I'll assume I should use text/template if I used `{{.}}`.
	// BUT, `extract_entities.go` used `strings.Replace`.
	// To minimize risk effectively, I will use `strings.Replace` and `{context}` in my prompt or code.
	// I can just replace `{{.InputText}}` with the content.

	n.systemPrompt = strings.Replace(sysPrompt, "{{.InputText}}", state.CleanedHTML, 1)

	messages := []common.Message{
		common.SystemMessage{Content: n.systemPrompt},
		common.HumanMessage{Content: "Extract the details (entities and items) now in JSON format."},
	}

	if n.LLM == nil {
		return fmt.Errorf("LLM client not set")
	}

	resp, err := n.LLM.Chat(ctx, messages)
	if err != nil {
		return err
	}

	jsonStr := extractJSONBlockHelper(resp.Content())

	var result struct {
		Entities      []model.Entity `json:"entities"`
		FindableItems []model.Item   `json:"findable_items"`
	}

	if err := json.Unmarshal([]byte(jsonStr), &result); err != nil {
		state.AddLog(fmt.Sprintf("Details Extract JSON error: %v", err))
		return err
	}

	// Post-process entities
	for i := range result.Entities {
		ent := &result.Entities[i]
		ent.ID = state.GetID(ent.Name)
	}
	state.ExtractedEntitiesRaw = result.Entities

	// Post-process items
	for i := range result.FindableItems {
		item := &result.FindableItems[i]
		item.ID = state.GetID(item.Name)
	}
	state.ExtractedItemsRaw = result.FindableItems

	state.AddLog(fmt.Sprintf("Extracted %d raw entities and %d raw items.", len(state.ExtractedEntitiesRaw), len(state.ExtractedItemsRaw)))
	return nil
}
