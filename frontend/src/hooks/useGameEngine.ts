import { useEffect, useMemo, useRef, useState } from 'react';
import type { DiceRoll, GameState, Item, Message, StreamChunk } from '../types';
import { EventType, StreamChunkType } from '../types';

export function useGameEngine() {
  // ==========================================
  // 1. State & Refs
  // ==========================================
  const [messages, setMessages] = useState<Message[]>([]);
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLevelTransition, setIsLevelTransition] = useState(false);
  const [diceAnimation, setDiceAnimation] = useState<DiceRoll | null>(null);

  const isInitialized = useRef(false);
  const isAnimating = useRef(false);

  // Queue system
  const pendingQueueRef = useRef<StreamChunk[]>([]);
  // Logic/Dice Lock system
  const pendingDiceRef = useRef<DiceRoll | null>(null);
  const lastLogicMsgIdRef = useRef<number | null>(null);
  const logicConfirmStatusRef = useRef(false);
  
  // ==========================================
  // 2. Session Management
  // ==========================================
  const sessionId = useMemo(() => {
    let id = localStorage.getItem('session_id');
    if (!id) {
        id = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        localStorage.setItem('session_id', id);
    }
    return id;
  }, []);

  // ==========================================
  // 3. Animation Control & Logic Locks
  // ==========================================

  const triggerDiceAnimation = (dice: DiceRoll) => {
      isAnimating.current = true;
      setDiceAnimation(dice);
      pendingDiceRef.current = null;
  };

  /**
   * Checks if valid conditions exist to trigger a pending dice roll.
   * (e.g., User has clicked confirm on the logic event).
   */
  const checkAndTriggerDice = () => {
    setMessages(prev => {
        const waitingId = lastLogicMsgIdRef.current;
        if (!waitingId) {
             // No logic event blocking? Play immediately.
             if (pendingDiceRef.current) triggerDiceAnimation(pendingDiceRef.current);
             return prev;
        }
        
        const msg = prev.find(m => m.id === waitingId);
        if (msg && msg.logicEventConfirmed) {
            // Confirmed + Dice Pending = Play
            if (pendingDiceRef.current) {
                 const dice = pendingDiceRef.current;
                 setTimeout(() => triggerDiceAnimation(dice!), 0);
            }
        }
        return prev;
    });
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

  const handleLogicEventConfirm = (msgId: number) => {
      logicConfirmStatusRef.current = true;
      setMessages(prev => prev.map(m => {
          if (m.id === msgId) return { ...m, logicEventConfirmed: true };
          return m;
      }));

      // If we have a pending dice roll waiting for this, fire it
      if (pendingDiceRef.current && lastLogicMsgIdRef.current === msgId) {
          triggerDiceAnimation(pendingDiceRef.current);
      }
  };

  // ==========================================
  // 4. Queue Processing Engine
  // ==========================================

  /**
   * Applies a single chunk to the state.
   */
  const handleChunkLive = (chunk: StreamChunk) => {
    console.log("Processing Live Chunk:", chunk);
    
    switch (chunk.type) {
      case StreamChunkType.MESSAGE:
        setMessages(prev => [...prev, {
          id: Date.now(),
          sender: chunk.sender || 'dm',
          text: chunk.text || '',
          logicEvent: chunk.logicEvent,
          options: chunk.options
        }]);
        
        if (chunk.logicEvent) {
             setMessages(prev => {
                const last = prev[prev.length - 1]; 
                lastLogicMsgIdRef.current = last.id; 
                logicConfirmStatusRef.current = false;
                last.logicEventConfirmed = false;
                return prev;
             });
        }

        if (gameState) {
             isAnimating.current = true; 
        } else {
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

      case StreamChunkType.SETTLEMENT:
        setMessages(prev => [...prev, {
            id: Date.now(),
            sender: 'system',
            text: '', 
            settlement: chunk.delta
        }]);
        tryProcessQueue();
        break;

      case StreamChunkType.DICE_ROLL:
        pendingDiceRef.current = chunk.dice;
        if (!lastLogicMsgIdRef.current) {
             triggerDiceAnimation(chunk.dice);
        } else {
             checkAndTriggerDice();
        }
        tryProcessQueue();
        break;

      case StreamChunkType.STATE:
        if (chunk.state) {
            if (gameState && chunk.state.level !== gameState.level) {
                // Level Transition
                setIsLevelTransition(true);
                isAnimating.current = true; 
                
                setTimeout(() => {
                    setGameState(chunk.state);
                    setTimeout(() => {
                        setIsLevelTransition(false);
                        isAnimating.current = false;
                        tryProcessQueue();
                    }, 500); 
                }, 500); 
            } else {
                setGameState(chunk.state);
                tryProcessQueue();
            }
        } else {
             tryProcessQueue();
        }
        break;

      case StreamChunkType.SUGGESTIONS:
        setMessages(prev => {
            if (prev.length === 0) return prev;
            const lastMsg = { ...prev[prev.length - 1] };
            lastMsg.options = chunk.options;
            return [...prev.slice(0, -1), lastMsg];
        });
        tryProcessQueue();
        break;

      case StreamChunkType.LOGIC_EVENT:
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

  /**
   * Attempts to process the next item in the queue.
   * Respects locks (Animation, Logic Events).
   */
  const tryProcessQueue = () => {
      if (isAnimating.current) return;
      
      const queue = pendingQueueRef.current;
      if (queue.length === 0) return;
      
      const nextChunk = queue[0]; 

      // Logic Event Lock: Block everything except DICE_ROLL
      if (lastLogicMsgIdRef.current !== null) {
          if (nextChunk.type !== StreamChunkType.DICE_ROLL) {
               return; 
          }
      }

      queue.shift(); 
      handleChunkLive(nextChunk);
  };

  /**
   * Adds a chunk to the processing queue.
   * Handles "patching" logic for updates (Suggestions, late LogicEvents) to avoid visual popping.
   */
  const enqueueChunk = async (chunk: StreamChunk) => {
    // Patching logic for late updates targetting the previous message
    if (chunk.type === StreamChunkType.LOGIC_EVENT || chunk.type === StreamChunkType.SUGGESTIONS) {
        const queue = pendingQueueRef.current;
        if (queue.length > 0) {
            // Check last message in queue
            for (let i = queue.length - 1; i >= 0; i--) {
                const target = queue[i];
                if (target.type === StreamChunkType.MESSAGE) {
                    if (chunk.type === StreamChunkType.LOGIC_EVENT) {
                        target.logicEvent = chunk.event;
                    } else {
                        target.options = chunk.options;
                    }
                    return; // Handled in place
                }
            }
        }
    }

    pendingQueueRef.current.push(chunk);
    tryProcessQueue();
  };


  // ==========================================
  // 5. Network Layer
  // ==========================================

  const streamRequest = async (
      payload: any, 
      onSuccess?: () => void, 
      onError?: (err: any) => void
  ) => {
      try {
        setIsLoading(true);
        const response = await fetch('/api/chat', { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
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
                    await enqueueChunk(chunk);
                } catch (e) {
                    console.error('Error parsing JSON chunk', e);
                }
            }
        }
        
        setIsLoading(false);
        if (onSuccess) onSuccess();

      } catch (error) {
        console.error("Stream request failed:", error);
        setIsLoading(false);
        if (onError) onError(error);
      }
  };

  const sendGameEvent = (text: string, eventType: EventType, eventData?: any, hidden: boolean = false) => {
      if (!hidden) {
          setMessages(prev => [...prev, { id: Date.now(), sender: 'player', text }]);
      }
      
      if (!gameState) return;

      streamRequest({
          event: { type: eventType, ...eventData },
          player_input: text,
          session_id: sessionId,
          current_state: gameState
      }, undefined, () => {
         setMessages(prev => [...prev, { id: Date.now() + 1, sender: 'system', text: "错误：与后端的连接已丢失。" }]);
      });
  };

  // Fetch initial state on mount
  useEffect(() => {
    if (isInitialized.current) return;
    isInitialized.current = true;

    streamRequest({
        event: { type: EventType.INIT },
        player_input: '',
        session_id: sessionId,
        current_state: null
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  },[]);


  // ==========================================
  // 6. UI Handlers
  // ==========================================

  const handleSendMessage = (text: string, hidden: boolean = false) => {
    sendGameEvent(text, EventType.MESSAGE, undefined, hidden);
  };

  const handleUseItem = (item: Item) => {
    sendGameEvent(`使用 ${item.name}`, EventType.USE, { item_id: item.id, quantity: 1 });
  };

  const handleDropItem = (item: Item, mode: 'one' | 'half' | 'all') => {
    let quantity = 1;
    const currentQty = item.quantity || 1;
    
    if (mode === 'half') quantity = Math.ceil(currentQty / 2);
    else if (mode === 'all') quantity = currentQty;
    
    sendGameEvent(`丢弃 ${quantity} 个 ${item.name}`, EventType.DROP, { item_id: item.id, quantity });
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
