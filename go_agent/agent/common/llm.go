package common

import (
	"context"
	"fmt"
	"os"

	openai "github.com/sashabaranov/go-openai"
)

// LLMClient wraps the OpenAI client
type LLMClient struct {
	client *openai.Client
	model  string
	tracer TracingClient
}

type chatResponse struct {
	content string
}

func (r *chatResponse) Content() string {
	return r.content
}

func NewLLMClient() (*LLMClient, error) {
	apiKey := os.Getenv("OPENAI_API_KEY")
	baseURL := os.Getenv("OPENAI_API_BASE")
	if baseURL == "" {
		baseURL = os.Getenv("OPENAI_BASE_URL")
	}

	if apiKey == "" {
		return nil, fmt.Errorf("OPENAI_API_KEY is not set")
	}

	config := openai.DefaultConfig(apiKey)
	if baseURL != "" {
		config.BaseURL = baseURL
	}

	client := openai.NewClientWithConfig(config)

	return &LLMClient{
		client: client,
		model:  "deepseek-chat", // Defaulting to DeepSeek as per project context
		tracer: NewTracingClient(),
	}, nil
}

func (c *LLMClient) Chat(ctx context.Context, messages []Message) (result ChatResponse, err error) {
	openaiMessages := make([]openai.ChatCompletionMessage, 0, len(messages))
	for _, msg := range messages {
		role := openai.ChatMessageRoleUser
		if msg.GetType() == "system" {
			role = openai.ChatMessageRoleSystem
		}
		openaiMessages = append(openaiMessages, openai.ChatCompletionMessage{
			Role:    role,
			Content: msg.GetContent(),
		})
	}

	// Tracing Start
	traceInputs := map[string]interface{}{
		"messages": openaiMessages,
	}
	span := c.tracer.Start(ctx, "ChatCompletion", traceInputs)

	// OpenAI Response Holder
	var resp openai.ChatCompletionResponse

	// Defer End
	defer func() {
		traceOutputs := map[string]interface{}{}
		if len(resp.Choices) > 0 {
			traceOutputs["content"] = resp.Choices[0].Message.Content
			traceOutputs["usage"] = resp.Usage
		}
		span.End(traceOutputs, err)
	}()

	resp, err = c.client.CreateChatCompletion(
		ctx,
		openai.ChatCompletionRequest{
			Model:       c.model,
			Messages:    openaiMessages,
			Temperature: 0.1, // Low temp for extraction/generation
		},
	)

	if err != nil {
		return nil, err
	}

	if len(resp.Choices) == 0 {
		return nil, fmt.Errorf("no choices returned from LLM")
	}

	return &chatResponse{content: resp.Choices[0].Message.Content}, nil
}
