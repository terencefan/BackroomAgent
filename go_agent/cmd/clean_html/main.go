package main

import (
	"context"
	"flag"
	"log"
	"os"
	"path/filepath"
	"strings"

	"backroom_agent_go/agent/model"
	"backroom_agent_go/agent/nodes"
)

func main() {
	levelPtr := flag.String("level", "", "Level name (e.g. level-2)")
	urlPtr := flag.String("url", "", "URL to derive level name (optional)")
	flag.Parse()

	levelName := *levelPtr
	if levelName == "" && *urlPtr != "" {
		// Try to derive from URL
		parts := strings.Split(*urlPtr, "/")
		candidate := parts[len(parts)-1]
		if candidate == "" && len(parts) > 1 {
			candidate = parts[len(parts)-2]
		}
		levelName = candidate
	}

	if levelName == "" {
		log.Fatal("Error: Please provide -level <name> or -url <url>")
	}

	// 1. Read Raw File
	rawFile := filepath.Join("data", "raw", levelName+".html")
	log.Printf("Reading raw HTML from: %s", rawFile)

	bytes, err := os.ReadFile(rawFile)
	if err != nil {
		log.Fatalf("Failed to read file: %v", err)
	}

	if len(bytes) == 0 {
		log.Fatal("Raw file is empty")
	}

	// 2. Initialize State
	state := model.NewAgentState(levelName, "", true)
	state.RawHTML = string(bytes)

	// 3. Execute Clean Node
	cleaner := &nodes.CleanNode{}
	log.Println("Executing CleanNode...")

	if err := cleaner.Execute(context.Background(), state); err != nil {
		log.Fatalf("CleanNode failed: %v", err)
	}

	log.Printf("Success. Cleaned HTML saved to data/level/%s.html", levelName)
}
