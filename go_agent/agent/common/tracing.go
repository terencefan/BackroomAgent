package common

import (
	"context"
	"os"
	"time"

	"github.com/google/uuid"
	"github.com/langchain-ai/langsmith-go"
)

type Span interface {
	End(outputs map[string]interface{}, err error)
}

type TracingClient interface {
	Start(ctx context.Context, name string, inputs map[string]interface{}) Span
}

type LangSmithClient struct {
	client *langsmith.Client
}

func NewTracingClient() TracingClient {
	if os.Getenv("LANGSMITH_TRACING") == "true" {
		return &LangSmithClient{client: langsmith.NewClient()}
	}
	return &NoOpTracingClient{}
}

type langSmithSpan struct {
	client    *langsmith.Client
	name      string
	inputs    map[string]interface{}
	startTime time.Time
	runID     string
}

func (c *LangSmithClient) Start(ctx context.Context, name string, inputs map[string]interface{}) Span {
	return &langSmithSpan{
		client:    c.client,
		name:      name,
		inputs:    inputs,
		startTime: time.Now(),
		runID:     uuid.New().String(),
	}
}

func (s *langSmithSpan) End(outputs map[string]interface{}, err error) {
	endTime := time.Now()
	// Capture variables for closure
	runID := s.runID
	name := s.name
	startTime := s.startTime
	inputs := s.inputs
	client := s.client

	go func() {
		// For single call, TraceID can be same as RunID if no parent context
		traceID := runID

		runParam := langsmith.RunParam{
			ID:        langsmith.String(runID),
			Name:      langsmith.String(name),
			RunType:   langsmith.F(langsmith.RunRunTypeLlm),
			StartTime: langsmith.String(startTime.Format(time.RFC3339Nano)),
			EndTime:   langsmith.String(endTime.Format(time.RFC3339Nano)),
			Inputs:    langsmith.F(inputs),
			Outputs:   langsmith.F(outputs),
			TraceID:   langsmith.String(traceID),
		}

		if err != nil {
			runParam.Error = langsmith.String(err.Error())
		}

		// Use a background context for the async operation to avoid cancellation issues
		bgCtx := context.Background()
		client.Runs.IngestBatch(bgCtx, langsmith.RunIngestBatchParams{
			Post: langsmith.F([]langsmith.RunParam{runParam}),
		})
	}()
}

type NoOpTracingClient struct{}

func (c *NoOpTracingClient) Start(ctx context.Context, name string, inputs map[string]interface{}) Span {
	return &noOpSpan{}
}

type noOpSpan struct{}

func (s *noOpSpan) End(outputs map[string]interface{}, err error) {}
