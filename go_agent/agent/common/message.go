package common

type Message interface {
	GetContent() string
	GetType() string
}

type HumanMessage struct {
	Content string
}

func (m HumanMessage) GetContent() string {
	return m.Content
}

func (m HumanMessage) GetType() string {
	return "human"
}

type SystemMessage struct {
	Content string
}

func (m SystemMessage) GetContent() string {
	return m.Content
}

func (m SystemMessage) GetType() string {
	return "system"
}
