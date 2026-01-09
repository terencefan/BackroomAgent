package nodes

import (
	"context"
	"fmt"
	"strings"

	"backroom_agent_go/agent/model"
)

type FilterDetailsNode struct{}

func (n *FilterDetailsNode) Name() string {
	return "FilterDetailsNode"
}

func (n *FilterDetailsNode) Execute(ctx context.Context, state *model.AgentState) error {
	state.AddLog("Filtering Details (Entities & Items)...")

	// Filter Entities
	filteredEntities := []model.Entity{}
	for _, ent := range state.ExtractedEntitiesRaw {
		if !strings.Contains(state.CleanedHTML, ent.Name) {
			state.AddLog(fmt.Sprintf("Filtered (Hallucination): Entity '%s' not found in source.", ent.Name))
			continue
		}
		filteredEntities = append(filteredEntities, ent)
	}
	state.FinalEntities = filteredEntities
	state.EntitiesExtracted = true

	// Filter Items
	filteredItems := []model.Item{}
	for _, item := range state.ExtractedItemsRaw {
		// Hallucination Check
		if !strings.Contains(state.CleanedHTML, item.Name) {
			state.AddLog(fmt.Sprintf("Filtered (Hallucination): Item '%s' not found in source.", item.Name))
			continue
		}
		filteredItems = append(filteredItems, item)
	}
	state.FinalItems = filteredItems
	state.ItemsExtracted = true

	state.AddLog(fmt.Sprintf("Filtered finished. %d entities and %d items remained.", len(state.FinalEntities), len(state.FinalItems)))
	return nil
}
