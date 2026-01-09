package nodes

import (
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

// Helper to load prompt file content
func loadPromptHelper(filename string) (string, error) {
	// Prompts are now in agent/prompt/
	path := filepath.Join("agent", "prompt", filename)

	// Check if running from root
	if _, err := os.Stat(path); os.IsNotExist(err) {
		// Try looking up if we are in a subdir (e.g. tests)
		path = filepath.Join("..", "..", "agent", "prompt", filename)
	}

	content, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	return string(content), nil
}

// Helper to extract JSON from MD block
func extractJSONBlockHelper(content string) string {
	re := regexp.MustCompile("```json([\\s\\S]*?)```")
	matches := re.FindStringSubmatch(content)
	if len(matches) > 1 {
		return strings.TrimSpace(matches[1])
	}
	// Try without "json"
	re2 := regexp.MustCompile("```([\\s\\S]*?)```")
	matches2 := re2.FindStringSubmatch(content)
	if len(matches2) > 1 {
		return strings.TrimSpace(matches2[1])
	}
	return strings.TrimSpace(content)
}
