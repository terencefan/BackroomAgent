import React from 'react';
import type { Item } from '../types';

interface InventoryGridProps {
  items: (Item | null)[];
}

export const InventoryGrid: React.FC<InventoryGridProps> = ({ items }) => {
  // Ensure we always have 36 slots (6x6)
  const slots = Array(36).fill(null).map((_, i) => items[i] || null);

  return (
    <div className="panel inventory-panel">
      <h3 className="panel-header">Inventory</h3>
      <div className="inventory-grid">
        {slots.map((item, index) => (
          <div 
            key={index} 
            className={`inventory-slot ${item ? 'occupied' : ''}`}
            title={item ? item.name : 'Empty Slot'}
          >
            {item ? (item.icon || item.name.substring(0, 2).toUpperCase()) : index + 1}
          </div>
        ))}
      </div>
    </div>
  );
};
