package common

import "context"

const (
	START NodeName = "Start"
	END   NodeName = "End"
)

type NodeName string

func (n NodeName) Name() string {
	return string(n)
}

// Simple implementations for Start/End as markers mostly
type markerNode[T AgentState] struct {
	name string
}

func (n *markerNode[T]) Name() string                               { return n.name }
func (n *markerNode[T]) Execute(ctx context.Context, state T) error { return nil }
