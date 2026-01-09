package nodes

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/PuerkitoBio/goquery"

	"backroom_agent_go/agent/model"
)

type CleanNode struct{}

func (n *CleanNode) Name() string {
	return "CleanNode"
}

// CleanContentNode performs the HTML cleaning separate from fetching
func (n *CleanNode) Execute(ctx context.Context, state *model.AgentState) error {
	state.AddLog("Cleaning HTML content...")

	if state.RawHTML == "" {
		return fmt.Errorf("no raw HTML to clean")
	}

	cleanHTML, links, err := CleanHTML(state.RawHTML)
	if err != nil {
		return err
	}

	state.CleanedHTML = cleanHTML
	state.ExtractedLinks = links

	// Save Cleaned HTML to data/level/{level_name}.html
	// This ensures prefix consistency with the JSON we will generate later
	if state.LevelName != "" {
		cleanPath := filepath.Join("data", "level", state.LevelName+".html")
		os.MkdirAll(filepath.Dir(cleanPath), 0755)
		os.WriteFile(cleanPath, []byte(cleanHTML), 0644)
		state.AddLog(fmt.Sprintf("Saved Cleaned HTML to %s", cleanPath))
	}

	return nil
}

// Reuse the constants from existing fetch.go if possible, or move them here.
// Since they are in the same package 'agent', we can access them if they are exported or in the same package.
// We previously defined UnwantedTags, etc in fetch.go.

// CleanHTML parses the raw HTML, applies cleaning strategies in a loop, and extracting the result.
func CleanHTML(rawHTML string) (string, []model.Link, error) {
	doc, err := goquery.NewDocumentFromReader(strings.NewReader(rawHTML))
	if err != nil {
		return "", nil, err
	}

	// 1. Extract Title (Before we potentially lose the head or title tag if focused on body)
	pageTitle := strings.TrimSpace(doc.Find("#page-title").Text())
	if pageTitle == "" {
		pageTitle = strings.TrimSpace(doc.Find("title").Text())
	}

	// 2. Focus on Main Content
	var content *goquery.Selection
	for _, id := range MainContentIDs {
		sel := doc.Find(id)
		if sel.Length() > 0 {
			content = sel
			break
		}
	}
	if content == nil {
		content = doc.Find("body")
	}
	if content.Length() == 0 {
		// Fallback if no body found (fragment)
		content = doc.Selection
	}

	// 3. FIFO Strategy Loop
	// "strategy" function: returns true if the content was modified.
	type CleanStrategy func(*goquery.Selection) bool

	queue := []CleanStrategy{
		removeUnwantedTags,
		removeGarbageSelectors,
		removeDisplayNone,
		removeInvalidLinks,
		cleanAttributesAndUnwrap,
		removeEmptyTags,
	}

	maxOps := 200 // Circuit breaker to prevent infinite loops
	ops := 0

	for len(queue) > 0 {
		ops++
		if ops > maxOps {
			// Break just in case
			break
		}

		strat := queue[0]
		queue = queue[1:]

		changed := strat(content)
		if changed {
			// If changed, re-queue this strategy to ensuring valid state
			queue = append(queue, strat)
		}
	}

	// 4. Extract Links (from the final clean content)
	var links []model.Link
	content.Find("a[href]").Each(func(i int, s *goquery.Selection) {
		href, exists := s.Attr("href")
		text := strings.TrimSpace(s.Text())
		if exists && text != "" && !strings.HasPrefix(href, "javascript") && !strings.HasPrefix(href, "#") {
			links = append(links, model.Link{Text: text, URL: href})
		}
	})

	// 5. Render
	cleanText, err := content.Html()
	if err != nil {
		return "", nil, err
	}

	// Remove empty lines from the resulting HTML
	var validLines []string
	for _, line := range strings.Split(cleanText, "\n") {
		if cleanString(line) != "" {
			validLines = append(validLines, line)
		}
	}
	cleanText = strings.Join(validLines, "\n")

	if pageTitle != "" {
		cleanText = fmt.Sprintf("<h1>%s</h1>\n%s", pageTitle, cleanText)
	}

	return cleanText, links, nil
}

// --- Strategies ---

