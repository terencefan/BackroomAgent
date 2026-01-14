import { useEffect, useMemo, useRef, useState } from 'react';
import type { DiceRoll, GameState, Item, Message, StreamChunk, StreamInitRequest, StreamMessageRequest } from '../types';
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
  const lastMsgIdRef = useRef<number>(0);

  const generateMsgId = () => {
      let newId = Date.now();
      if (newId <= lastMsgIdRef.current) {
          newId = lastMsgIdRef.current + 1;
      }
      lastMsgIdRef.current = newId;
      return newId;
  };
  
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
    // console.log("Processing Live Chunk:", chunk);
    console.log(`[Engine] apply: ${chunk.type}`, chunk);
    
    switch (chunk.type) {
      case StreamChunkType.MESSAGE:
        setMessages(prev => [...prev, {
          id: generateMsgId(),
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
          id: generateMsgId(),
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
            id: generateMsgId(),
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
      // console.log('tryProcessQueue', isAnimating.current, pendingQueueRef.current.length);
      if (isAnimating.current) return;
      
      const queue = pendingQueueRef.current;
      if (queue.length === 0) return;
      
      let nextChunkIndex = 0;

      // Logic Event Lock: Block everything except DICE_ROLL
      if (lastLogicMsgIdRef.current !== null) {
          // Scan for a DICE_ROLL chunk in the queue to let it jump ahead
          const diceIndex = queue.findIndex(c => c.type === StreamChunkType.DICE_ROLL);
          if (diceIndex !== -1) {
              nextChunkIndex = diceIndex;
          } else {
              // No dice roll found? Then we are truly blocked.
              return; 
          }
      }

      const nextChunk = queue[nextChunkIndex];
      // Remove from the found position
      queue.splice(nextChunkIndex, 1);
      
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

  const streamRequestSSE = async (
      payload: StreamInitRequest | StreamMessageRequest,
      onSuccess?: () => void,
      onError?: (err: unknown) => void
  ) => {
      try {
        setIsLoading(true);
        
        // 发送 POST 请求，接收 SSE 流
        const response = await fetch('/api/chat/stream', {
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
            
            // 解析 SSE 格式: "data: {...}\n\n"
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (!line.trim()) continue;
                
                // SSE 格式: "data: {...}"
                if (line.startsWith('data: ')) {
                    try {
                        const jsonStr = line.substring(6); // 移除 "data: " 前缀
                        const chunk = JSON.parse(jsonStr);
                        console.log(`[DungeonMaster] recv: ${chunk.type}`, chunk);
                        
                        // 处理 init_context
                        if (chunk.type === StreamChunkType.INIT_CONTEXT) {
                            // 接收完整上下文（历史消息和游戏状态）
                            // 这里可以用于恢复会话状态，但通常 init 时消息历史为空
                            if (chunk.game_state) {
                                setGameState(chunk.game_state);
                            }
                            continue; // 不加入消息队列
                        }
                        
                        await enqueueChunk(chunk);
                    } catch (e) {
                        console.error('Error parsing SSE chunk', e, line);
                    }
                }
            }
        }
        
        setIsLoading(false);
        if (onSuccess) onSuccess();

      } catch (error) {
        console.error("DungeonMaster stream request failed:", error);
        setIsLoading(false);
        if (onError) onError(error);
      }
  };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const sendGameEvent = (text: string, eventType: EventType, eventData?: any, hidden: boolean = false) => {
      if (!hidden) {
          setMessages(prev => [...prev, { id: generateMsgId(), sender: 'player', text }]);
      }
      
      if (eventType === EventType.INIT) {
          // init 事件：建立连接，重建会话
          const request: StreamInitRequest = {
              event: { type: EventType.INIT, ...eventData },
              session_id: sessionId,
              game_state: gameState || null,
          };
          
          streamRequestSSE(request, undefined, () => {
              setMessages(prev => [...prev, { id: generateMsgId(), sender: 'system', text: "错误：初始化连接失败。" }]);
          });
      } else {
          // message 事件：只发送增量
          if (!gameState) return;
          
          const request: StreamMessageRequest = {
              event: { type: eventType, ...eventData },
              player_input: text,
              session_id: sessionId,
              game_state: gameState, // 只发送当前游戏状态（增量）
          };
          
          streamRequestSSE(request, undefined, () => {
              setMessages(prev => [...prev, { id: generateMsgId(), sender: 'system', text: "错误：与后端的连接已丢失。" }]);
          });
      }
  };

  // Fetch initial state on mount
  useEffect(() => {
    if (isInitialized.current) return;
    isInitialized.current = true;

    // 使用新的 SSE 协议发送 init 事件
    const request: StreamInitRequest = {
        event: { type: EventType.INIT },
        session_id: sessionId,
        game_state: null, // init 时可以不提供 game_state，使用默认值
    };
    
    streamRequestSSE(request);
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
