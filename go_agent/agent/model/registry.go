package model

import (
	"sync"

	"github.com/google/uuid"
)

// GlobalIDRegistry is a thread-safe singleton to store Name -> UUID mappings.
// This ensures that across the entire process lifetime, the same name always gets the same ID.
type idRegistry struct {
	mu  sync.RWMutex
	ids map[string]string
}

var (
	registryInstance *idRegistry
	registryOnce     sync.Once
)

// GetRegistry returns the singleton instance of IDRegistry
func GetRegistry() *idRegistry {
	registryOnce.Do(func() {
		registryInstance = &idRegistry{
			ids: make(map[string]string),
		}
	})
	return registryInstance
}

// GetID returns an existing ID for the given name, or generates a new one.
// It is safe for concurrent use.
func (r *idRegistry) GetID(name string) string {
	// 1. Try Read Lock first for performance
	r.mu.RLock()
	id, exists := r.ids[name]
	r.mu.RUnlock()

	if exists {
		return id
	}

	// 2. Write Lock to generate and store
	r.mu.Lock()
	defer r.mu.Unlock()

	// Double-check locking pattern to avoid race condition where ID appeared between RUnlock and Lock
	if id, exists := r.ids[name]; exists {
		return id
	}

	newID := uuid.New().String()
	r.ids[name] = newID
	return newID
}