func removeUnwantedTags(s *goquery.Selection) bool {
	changed := false
	for _, tag := range UnwantedTags {
		found := s.Find(tag)
		if found.Length() > 0 {
			found.Remove()
			changed = true
		}
	}
	return changed
}

func removeGarbageSelectors(s *goquery.Selection) bool {
	changed := false
	for _, cls := range GarbageClasses {
		// Class or ID
		found := s.Find("." + cls + ", #" + cls)
		if found.Length() > 0 {
			found.Remove()
			changed = true
		}
	}
	return changed
}

func removeDisplayNone(s *goquery.Selection) bool {
	// We need to collect items to remove first to avoid modifying while iterating?
	// goquery .Each is usually safe, but let's be careful.
	var toRemove []*goquery.Selection

	s.Find("*").Each(func(i int, sel *goquery.Selection) {
		if style, exists := sel.Attr("style"); exists {
			if strings.Contains(strings.ReplaceAll(strings.ToLower(style), " ", ""), "display:none") {
				toRemove = append(toRemove, sel)
			}
		}
	})

	if len(toRemove) > 0 {
		for _, sel := range toRemove {
			sel.Remove()
		}
		return true
	}
	return false
}

func cleanAttributesAndUnwrap(s *goquery.Selection) bool {
	changed := false

	// We iterate all descendants
	s.Find("*").Each(func(i int, s *goquery.Selection) {
		tagName := goquery.NodeName(s)

		if UsefulTags[tagName] {
			// It is a useful tag. Clean attributes.
			// Keep 'href' for 'a', remove ALL others (style, class, id, etc.)

			// Get potentially needed attributes
			href, hasHref := s.Attr("href")

			// Currently GoQuery doesn't support "RemoveAllAttributes" easily.
			// Accessing the underlying html.Node
			if len(s.Nodes) > 0 {
				node := s.Nodes[0]
				// Filter attributes
				// goquery.Node is *html.Node

				if len(node.Attr) > 0 {
					// We have attributes. Check if we need to clean.
					needsClean := false

					if tagName == "a" {
						// For 'a', we accept only 'href'
						if len(node.Attr) > 1 || (len(node.Attr) == 1 && node.Attr[0].Key != "href") {
							needsClean = true
						}
					} else {
						// For others, we accept NO attributes
						if len(node.Attr) > 0 {
							needsClean = true
						}
					}

					if needsClean {
						// We can just wipe them
						node.Attr = nil
						// Restore allowed
						if tagName == "a" && hasHref {
							s.SetAttr("href", href)
						}
						changed = true
					}
				}
			}
		} else {
			// Not useful: Unwrap (Replace with children)
			s.ReplaceWithSelection(s.Contents())
			changed = true
		}
	})
	return changed
}

func removeInvalidLinks(s *goquery.Selection) bool {
	changed := false
	s.Find("a").Each(func(i int, sub *goquery.Selection) {
		// We re-check href here because it might be executed multiple times or on new nodes
		href, exists := sub.Attr("href")
		if exists {
			href = strings.ToLower(strings.TrimSpace(href))
			if strings.HasPrefix(href, "#") || strings.HasPrefix(href, "javascript:") {
				sub.Remove()
				changed = true
			}
		}
	})
	return changed
}

func removeEmptyTags(s *goquery.Selection) bool {
	changed := false
	// Find all potential candidates
	s.Find("*").Each(func(i int, sub *goquery.Selection) {
		// If it has children elements, it's not empty
		if sub.Children().Length() > 0 {
			return
		}

		text := cleanString(sub.Text())
		if text == "" {
			sub.Remove()
			changed = true
		}
	})
	return changed
}

func cleanString(s string) string {
	// Remove Zero Width Space (\u200b) and other invisibles
	replacements := []string{
		"\u200b", "", // Zero Width Space
		"\u200c", "", // Zero Width Non-Joiner
		"\u200d", "", // Zero Width Joiner
		"\ufeff", "", // BOM
		"\u00a0", " ", // No-Break Space -> Space (optional, but good for trimming)
	}
	r := strings.NewReplacer(replacements...)
	return strings.TrimSpace(r.Replace(s))
}
