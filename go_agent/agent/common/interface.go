package common

import "context"

type AgentState interface {
	AddLog(msg string)
	ReceiveMessage(msg Message)
}

type Agent interface {
	Run(ctx context.Context, msg Message) error
}

type ChatResponse interface {
	Content() string
}

type ModelClient interface {
	Chat(ctx context.Context, messages []Message) (ChatResponse, error)
}

type LLMNode[T AgentState] interface {
	Node[T]
	SetLLM(client ModelClient)
	GetSystemPrompt() string
	GetUserPrompt() string
}

type Node[T AgentState] interface {
	Name() string
	Execute(ctx context.Context, state T) error
}
