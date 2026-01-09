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

const ANIMATION_DURATION = 2000;

const InventorySlot: React.FC<{
  item: Item | null;
  index: number;
  onContextMenu: (e: React.MouseEvent, item: Item) => void;
  isResorting: boolean;
}> = ({ item, index, onContextMenu, isResorting }) => {
    // Determine what to display: either current item or the ghost of prev item during removal
    const [displayItem, setDisplayItem] = useState<Item | null>(item);
    const [popup, setPopup] = useState<{ text: string; type: 'increase' | 'decrease'; key: number } | null>(null);
    
    // Refs to track previous prop state and timeout
    const prevPropItemRef = useRef<Item | null>(item);
    const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    useEffect(() => {
        const prev = prevPropItemRef.current;
        const current = item;

        // Immediate Snap if Resorting (No Animations)
        if (isResorting) {
            // Guard against redundant sets (fix for eslint set-state-in-effect)
            if (displayItem !== current && (displayItem?.id !== current?.id || displayItem?.quantity !== current?.quantity)) {
                // eslint-disable-next-line react-hooks/set-state-in-effect
                setDisplayItem(current);
            }
            setPopup(null);
            prevPropItemRef.current = current ? { ...current } : null;
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
                timeoutRef.current = null;
            }
            return;
        }
        
        // Update ref immediately for next time
        prevPropItemRef.current = current ? { ...current } : null;

        // Clear any existing timer to prevent race conditions
        if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
            timeoutRef.current = null;
        }

        let diff = 0;
        let isRemoval = false;

        // Logic to detect meaningful changes
        if (prev && !current) {
            // CASE: Removal
            isRemoval = true;
            diff = -(prev.quantity || 1);
        } else if (!prev && current) {
            // CASE: Addition (New Slot)
            diff = (current.quantity || 1);
        } else if (prev && current && prev.id === current.id) {
            // CASE: Quantity Change
            diff = (current.quantity || 1) - (prev.quantity || 1);
        } else if (prev && current && prev.id !== current.id) {
            // CASE: Swap/Replace (Force reset without animation for now)
            setDisplayItem(current);
            setPopup(null);
            return;
        }

        // Trigger Popup if there's a quant change
        if (diff !== 0) {
              setPopup({
                text: diff > 0 ? `+${diff}` : `${diff}`,
                type: diff > 0 ? 'increase' : 'decrease',
                key: Date.now() 
            });
        }

        // Handle Item Display state
        if (isRemoval) {
            // Keep showing the old item (Ghost)
            setDisplayItem(prev);
            
            // Wait for animation to finish before clearing
            timeoutRef.current = setTimeout(() => {
                setDisplayItem(null);
                setPopup(null);
            }, ANIMATION_DURATION);
        } else {
             // Standard update
             setDisplayItem(current);

             // Clear popup only (item stays)
             if (diff !== 0) {
                 timeoutRef.current = setTimeout(() => {
                    setPopup(null);
                 }, ANIMATION_DURATION);
             }
        }

        // Cleanup on unmount
        return () => {
             if (timeoutRef.current) clearTimeout(timeoutRef.current);
        };
    }, [item, isResorting, displayItem]); // Re-run when props or displayItem changes

  // Logic to separate "Ghost" from "Real"
  // If prop item is null but displayItem exists, it's a ghost (animating out)
  const isGhost = !item && !!displayItem && !isResorting;

  return (
    <div 
      className={`inventory-slot ${displayItem ? 'occupied' : ''} ${displayItem?.category ? `category-${displayItem.category}` : ''} ${popup ? 'animating-change' : ''} ${isGhost ? 'ghost-item' : ''}`}
      onContextMenu={(e) => {
          // Only allow interactions if it's NOT a ghost
          if (item && displayItem) {
              onContextMenu(e, displayItem);
          } else {
              e.preventDefault();
          }
      }}
    >
      {displayItem ? (
        <>
          <span className="item-icon">{displayItem.icon || displayItem.name.substring(0, 2).toUpperCase()}</span>
          {(displayItem.quantity || 1) > 1 && (
            <span className="item-quantity">{displayItem.quantity}</span>
          )}
          <div className="item-tooltip">
            <span className="tooltip-quantity">x{displayItem.quantity || 1}</span>
            <div className="tooltip-title">{displayItem.name}</div>
            <div className="tooltip-desc">{displayItem.description || "暂无描述"}</div>
            <div className="tooltip-hint" style={{fontSize: '0.7em', color: '#666', marginTop: '4px'}}>右键打开菜单</div>
          </div>
          {popup && (
              <div key={popup.key} className={`qty-change-popup ${popup.type}`}>
                  {popup.text}
              </div>
          )}
        </>
      ) : (
         <span className="empty-slot-number">{index + 1}</span>
      )}
    </div>
  );
};

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

  // --- Animation & Sorting Logic ---
  const [displaySlots, setDisplaySlots] = useState<(Item | null)[]>(() => {
     // Initialize with sorted items immediately to prevent "addition" animation on first load
     const validItems = items.filter((item): item is Item => item !== null);
     const sortedTarget = [...validItems].sort((a, b) => {
         const orderA = CATEGORY_ORDER[a.category || ''] || 99;
         const orderB = CATEGORY_ORDER[b.category || ''] || 99;
         return orderA - orderB;
     });
     return Array(36).fill(null).map((_, i) => sortedTarget[i] || null);
  });
  
  const [isResorting, setIsResorting] = useState(false);
  const isFirstRender = useRef(true);
  const sortTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
     // Prepare the "Target" state (Sorted & Padded)
     const validItems = items.filter((item): item is Item => item !== null);
     const sortedTarget = [...validItems].sort((a, b) => {
         const orderA = CATEGORY_ORDER[a.category || ''] || 99;
         const orderB = CATEGORY_ORDER[b.category || ''] || 99;
         return orderA - orderB;
     });
     // Map ID -> Item for constant access
     const nextItemsMap = new Map();
     validItems.forEach(it => nextItemsMap.set(it.id, it));

     if (isFirstRender.current) {
         // Initial Load - Already handled by useState initializer
         isFirstRender.current = false;
         return;
     }

     // --- Calculate Transition State ---
     
     if (sortTimeoutRef.current) {
         clearTimeout(sortTimeoutRef.current);
     }

     // 1. Create a working copy of current slots
     const newDisplaySlots = [...displaySlots];
     
     // 2. Track which items from 'next' have been placed
     const placedIds = new Set<string>();

     // 3. Update existing items in place
     for (let i = 0; i < 36; i++) {
         const currentSlotItem = newDisplaySlots[i];
         if (currentSlotItem) {
             if (nextItemsMap.has(currentSlotItem.id)) {
                 // Item still exists: Update it in place
                 newDisplaySlots[i] = nextItemsMap.get(currentSlotItem.id)!;
                 placedIds.add(currentSlotItem.id);
             } else {
                 // Item removed: Set to null (Triggers Ghost Animation in InventorySlot)
                 newDisplaySlots[i] = null;
             }
         }
     }

     const newItemsToAdd: Item[] = [];
     nextItemsMap.forEach((item, id) => {
         if (!placedIds.has(id)) {
             newItemsToAdd.push(item);
         }
     });

     // 4. Render Step 1: Removals & Updates ONLY (New items are HELD BACK)
     // This allows removal animations to play out in empty spaces.
     // newItemsToAdd will be added AFTER the sort phase.
     
      
     setDisplaySlots(newDisplaySlots);

     // 5. Schedule Sort & Additions
     // Phase 2: Sort (Clear ghosts & compact) -> Phase 3: Add new Items
     
     sortTimeoutRef.current = setTimeout(() => {
         // --- Phase 2: Sort (Compact existing) ---
         // Construct the list of items that are NOT new, but sorted
         // We can do this by filtering sortedTarget to exclude new items, BUT
         // simpler is to just take the final sortedTarget.
         // Wait, user wants: Remove -> Sort (Compact) -> Add.
         
         // If we just jump to final sorted state, the new items appear instantly in their sorted position.
         // The user wants "Sort (make room) -> then Add".
         // So we need an intermediate state: [Existing Sorted Items, ...Empty, ...Empty]
         
         const existingSorted = sortedTarget.filter(t => !newItemsToAdd.find(n => n.id === t.id));
         const intermediateSlots = Array(36).fill(null).map((_, i) => existingSorted[i] || null);

         // Apply Sort (Compact)
         setIsResorting(true);
         setDisplaySlots(intermediateSlots);
         
         // --- Phase 3: Add New Items ---
         // Give a small delay for the sort to "snap" and clear flags, then add the new items.
         setTimeout(() => {
             setIsResorting(false); // Enable animations again
             
             // Now set the full final state (including new items)
             // The new items will appear in their sorted positions. 
             // Since they were NULL in 'intermediateSlots', they will trigger 'Addition' diff (+X animation).
             
             const finalSlots = Array(36).fill(null).map((_, i) => sortedTarget[i] || null);
             setDisplaySlots(finalSlots);
         }, 100); // 100ms delay after compacting

         sortTimeoutRef.current = null;
     }, ANIMATION_DURATION); 

     return () => {
         if (sortTimeoutRef.current) clearTimeout(sortTimeoutRef.current);
     };

     // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [items]);

  return (
    <div className="panel inventory-panel">
      <h3 className="panel-header">物品栏</h3>
      <div className="inventory-grid">
        {displaySlots.map((item, index) => (
          <InventorySlot 
            key={index} 
            item={item} 
            index={index} 
            onContextMenu={handleContextMenu} 
            isResorting={isResorting}
          />
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
