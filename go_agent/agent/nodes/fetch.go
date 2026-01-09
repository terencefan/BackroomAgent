package nodes

import (
	"context"
	"fmt"
	"io"
	"math/rand"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"time"

	"backroom_agent_go/agent/model"
)

var WikiMirrors = []string{
	"http://brcn.backroomswiki.cn",
	"https://backrooms-wiki-cn.wikidot.com",
}

// Reuse exported variables from clean.go if possible or redefine
// Since they are package level in the same package 'agent', we can share them if we rename them to Exported (Capitalized)
// or just keep them here if `clean.go` uses them.
// Let's assume clean.go needs them, so we keep them here but Exported.

// Constants for Cleaning
var UnwantedTags = []string{
	"script", "style", "meta", "link", "noscript", "iframe", "svg", "form", "input", "button", "nav", "footer", "header", "aside",
}

var GarbageClasses = []string{
	"sidebar", "ad", "advertisement", "cookie", "popup", "newsletter", "menu", "navigation", "social", "share",
	"creditRate", "credit", "modalbox", "printuser", "licensebox", "rate-box", "page-options-bottom", "bottom-box",
	"page-tags", "page-info", "page-info-break", "top-text", "bottom-text", "scp-image-block", "footer-wikiwalk-nav",
}

var UsefulTags = map[string]bool{
	"h1": true, "h2": true, "h3": true, "h4": true, "h5": true, "h6": true,
	"p": true, "br": true, "hr": true,
	"ul": true, "ol": true, "li": true, "dl": true, "dt": true, "dd": true,
	"table": true, "thead": true, "tbody": true, "tfoot": true, "tr": true, "th": true, "td": true,
	"blockquote": true, "pre": true, "code": true,
	"b": true, "strong": true, "i": true, "em": true, "u": true, "a": true,
}

var MainContentIDs = []string{
	"#page-content", "#main-content", "#content", "#mw-content-text", "#wiki-content",
}

type FetchNode struct{}

func (n *FetchNode) Name() string {
	return "FetchNode"
}

func (n *FetchNode) Execute(ctx context.Context, state *model.AgentState) error {
	state.AddLog(fmt.Sprintf("Fetching content for %s...", state.LevelName))

	// 1. Generate Candidates
	candidates := n.generateCandidates(state.URL, state.LevelName)
	if len(candidates) == 0 {
		state.AddLog("Error: Could not resolve a URL to fetch.")
	}

	var rawHTML string

	// 2. Try Network with Retries and Mirrors
	for _, cand := range candidates {
		state.AddLog(fmt.Sprintf("Attempting fetch from: %s", cand))
		content, err := n.fetchWithRetries(cand)
		if err == nil {
			rawHTML = content
			state.AddLog(fmt.Sprintf("Successfully fetched from %s", cand))

			// Update state URL to the successful one
			state.URL = cand

			// Update LevelName to match URL segment (lowercase) per requirements
			// e.g. .../Level-3 -> level-3
			if parsed, err := url.Parse(cand); err == nil {
				path := strings.TrimRight(parsed.Path, "/")
				segments := strings.Split(path, "/")
				if len(segments) > 0 {
					lastSeg := segments[len(segments)-1]
					state.LevelName = strings.ToLower(lastSeg)
				}
			}
			break
		} else {
			state.AddLog(fmt.Sprintf("Failed to fetch %s: %v", cand, err))
		}
	}

	// 3. Save Raw Cache (if fetch succeeded)
	if rawHTML != "" && state.LevelName != "" {
		rawPath := filepath.Join("data", "raw", state.LevelName+".html")
		if err := os.MkdirAll(filepath.Dir(rawPath), 0755); err == nil {
			os.WriteFile(rawPath, []byte(rawHTML), 0644)
		}
	}

	// 4. Fallback to Local Cache (if fetch failed)
	if rawHTML == "" {
		state.AddLog("Network fetch failed or no content found. Attempting local cache fallback...")

		// Try exact name
		pathsToTry := []string{
			filepath.Join("data", "raw", state.LevelName+".html"),
			filepath.Join("data", "raw", strings.ToLower(strings.ReplaceAll(state.LevelName, " ", "-"))+".html"),
		}

		for _, p := range pathsToTry {
			if _, err := os.Stat(p); err == nil {
				content, err := os.ReadFile(p)
				if err == nil {
					rawHTML = string(content)
					state.AddLog(fmt.Sprintf("Loaded raw HTML from local cache: %s", p))
					// Update level name to match the file we found (normalized)
					base := filepath.Base(p)
					state.LevelName = strings.TrimSuffix(base, ".html")
					break
				}
			}
		}
	}

	if rawHTML == "" {
		return fmt.Errorf("failed to fetch content for %s", state.LevelName)
	}

	// Just set RawHTML. Cleaning is done in CleanContentNode.
	state.RawHTML = rawHTML
	return nil
}

