package nodes

import (
	"strings"
	"testing"
)

func TestCleanHTML(t *testing.T) {
	rawHTML := `<!DOCTYPE html>
<html>
<head>
	<title>Test Page</title>
	<script>alert('bad');</script>
	<style>.ad { color: red; }</style>
</head>
<body>
	<div id="page-content">
		<h1>Real Title</h1>
		<p class="text-cls" style="color: blue;">
			This is <b>content</b>.
			<a href="/link" class="link-cls">Link</a>
		</p>
		
		<div class="ad-container">
			<div class="ad">Buy stuff</div>
		</div>
		<div id="sidebar">Sidebar content</div>
		<div style="display: none;">Hidden text</div>
		<div style="display:none">Hidden text 2</div>
		
		<p></p>
		<div> </div>
		<span></span>

		<p>Next paragraph.</p>
	</div>
	<div class="footer">Footer</div>
</body>
</html>`

	cleaned, links, err := CleanHTML(rawHTML)
	if err != nil {
		t.Fatalf("CleanHTML failed: %v", err)
	}

	t.Logf("Cleaned HTML:\n%s", cleaned)
	t.Logf("Links: %v", links)

	if !strings.Contains(cleaned, "<h1>Test Page</h1>") {
		t.Errorf("Expected extracted title 'Test Page' in h1, got output:\n%s", cleaned)
	}

	if strings.Contains(cleaned, "<script") {
		t.Error("Output contains <script> tag")
	}
	if strings.Contains(cleaned, "<style") {
		t.Error("Output contains <style> tag")
	}

	if strings.Contains(cleaned, "Buy stuff") {
		t.Error("Output contains garbage content 'Buy stuff'")
	}
	if strings.Contains(cleaned, "Sidebar content") {
		t.Error("Output contains garbage content 'Sidebar content'")
	}
	if strings.Contains(cleaned, "Footer") {
		t.Error("Output contains footer content")
	}

	if strings.Contains(cleaned, "Hidden text") {
		t.Error("Output contains display:none content")
	}

	if strings.Contains(cleaned, "class=") {
		t.Error("Output contains class attribute")
	}
	if strings.Contains(cleaned, "style=") {
		t.Error("Output contains style attribute")
	}

	if !strings.Contains(cleaned, `<a href="/link">Link</a>`) {
		t.Errorf("Link was not preserved correctly or attributes not cleaned. Got:\n%s", cleaned)
	}

	if strings.Contains(cleaned, "<p></p>") {
		t.Error("Output contains empty <p>")
	}

	if len(links) != 1 {
		t.Errorf("Expected 1 extracted link, got %d", len(links))
	} else {
		if links[0].Text != "Link" || links[0].URL != "/link" {
			t.Errorf("Link extraction incorrect: %+v", links[0])
		}
	}
}
