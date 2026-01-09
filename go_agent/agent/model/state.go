package model

import (
	"log"
	"sync"

	"backroom_agent_go/agent/common"
)

// Item represents a findable item
type Item struct {
	ID          string `json:"id"`
	Name        string `json:"name"`
	Description string `json:"description"`
	Category    string `json:"category"`
}

// Entity represents an entity
type Entity struct {
	ID          string `json:"id"`
	Name        string `json:"name"`
	Description string `json:"description"`
	Behavior    string `json:"behavior"`
}

// LevelData represents the structure of the generate level json
type LevelData struct {
	ID                     string                  `json:"level_id"`
	Title                  string                  `json:"title"`
	SurvivalDifficulty     SurvivalDifficulty      `json:"survival_difficulty"`
	Atmosphere             Atmosphere              `json:"atmosphere"`
	EnvironmentalMechanics []EnvironmentalMechanic `json:"environmental_mechanics"`
	SubZones               []SubZone               `json:"sub_zones"`
	Factions               []Faction               `json:"factions"`
	Links                  []Link                  `json:"links,omitempty"`
	FindableItems          []Item                  `json:"findable_items,omitempty"`
	Entities               []Entity                `json:"entities,omitempty"`
}

type SubZone struct {
	Name        string `json:"name"`
	Description string `json:"description"`
	DangerLevel string `json:"danger_level"`
}

type Faction struct {
	Name        string `json:"name"`
	Alignment   string `json:"alignment"`
	Description string `json:"description"`
}

type SurvivalDifficulty struct {
	Class       string `json:"class"`
	Description string `json:"description"`
}

type Atmosphere struct {
	Visuals []string `json:"visuals"`
	Audio   []string `json:"audio"`
	Smell   []string `json:"smell"`
	Vibe    []string `json:"vibe"`
}

type EnvironmentalMechanic struct {
	Mechanic           string `json:"mechanic"`
	Effect             string `json:"effect"`
	TriggerProbability string `json:"trigger_probability"`
}

type Link struct {
	Text string `json:"text"`
	URL  string `json:"url"`
}

// AgentState mimics the TypedDict in Python
type AgentState struct {
	// Input
	URL         string
	LevelName   string
	ForceUpdate bool

	// Logs
	Logs []string

	// Fetch Data
	RawHTML        string // Raw from source/cache
	CleanedHTML    string // Processed for LLM
	ExtractedLinks []Link

	// Generated
	LevelJSONGenerated bool
	FinalLevelData     LevelData

	// Extracted Raw
	ExtractedItemsRaw    []Item
	ExtractedEntitiesRaw []Entity

	// Filtered / Final
	FinalItems        []Item
	FinalEntities     []Entity
	ItemsExtracted    bool
	EntitiesExtracted bool

	mu sync.Mutex
}

func NewAgentState(levelName, url string, forceUpdate bool) *AgentState {
	return &AgentState{
		LevelName:   levelName,
		URL:         url,
		ForceUpdate: forceUpdate,
		Logs:        make([]string, 0),
	}
}

func (s *AgentState) GetID(name string) string {
	return GetRegistry().GetID(name)
}

func (s *AgentState) AddLog(msg string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	log.Printf("LOG: %s", msg)
	s.Logs = append(s.Logs, msg)
}

func (s *AgentState) ReceiveMessage(msg common.Message) {
	s.AddLog("Received message: " + msg.GetContent())
	// For now, we don't change state based on message content automatically,
	// but specific nodes might read the message from logs or we might add a LastMessage field.
}