// generateCandidates generates a list of URLs to try based on input URL and LevelName
func (n *FetchNode) generateCandidates(inputURL string, levelName string) []string {
	var candidates []string
	seen := make(map[string]bool)

	// Helper to add unique candidate
	addCandidate := func(u string) {
		if u != "" && !seen[u] {
			candidates = append(candidates, u)
			seen[u] = true
		}
	}

	// 1. If URL is provided
	if inputURL != "" {
		// If custom URL (not in our mirrors), try strict
		isKnownMirror := false
		for _, m := range WikiMirrors {
			if strings.Contains(inputURL, m) {
				isKnownMirror = true
				break
			}
		}

		if !isKnownMirror {
			addCandidate(inputURL)
		} else {
			// If it's a known mirror, extract the path and generate all mirror variants
			parsed, err := url.Parse(inputURL)
			if err == nil {
				path := parsed.Path
				for _, mirror := range WikiMirrors {
					base := strings.TrimRight(mirror, "/")
					rel := strings.TrimLeft(path, "/")
					full := fmt.Sprintf("%s/%s", base, rel)
					addCandidate(full)
				}
			} else {
				addCandidate(inputURL)
			}
		}
	}

	// 2. If LevelName is provided (supplementary or primary)
	if levelName != "" && len(candidates) == 0 {
		sanitized := strings.ReplaceAll(levelName, " ", "-")
		for _, mirror := range WikiMirrors {
			base := strings.TrimRight(mirror, "/")
			full := fmt.Sprintf("%s/%s", base, sanitized)
			addCandidate(full)
		}
	}

	return candidates
}

// fetchWithRetries attempts to GET a URL with retries
func (n *FetchNode) fetchWithRetries(targetURL string) (string, error) {
	retries := 3
	var lastErr error

	client := &http.Client{
		Timeout: 30 * time.Second,
	}

	for i := 0; i < retries; i++ {
		req, err := http.NewRequest("GET", targetURL, nil)
		if err != nil {
			return "", err
		}
		// Mimic browser
		req.Header.Set("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36")

		resp, err := client.Do(req)
		if err == nil {
			defer resp.Body.Close()
			if resp.StatusCode == 200 {
				bodyBytes, err := io.ReadAll(resp.Body)
				if err == nil {
					return string(bodyBytes), nil
				}
				lastErr = err
			} else if resp.StatusCode == 404 {
				return "", fmt.Errorf("status 404: Not Found")
			} else {
				lastErr = fmt.Errorf("status %d", resp.StatusCode)
			}
		} else {
			lastErr = err
		}

		// Wait before retry
		if i < retries-1 {
			// Exponential backoff: 2^i + jitter
			baseWait := time.Duration(1<<uint(i)) * time.Second
			jitter := time.Duration(rand.Int63n(1000)) * time.Millisecond
			time.Sleep(baseWait + jitter)
		}
	}

	return "", lastErr
}
