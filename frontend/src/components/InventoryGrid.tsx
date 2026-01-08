import React, { useEffect, useRef, useState } from 'react';
import type { Item } from '../types';

interface InventoryGridProps {
  items: (Item | null)[];
  onUseItem?: (item: Item) => void;
  onDropItem?: (item: Item, mode: 'one' | 'half' | 'all') => void;
  isLoading?: boolean;
}

const CATEGORY_ORDER: Record<string, number> = {
  'resource': 1,
  'medical': 2,
  'weapon': 3,
  'tool': 4,
  'document': 5,
  'special': 6
};

// ... existing code ...

export const InventoryGrid: React.FC<InventoryGridProps> = ({ items, onUseItem, onDropItem, isLoading }) => {
  const [contextMenu, setContextMenu] = useState<{
    visible: boolean;
    x: number;
    y: number;
    item: Item | null;
  }>({ visible: false, x: 0, y: 0, item: null });

  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setContextMenu({ ...contextMenu, visible: false });
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [contextMenu]);

  const handleContextMenu = (e: React.MouseEvent, item: Item) => {
    e.preventDefault();
    if (isLoading) return; // Prevent interaction during loading
    
    setContextMenu({
      visible: true,
      x: e.clientX,
      y: e.clientY,
      item: item
    });
  };

  const handleAction = (action: 'use' | 'drop', param?: 'one' | 'half' | 'all') => {
    if (!contextMenu.item) return;

    if (action === 'use' && onUseItem) {
      onUseItem(contextMenu.item);
    } else if (action === 'drop' && onDropItem && param) {
      onDropItem(contextMenu.item, param);
    }
    setContextMenu({ ...contextMenu, visible: false });
  };

  // Filter out nulls, sort items, and then pad with nulls to 36 slots
  const validItems = items.filter((item): item is Item => item !== null);
  
  const sortedItems = [...validItems].sort((a, b) => {
    const orderA = CATEGORY_ORDER[a.category || ''] || 99;
    const orderB = CATEGORY_ORDER[b.category || ''] || 99;
    return orderA - orderB;
  });

  // Ensure we always have 36 slots (6x6)
  const slots = Array(36).fill(null).map((_, i) => sortedItems[i] || null);

  return (
    <div className="panel inventory-panel">
      <h3 className="panel-header">物品栏</h3>
      <div className="inventory-grid">
        {slots.map((item, index) => (
          <div 
            key={index} 
            className={`inventory-slot ${item ? 'occupied' : ''} ${item?.category ? `category-${item.category}` : ''}`}
            onContextMenu={(e) => item ? handleContextMenu(e, item) : e.preventDefault()}
          >
            {item ? (
              <>
                <span className="item-icon">{item.icon || item.name.substring(0, 2).toUpperCase()}</span>
                {(item.quantity || 1) > 1 && (
                  <span className="item-quantity">{item.quantity}</span>
                )}
                <div className="item-tooltip">
                  <span className="tooltip-quantity">x{item.quantity || 1}</span>
                  <div className="tooltip-title">{item.name}</div>
                  <div className="tooltip-desc">{item.description || "暂无描述"}</div>
                  <div className="tooltip-hint" style={{fontSize: '0.7em', color: '#666', marginTop: '4px'}}>右键打开菜单</div>
                </div>
              </>
            ) : (
               <span className="empty-slot-number">{index + 1}</span>
            )}
          </div>
        ))}
      </div>

       {contextMenu.visible && contextMenu.item && (
        <div 
          ref={menuRef}
          className="context-menu" 
          style={{ top: contextMenu.y, left: contextMenu.x }}
        >
            <div className="context-menu-item" onClick={() => handleAction('use')}>
                使用
            </div>
            <div className="context-menu-divider"></div>
            <div className="context-menu-item submenu-trigger">
                丢弃
                <div className="submenu">
                    <div className="context-menu-item" onClick={() => handleAction('drop', 'one')}>
                        丢弃一个
                    </div>
                    <div className="context-menu-item" onClick={() => handleAction('drop', 'half')}>
                        丢弃一半
                    </div>
                    <div className="context-menu-item" onClick={() => handleAction('drop', 'all')}>
                        丢弃全部
                    </div>
                </div>
            </div>
        </div>
      )}
    </div>
  );
};
