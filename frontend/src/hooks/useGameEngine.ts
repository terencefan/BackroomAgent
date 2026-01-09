import { useEffect, useMemo, useRef, useState } from 'react';
import type { DiceRoll, GameState, Item, Message, StreamChunk } from '../types';
import { EventType, StreamChunkType } from '../types';

export function useGameEngine() {
  // State
  const [messages, setMessages] = useState<Message[]>([]);
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLevelTransition, setIsLevelTransition] = useState(false);
  const [diceAnimation, setDiceAnimation] = useState<DiceRoll | null>(null);
  const isInitialized = useRef(false);

  // Queue system for serial processing
  const pendingQueueRef = useRef<StreamChunk[]>([]);
  const isAnimating = useRef(false);

  // Queue to hold dice result if it arrives before user confirmation
  const pendingDiceRef = useRef<DiceRoll | null>(null);
  // Track the ID of the message that initiated the current logic wait
  const lastLogicMsgIdRef = useRef<number | null>(null);
  const logicConfirmStatusRef = useRef(false);
  
  const sessionId = useMemo(() => {
    let id = localStorage.getItem('session_id');
    if (!id) {
        id = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        localStorage.setItem('session_id', id);
    }
    return id;
  }, []);

  const triggerDiceAnimation = (dice: DiceRoll) => {
      isAnimating.current = true;
      setDiceAnimation(dice);
      pendingDiceRef.current = null;
  };

  const checkAndTriggerDice = () => {
    // This helper tries to trigger animation if conditions are met
    // We need access to current messages state to see if it matches lastLogicMsgIdRef and is confirmed
    setMessages(prev => {
        const waitingId = lastLogicMsgIdRef.current;
        if (!waitingId) {
             // No waiting logic event? Just play if we have dice
             if (pendingDiceRef.current) triggerDiceAnimation(pendingDiceRef.current);
             return prev;
        }
        
        const msg = prev.find(m => m.id === waitingId);
        if (msg && msg.logicEventConfirmed) {
            // It IS confirmed, and we have dice pending
            if (pendingDiceRef.current) {
                 // We can't call triggerDiceAnimation here strictly because it calls setMessages (loop)
                 // But we can defer it
                 const dice = pendingDiceRef.current; // Capture ref value
                 setTimeout(() => triggerDiceAnimation(dice!), 0);
            }
        }
        return prev;
    });
  };

  const tryProcessQueue = () => {
      if (isAnimating.current) return;
      
      const queue = pendingQueueRef.current;
      if (queue.length === 0) return;
      
      const nextChunk = queue[0]; // Peek

      // Check if we are in a logic event sequence (Dice Roll pending/active)
      if (lastLogicMsgIdRef.current !== null) {
          // While waiting for Logic/Dice resolution, we BLOCK everything EXCEPT the Dice Roll itself.
          // This ensures:
          // 1. Narrative result (MESSAGE) doesn't show before animation
          // 2. State updates don't happen before animation
          // 3. Dice Roll data (background) CAN pass through to ready the animation
          if (nextChunk.type !== StreamChunkType.DICE_ROLL) {
               return; 
          }
      }

      queue.shift(); // Remove from queue
      handleChunkLive(nextChunk);
  };

  const handleAnimationComplete = () => {
      isAnimating.current = false;
      tryProcessQueue();
  };

   const handleDiceAnimationComplete = () => {
        if (lastLogicMsgIdRef.current) {
            setMessages(prev => prev.map(m => {
                if (m.id === lastLogicMsgIdRef.current) {
                    return { ...m, logicRollResult: diceAnimation?.result };
                }
                return m;
            }));
            lastLogicMsgIdRef.current = null;
        }
        setDiceAnimation(null);
        handleAnimationComplete();
   }


  const handleChunkLive = (chunk: StreamChunk) => {
    console.log("Processing Live Chunk:", chunk);
    
    switch (chunk.type) {
      case StreamChunkType.MESSAGE:
        setMessages(prev => [...prev, {
          id: Date.now(),
          sender: chunk.sender || 'dm',
          text: chunk.text || '',
          // Apply any patched properties if they exist on the chunk object
          logicEvent: (chunk as any).logicEvent,
          options: (chunk as any).options
        }]);
        
        // If this message has a logicEvent, we need to track its ID for future dice rolls
        // We can't access legitimate ID cleanly here because setState is async/functional.
        // We defer tracking to the effect or rely on functional update side-effect (safe enough for refs).
        if ((chunk as any).logicEvent) {
             setMessages(prev => {
                const last = prev[prev.length - 1]; // This is the new one
                lastLogicMsgIdRef.current = last.id; 
                logicConfirmStatusRef.current = false;
                // We also need to reset confirmation state just in case
                last.logicEventConfirmed = false;
                return prev;
             });
        }

        // Only block for animation if the UI is actually visible (gameState exists)
        // This prevents deadlock on initial load where MESSAGE/INIT arrives before STATE
        if (gameState) {
             isAnimating.current = true; // Will be cleared by ChatBox callback
        } else {
             // UI not ready/visible, assume "fast forward" or simple loading
             // Don't block queue
             setTimeout(tryProcessQueue, 0);
        }
        break;
      
      case StreamChunkType.INIT:
        setMessages(prev => [...prev, {
          id: Date.now(),
          sender: 'init',
          text: chunk.text || '',
        }]);

        if (gameState) {
            isAnimating.current = true;
        } else {
            setTimeout(tryProcessQueue, 0);
        }
        break;

      case StreamChunkType.DICE_ROLL:
        // Logic for Dice Roll handling
        pendingDiceRef.current = chunk.dice;
        if (!lastLogicMsgIdRef.current) {
             triggerDiceAnimation(chunk.dice);
        } else {
             checkAndTriggerDice();
        }
        break;

      case StreamChunkType.STATE:
        // Update Game State
        if (chunk.state) {
            if (gameState && chunk.state.level !== gameState.level) {
                setIsLevelTransition(true);
                // Animations are handled via CSS transitions, but we can't block queue easily on CSS
                // unless we set isAnimating. 
                // For level transition (~1s), let's block.
                isAnimating.current = true; 
                
                setTimeout(() => {
                    setGameState(chunk.state);
                    setTimeout(() => {
                        setIsLevelTransition(false);
                        isAnimating.current = false;
                        tryProcessQueue();
                    }, 500); // Wait for fade in
                }, 500); // Wait for fade out
            } else {
                setGameState(chunk.state);
                // Don't block queue for simple state updates
                tryProcessQueue();
            }
        } else {
             tryProcessQueue();
        }
        break;

      case StreamChunkType.SUGGESTIONS:
        // If suggestions arrive late and target displayed message
        setMessages(prev => {
            if (prev.length === 0) return prev;
            const lastMsg = { ...prev[prev.length - 1] };
            lastMsg.options = chunk.options;
            return [...prev.slice(0, -1), lastMsg];
        });
        tryProcessQueue();
        break;

      case StreamChunkType.LOGIC_EVENT:
        // If logic event arrives late and targets displayed message
        setMessages(prev => {
            if (prev.length === 0) return prev;
            const lastMsg = { ...prev[prev.length - 1] };
            lastMsg.logicEvent = chunk.event;
            lastMsg.logicEventConfirmed = false;
            lastLogicMsgIdRef.current = lastMsg.id;
            return [...prev.slice(0, -1), lastMsg];
        });
        tryProcessQueue();
        break;
    }
  };

  const processStreamChunk = async (chunk: StreamChunk) => {
    // Items that modify existing messages (LogicEvent, Suggestions) need special handling
    // If they modify a message that is currently in the queue, we patch it there.
    if (chunk.type === StreamChunkType.LOGIC_EVENT || chunk.type === StreamChunkType.SUGGESTIONS) {
        const queue = pendingQueueRef.current;
        if (queue.length > 0) {
            // Check if the last item in queue is a valid target (MESSAGE)
            // Note: We scan from end.
            for (let i = queue.length - 1; i >= 0; i--) {
                const target = queue[i];
                if (target.type === StreamChunkType.MESSAGE) {
                    if (chunk.type === StreamChunkType.LOGIC_EVENT) {
                        // Patch logic event onto the message chunk
                        (target as any).logicEvent = chunk.event;
                    } else {
                        // Patch options
                        (target as any).options = chunk.options;
                    }
                    return; // Handled in queue
                }
            }
        }
    }

    // Add to queue
    pendingQueueRef.current.push(chunk);
    tryProcessQueue();
  };

  // Fetch initial state on mount
  useEffect(() => {
    if (isInitialized.current) return;
    isInitialized.current = true;

    const fetchInitialState = async () => {
      try {
        setIsLoading(true);
        const response = await fetch('/api/chat', { 
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                event: { type: EventType.INIT },
                player_input: '',
                session_id: sessionId,
                current_state: null
            })
        });
        
        if (!response.ok) throw new Error('Network response was not ok');

        const reader = response.body?.getReader();
        if (!reader) throw new Error('Response body is not readable');

        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const chunk = JSON.parse(line);
                    await processStreamChunk(chunk);
                } catch (e) {
                    console.error('Error parsing JSON chunk', e);
                }
            }
        }
        setIsLoading(false);

      } catch (error) {
        console.error("Failed to fetch initial state:", error);
        setIsLoading(false);
      }
    };

    fetchInitialState();
  },[]);

  const processGameEvent = async (text: string, eventType: EventType, eventData?: { item_id?: string, quantity?: number }, hidden: boolean = false) => {
    // Add player message immediately ONLY if not hidden
    if (!hidden) {
        const playerMsg = { id: Date.now(), sender: 'player' as const, text };
        setMessages(prev => [...prev, playerMsg]);
    }
    
    // Guard clause if state isn't loaded yet (though UI should prevent this)
    if (!gameState) return;

    try {
      setIsLoading(true);
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          event: { type: eventType, ...eventData },
          player_input: text,
          session_id: sessionId,
          current_state: gameState
        }),
      });

      if (!response.ok) throw new Error('Network response was not ok');

      const reader = response.body?.getReader();
      if (!reader) throw new Error('Response body is not readable');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        
        // Keep the last partial line in the buffer
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const chunk = JSON.parse(line);
            await processStreamChunk(chunk);
          } catch (e) {
            console.error('Error parsing JSON chunk', e);
          }
        }
      }
      setIsLoading(false);

    } catch (error) {
      console.error("Error communicating with backend:", error);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        sender: 'system',
        text: "错误：与后端的连接已丢失。"
      }]);
      setIsLoading(false);
    } 
  };

  const handleLogicEventConfirm = (msgId: number) => {
      // 1. Mark message as confirmed
      logicConfirmStatusRef.current = true;
      setMessages(prev => prev.map(m => {
          if (m.id === msgId) return { ...m, logicEventConfirmed: true };
          return m;
      }));

      // 2. Check if we have a pending dice roll waiting for this confirmation
      // If pendingDiceRef is set, fire it!
      if (pendingDiceRef.current && lastLogicMsgIdRef.current === msgId) {
          triggerDiceAnimation(pendingDiceRef.current);
      }
  };

  const handleSendMessage = (text: string, hidden: boolean = false) => {
    processGameEvent(text, EventType.MESSAGE, undefined, hidden);
  };

  const handleUseItem = (item: Item) => {
    processGameEvent(`使用 ${item.name}`, EventType.USE, { item_id: item.id, quantity: 1 });
  };

  const handleDropItem = (item: Item, mode: 'one' | 'half' | 'all') => {
    let quantity = 1;
    const currentQty = item.quantity || 1;
    
    if (mode === 'half') {
      quantity = Math.ceil(currentQty / 2);
    } else if (mode === 'all') {
      quantity = currentQty;
    }
    
    processGameEvent(`丢弃 ${quantity} 个 ${item.name}`, EventType.DROP, { item_id: item.id, quantity });
  };

  const handleOptionSelect = (msgId: number, option: string) => {
      setMessages(prev => prev.map(m => 
        m.id === msgId ? { ...m, selectedOption: option } : m
      ));
  };


  return {
      messages,
      gameState,
      isLoading,
      isLevelTransition,
      diceAnimation,
      handleSendMessage,
      handleUseItem,
      handleDropItem,
      handleLogicEventConfirm,
      handleAnimationComplete,
      handleDiceAnimationComplete,
      handleOptionSelect
  };
}
