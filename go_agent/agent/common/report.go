package common

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"
)

// Report Structures
type NodeExecutionRecord struct {
	NodeName  string    `json:"node_name"`
	StartTime time.Time `json:"start_time"`
	EndTime   time.Time `json:"end_time"`
	Duration  string    `json:"duration"`
	Status    string    `json:"status"` // "Success" or "Error"
	ErrorMsg  string    `json:"error_msg,omitempty"`
}

type ExecutionReport struct {
	StartTime     time.Time             `json:"start_time"`
	EndTime       time.Time             `json:"end_time"`
	TotalDuration string                `json:"total_duration"`
	Status        string                `json:"status"`
	Nodes         []NodeExecutionRecord `json:"nodes"`
}

func writeReport(report ExecutionReport) error {
	tmpDir := "tmp"
	if err := os.MkdirAll(tmpDir, 0755); err != nil {
		return err
	}

	timestamp := report.StartTime.Format("20060102_150405")
	filename := filepath.Join(tmpDir, fmt.Sprintf("report_%s.json", timestamp))

	data, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return err
	}

	return os.WriteFile(filename, data, 0644)
}
