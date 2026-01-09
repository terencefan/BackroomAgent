package common

import (
	"context"
	"errors"
	"fmt"
	"log"
	"time"
)

type ExecutionGraph[T AgentState] struct {
	Nodes     map[string]Node[T]
	Edges     map[string][]string // Node -> []NextNodes (Adjacency List)
	StartNode string
	EndNode   string
}

type GraphAgent[T AgentState] struct {
	Graph *ExecutionGraph[T]
	LLM   ModelClient
}

func NewGraphAgent[T AgentState](llm ModelClient) *GraphAgent[T] {
	g := &GraphAgent[T]{
		Graph: &ExecutionGraph[T]{
			Nodes:     make(map[string]Node[T]),
			Edges:     make(map[string][]string),
			StartNode: string(START),
			EndNode:   string(END),
		},
		LLM: llm,
	}
	// Pre-register Start/End
	g.RegisterNode(&markerNode[T]{name: string(START)})
	g.RegisterNode(&markerNode[T]{name: string(END)})
	return g
}

func (g *GraphAgent[T]) RegisterNode(node Node[T]) {
	g.Graph.Nodes[node.Name()] = node
	// If node needs LLM and we have one, inject it
	if llmNode, ok := node.(LLMNode[T]); ok {
		if g.LLM != nil {
			llmNode.SetLLM(g.LLM)
		}
	}
}

type Namer interface {
	Name() string
}

// AddEdge adds a directed edge: from -> to
// from/to must implement Name() string (Node[T] or NodeName)
// Returns error if node not registered
func (g *GraphAgent[T]) AddEdge(from, to Namer) error {
	fromName := from.Name()
	toName := to.Name()

	if _, ok := g.Graph.Nodes[fromName]; !ok {
		return fmt.Errorf("node %s not registered", fromName)
	}
	if _, ok := g.Graph.Nodes[toName]; !ok {
		return fmt.Errorf("node %s not registered", toName)
	}

	g.Graph.Edges[fromName] = append(g.Graph.Edges[fromName], toName)
	return nil
}

// Run executes the graph from Start to End using a queue
func (g *GraphAgent[T]) Run(ctx context.Context, state T, msg Message) error {
	// Initialize Reporting
	report := ExecutionReport{
		StartTime: time.Now(),
		Status:    "Success", // Default to success unless error
		Nodes:     make([]NodeExecutionRecord, 0),
	}

	// Ensure report generation on exit
	defer func() {
		report.EndTime = time.Now()
		report.TotalDuration = report.EndTime.Sub(report.StartTime).String()

		if err := writeReport(report); err != nil {
			log.Printf("Error writing report: %v", err)
		}
	}()

	// Initialize context/state
	state.ReceiveMessage(msg)

	queue := []string{g.Graph.StartNode}
	maxSteps := 100
	step := 0

	for len(queue) > 0 {
		step++
		if step > maxSteps {
			report.Status = "Error: Max Steps Exceeded"
			return errors.New("max execution steps exceeded")
		}

		currentNodeName := queue[0]
		queue = queue[1:]

		node, exists := g.Graph.Nodes[currentNodeName]
		if !exists {
			report.Status = fmt.Sprintf("Error: Node %s not found", currentNodeName)
			return fmt.Errorf("node %s not found", currentNodeName)
		}

		// Execute Node
		log.Printf("Starting node execution: %s", currentNodeName)
		nodeStart := time.Now()

		err := node.Execute(ctx, state)

		nodeDuration := time.Since(nodeStart)
		log.Printf("Finished node execution: %s (Duration: %v)", currentNodeName, nodeDuration)

		// Record Node Execution
		nodeStatus := "Success"
		errMsg := ""
		if err != nil {
			nodeStatus = "Error"
			errMsg = err.Error()
		}

		record := NodeExecutionRecord{
			NodeName:  currentNodeName,
			StartTime: nodeStart,
			EndTime:   time.Now(),
			Duration:  nodeDuration.String(),
			Status:    nodeStatus,
			ErrorMsg:  errMsg,
		}

		report.Nodes = append(report.Nodes, record)

		if err != nil {
			report.Status = fmt.Sprintf("Error in node %s: %v", currentNodeName, err)
			return err
		}

		if currentNodeName == g.Graph.EndNode {
			break
		}

		if nextNodes, ok := g.Graph.Edges[currentNodeName]; ok {
			queue = append(queue, nextNodes...)
		}
	}

	return nil
}
