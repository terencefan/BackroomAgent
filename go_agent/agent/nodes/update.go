package nodes

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"backroom_agent_go/agent/model"
)

type UpdateNode struct{}

func (n *UpdateNode) Name() string {
	return "UpdateNode"
}

// UpdateNode saves the Level JSON, Items, and Entities to disk basically mirroring Python's update.py
func (n *UpdateNode) Execute(ctx context.Context, state *model.AgentState) error {
	state.AddLog("Updating (Saving) Data...")

	if state.FinalLevelData.Title == "" {
		state.AddLog("Error: No Level Title generated, skipping save.")
		return nil
	}

	// 1. Prepare Paths
	// Assuming running from root, paths mirror Python structure
	baseDataPath := "data"
	levelPath := filepath.Join(baseDataPath, "level")
	itemPath := filepath.Join(baseDataPath, "item")
	entityPath := filepath.Join(baseDataPath, "entity")

	// Ensure directories exist
	os.MkdirAll(levelPath, 0755)
	os.MkdirAll(itemPath, 0755)
	os.MkdirAll(entityPath, 0755)

	// 2. Save Level Data
	// Combine explicit fields into the map for saving to match Python output structure
	// Python: final_data = {**level_data, "items": [...], "entities": [...]}
	finalMap := make(map[string]interface{})

	// Convert LevelData struct back to map for flexibility
	levelJSON, _ := json.Marshal(state.FinalLevelData)
	json.Unmarshal(levelJSON, &finalMap)

	// Add Name lists (requested: only names)
	itemNames := []string{}
	for _, i := range state.FinalItems {
		itemNames = append(itemNames, i.Name)
	}
	entityNames := []string{}
	for _, e := range state.FinalEntities {
		entityNames = append(entityNames, e.Name)
	}

	finalMap["items"] = itemNames      // Override with names
	finalMap["entities"] = entityNames // Override with names
	// Clean up structs if they were marshaled into map (though LevelData shouldn't populate them if empty)
	delete(finalMap, "findable_items")

	// Save Level JSON file
	// Use state.LevelName for filename consistency, instead of state.FinalLevelData.ID/Title
	levelID := state.LevelName
	if levelID == "" {
		// Fallback if LevelName is missing for some reason
		levelID = state.FinalLevelData.ID
	}
	levelFileName := filepath.Join(levelPath, fmt.Sprintf("%s.json", levelID))
	saveJSON(levelFileName, finalMap)
	state.AddLog(fmt.Sprintf("Saved Level: %s", levelFileName))

	// 3. Save Items
	for _, item := range state.FinalItems {
		// structure: data/item/{category}/{name}.json
		cat := "Uncategorized"
		if item.Category != "" {
			cat = item.Category
		}
		// Sanitize for path usage basic approach
		catDir := filepath.Join(itemPath, cat)
		os.MkdirAll(catDir, 0755)

		// Filename is {name}.json
		fPath := filepath.Join(catDir, fmt.Sprintf("%s.json", item.Name))
		saveJSON(fPath, item)
	}
	if len(state.FinalItems) > 0 {
		state.AddLog(fmt.Sprintf("Saved %d Items", len(state.FinalItems)))
	}

	// 4. Save Entities
	for _, ent := range state.FinalEntities {
		// structure: data/entity/{name}.json
		fPath := filepath.Join(entityPath, fmt.Sprintf("%s.json", ent.Name))
		saveJSON(fPath, ent)
	}
	if len(state.FinalEntities) > 0 {
		state.AddLog(fmt.Sprintf("Saved %d Entities", len(state.FinalEntities)))
	}
	return nil
}

func saveJSON(path string, data interface{}) {
	file, err := os.Create(path)
	if err != nil {
		fmt.Printf("Error creating file %s: %v\n", path, err)
		return
	}
	defer file.Close()

	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(data); err != nil {
		fmt.Printf("Error encoding JSON to %s: %v\n", path, err)
	}
}
