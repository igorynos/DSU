package registry

import (
	"github.com/igorynos/DSU/internal/device"
	"sync"
	"time"
)

type EventType string

const (
	Added   EventType = "added"
	Updated EventType = "updated"
	Removed EventType = "removed"
)

type Event struct {
	Type   EventType
	Device device.Device
}
type Registry struct {
	mu      sync.RWMutex
	devices map[string]device.Device
	ttl     time.Duration
	events  chan Event
}

func New(ttl time.Duration) *Registry {
	return &Registry{devices: map[string]device.Device{}, ttl: ttl, events: make(chan Event, 64)}
}
func (r *Registry) Events() <-chan Event { return r.events }
func (r *Registry) Upsert(d device.Device) {
	r.mu.Lock()
	_, ok := r.devices[d.Key()]
	r.devices[d.Key()] = d
	r.mu.Unlock()
	typ := Added
	if ok {
		typ = Updated
	}
	select {
	case r.events <- Event{typ, d}:
	default:
	}
}
func (r *Registry) List() []device.Device {
	r.mu.RLock()
	defer r.mu.RUnlock()
	out := make([]device.Device, 0, len(r.devices))
	for _, d := range r.devices {
		out = append(out, d)
	}
	return out
}
func (r *Registry) Prune(now time.Time) {
	r.mu.Lock()
	defer r.mu.Unlock()
	for k, d := range r.devices {
		if now.Sub(d.LastSeen) > r.ttl {
			delete(r.devices, k)
			select {
			case r.events <- Event{Removed, d}:
			default:
			}
		}
	}
}
