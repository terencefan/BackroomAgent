package nodes

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"backroom_agent_go/agent/common"
	"backroom_agent_go/agent/model"
)

type GenerateJSONNode struct {
	LLM          common.ModelClient
	systemPrompt string
}

func (n *GenerateJSONNode) SetLLM(client common.ModelClient) {
	n.LLM = client
}

func (n *GenerateJSONNode) GetSystemPrompt() string {
	return n.systemPrompt
}

func (n *GenerateJSONNode) GetUserPrompt() string {
	return ""
}

func (n *GenerateJSONNode) Name() string {
	return "GenerateJSONNode"
}

func (n *GenerateJSONNode) Execute(ctx context.Context, state *model.AgentState) error {
	jsonPath := filepath.Join("data", "level", state.LevelName+".json")
	if _, err := os.Stat(jsonPath); err == nil && !state.ForceUpdate {
		state.AddLog("Level JSON already exists. Skipping generation.")
		state.LevelJSONGenerated = true
		return nil
	}

	state.AddLog("Generating Level JSON...")
	sysPrompt, err := loadPromptHelper("generate_json.prompt")
	if err != nil {
		return err
	}
	n.systemPrompt = sysPrompt

	userPrompt := fmt.Sprintf("Here is the cleaned HTML content of the level:\n\n%s", state.CleanedHTML)

	// Since we set n.SystemPrompt, we can just pass the user message.
	messages := []common.Message{
		common.SystemMessage{Content: n.systemPrompt},
		common.HumanMessage{Content: userPrompt},
	}

	if n.LLM == nil {
		return fmt.Errorf("LLM client not set")
	}

	resp, err := n.LLM.Chat(ctx, messages)
	if err != nil {
		return err
	}

	jsonStr := extractJSONBlockHelper(resp.Content())
	// Validate and Populate State
	var levelData model.LevelData
	if err := json.Unmarshal([]byte(jsonStr), &levelData); err != nil {
		state.AddLog(fmt.Sprintf("JSON Unmarshal failed: %v", err))
		// We write it anyway for debugging
	} else {
		state.FinalLevelData = levelData
	}

	// Also save the file immediately as cache/result
	os.MkdirAll(filepath.Dir(jsonPath), 0755)
	os.WriteFile(jsonPath, []byte(jsonStr), 0644)

	state.LevelJSONGenerated = true
	state.AddLog("Level JSON generated and saved.")
	return nil
}
