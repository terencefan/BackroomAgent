package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"os"
	"strings"
	"sync"

	"github.com/joho/godotenv"

	"backroom_agent_go/agent/common"
	"backroom_agent_go/agent/model"
	"backroom_agent_go/agent/nodes"
)

var (
	urlFlag   = flag.String("url", "", "URL of the Backrooms Wiki page to process")
	nameFlag  = flag.String("name", "", "Level Name (e.g. 'Level 3')")
	batchFlag = flag.Bool("batch", false, "Run in batch mode")
	startFlag = flag.Int("start", 0, "Start Level for batch mode")
	endFlag   = flag.Int("end", 11, "End Level for batch mode")
)

func init() {
	// Configure Log to show time with microseconds
	log.SetFlags(log.LstdFlags | log.Lmicroseconds)

	// Load Env
	if err := godotenv.Load(); err != nil {
		// handle if .env doesn't exist, might be set in shell
		log.Println("Warning: No .env file found")
	}

	if os.Getenv("OPENAI_API_KEY") == "" {
		log.Println("Warning: OPENAI_API_KEY is not set in environment (required for JSON generation)")
	}

	// CLI Arguments
	flag.Parse()
}

func main() {
	// Initialize Shared Client
	client, err := common.NewLLMClient()
	if err != nil {
		log.Fatalf("Failed to create LLM Client: %v", err)
	}

	if *batchFlag || (*urlFlag == "" && *nameFlag == "") {
		// Batch Mode 0-11
		runBatch(client)
	} else {
		// Single Mode
		runSingle(client)
	}
}

func runSingle(client common.ModelClient) {
	var levelName string
	if *nameFlag != "" {
		levelName = *nameFlag
	} else {
		// Derive Level Name if possible
		parts := strings.Split(*urlFlag, "/")
		levelName = parts[len(parts)-1]
		if levelName == "" && len(parts) > 1 {
			levelName = parts[len(parts)-2]
		}
	}

	if err := buildAndRunAgent(levelName, *urlFlag, client); err != nil {
		log.Printf("Agent failed: %v", err)
	}
}

func runBatch(client common.ModelClient) {
	var wg sync.WaitGroup
	sem := make(chan struct{}, 10) // Concurrency limit 10

	fmt.Printf("Starting Batch Processing for Levels %d-%d...\n", *startFlag, *endFlag)

	for i := *startFlag; i <= *endFlag; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			sem <- struct{}{}        // Acquire token
			defer func() { <-sem }() // Release token

			levelName := fmt.Sprintf("Level %d", i)
			url := fmt.Sprintf("https://backrooms-wiki-cn.wikidot.com/level-%d", i)

			log.Printf("[%s] Starting...", levelName)
			if err := buildAndRunAgent(levelName, url, client); err != nil {
				log.Printf("[%s] Failed: %v", levelName, err)
			} else {
				log.Printf("[%s] Completed successfully.", levelName)
			}
		}(i)
	}

	wg.Wait()
	fmt.Println("All levels processed.")
}

func buildAndRunAgent(levelName, url string, client common.ModelClient) error {
	// Initialize State
	// Each agent needs its own state
	state := model.NewAgentState(levelName, url, true)

	// Define Pipeline using New Graph Agent
	agent := common.NewGraphAgent[*model.AgentState](client)

	// Nodes
	fetchNode := &nodes.FetchNode{}
	cleanNode := &nodes.CleanNode{}
	genJSONNode := &nodes.GenerateJSONNode{}
	extractDetailsNode := &nodes.ExtractDetailsNode{}
	filterDetailsNode := &nodes.FilterDetailsNode{}
	updateNode := &nodes.UpdateNode{}

	agent.RegisterNode(fetchNode)
	agent.RegisterNode(cleanNode)
	agent.RegisterNode(genJSONNode)
	agent.RegisterNode(extractDetailsNode)
	agent.RegisterNode(filterDetailsNode)
	agent.RegisterNode(updateNode)

	// Routing (Start -> Fetch -> Clean -> GenJSON -> ExtractDetails -> FilterDetails -> Update -> End)
	mustAddEdge := func(from, to common.Namer) {
		if err := agent.AddEdge(from, to); err != nil {
			// Panic here is okay as it's configuration error
			panic(fmt.Sprintf("Failed to add edge %s -> %s: %v", from.Name(), to.Name(), err))
		}
	}

	mustAddEdge(common.START, fetchNode)
	mustAddEdge(fetchNode, cleanNode)
	mustAddEdge(cleanNode, genJSONNode)
	mustAddEdge(genJSONNode, extractDetailsNode)
	mustAddEdge(extractDetailsNode, filterDetailsNode)
	mustAddEdge(filterDetailsNode, updateNode)
	mustAddEdge(updateNode, common.END)

	startMsg := common.HumanMessage{Content: fmt.Sprintf("Process URL: %s", url)}
	return agent.Run(context.Background(), state, startMsg)
}
