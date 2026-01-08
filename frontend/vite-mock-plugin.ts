import type { Plugin } from 'vite';

// Define types locally for the build script context to avoid importing from src which might have specialized aliases
interface Attributes {
    STR: number;
    DEX: number;
    CON: number;
    INT: number;
    WIS: number;
    CHA: number;
}

interface Vitals {
    hp: number;
    maxHp: number;
    sanity: number;
    maxSanity: number;
}

interface Item {
    id: string;
    name: string;
    icon?: string;
    quantity: number;
    description?: string;
    category?: string;
}

interface GameState {
    level: string;
    attributes: Attributes;
    vitals: Vitals;
    inventory: (Item | null)[];
}

interface GameEvent {
    type: 'init' | 'action' | 'message' | 'use' | 'drop';
    item_id?: string;
    quantity?: number;
}

interface ChatRequest {
    event: GameEvent;
    player_input: string;
    current_state: GameState | null;
}

interface BackendMessage {
    text: string;
    sender: 'dm' | 'system';
    options?: string[];
  }
  
  interface ChatResponse {
    messages: BackendMessage[];
    new_state: GameState;
  }


const INITIAL_GAME_STATE: GameState = {
  level: "Level 1",
  attributes: {
    STR: 12,
    DEX: 14,
    CON: 13,
    INT: 16,
    WIS: 10,
    CHA: 8
  },
  vitals: {
    hp: 18,
    maxHp: 20,
    sanity: 85,
    maxSanity: 100
  },
  inventory: [
    { id: '1', name: '杏仁水', icon: '💧', quantity: 3, description: '一瓶散发着甜杏仁味的淡黄色液体。在这个地方，它是生命的源泉。', category: 'resource' },
    { id: '2', name: '手电筒', icon: '🔦', quantity: 1, description: '一个结实的手电筒，电池电量似乎还很足。能照亮前方未知的黑暗。', category: 'tool' },
    { id: '3', name: '大砍刀', icon: '🔪', quantity: 1, description: '一把生锈但依然锋利的大砍刀，是对付实体的好帮手。', category: 'weapon' },
    { id: '4', name: '急救包', icon: '❤️', quantity: 2, description: '包含绷带、消毒水和止痛药的标准急救包。', category: 'medical' },
    { id: '5', name: '压缩饼干', icon: '🍪', quantity: 5, description: '虽然口感像木屑，但能提供大量热量。', category: 'resource' },
    { id: '6', name: '撬棍', icon: '🔧', quantity: 1, description: '物理学圣剑，无论是开门还是敲人都在行。', category: 'tool' },
    { id: '7', name: '旧照片', icon: '📷', quantity: 1, description: '一张模糊的照片，依稀能分辨出一个微笑的人影，看着它让你感到莫名的悲伤。', category: 'document' },
    { id: '8', name: '生锈的钥匙', icon: '🗝️', quantity: 1, description: '不知道能打开哪扇门，但在后室里，钥匙总是有用的。', category: 'tool' },
    { id: '9', name: '无线电', icon: '📻', quantity: 1, description: '只能发出沙沙的白噪音，偶尔似乎能听到有人在低语。', category: 'tool' },
    { id: '10', name: '幸运硬币', icon: '🪙', quantity: 1, description: '一枚古老的金币，正面是笑脸，反面是哭脸。', category: 'special' },
    { id: '11', name: '皇家口粮', icon: '🥫', quantity: 1, description: '极其实验性的食物，据说味道好极了，但副作用未知。', category: 'resource' },
    { id: '12', name: '灭火器', icon: '🧯', quantity: 1, description: '沉重但可靠，可以用来扑灭火焰或作为钝器。', category: 'tool' },
    { id: '13', name: '录音带', icon: '📼', quantity: 1, description: '上面写着“不要听”，这让你更想找个播放器来听听。', category: 'document' },
    { id: '14', name: '损坏的指南针', icon: '🧭', quantity: 1, description: '指针疯狂地旋转，在这里方向是没有意义的。', category: 'special' },
    { id: '15', name: '瓶装闪电', icon: '⚡', quantity: 1, description: '玻璃瓶里跳动着蓝色的电弧，投掷出去可能造成巨大伤害。', category: 'weapon' },
    { id: '16', name: '液体痛苦', icon: '☠️', quantity: 1, description: '深红色的粘稠液体，以此物命名是有原因的。千万别喝。', category: 'special' },
    { id: '17', name: '摄像机', icon: '📹', quantity: 1, description: '电池还能撑一会，也许能记录下什么重要的东西。', category: 'tool' },
    { id: '18', name: '圣水', icon: '🏺', quantity: 1, description: '也许对某些邪恶实体有效？或者只是一瓶普通的自来水。', category: 'special' },
    { id: '19', name: '神秘纸条', icon: '📄', quantity: 1, description: '上面潦草地写着：“它就在你后面。”', category: 'document' },
    { id: '20', name: '瑞士军刀', icon: '⚔️', quantity: 1, description: '多功能工具，虽然每一项功能都不算顶尖，但胜在全面。', category: 'tool' },
    { id: '21', name: '电池', icon: '🔋', quantity: 4, description: '通用的AA电池，在这个没有充电插座的地方是硬通货。', category: 'resource' },
    null, null, null, null, null, null, null, null, null, null, null, null, null, null, null
  ]
};

export const mockServerPlugin = (): Plugin => {
    return {
        name: 'vite-mock-server',
        configureServer(server) {
            // Middleware for parsing JSON body
            server.middlewares.use((req, _res, next) => {
                if (req.method === 'POST' && req.url === '/api/chat') {
                    let body = '';
                    req.on('data', chunk => {
                        body += chunk.toString();
                    });
                    req.on('end', () => {
                        try {
                            if (body) {
                                (req as any).body = JSON.parse(body);
                            }
                            next();
                        } catch (e) {
                            console.error('JSON Parse Error', e);
                            next();
                        }
                    });
                } else {
                    next();
                }
            });

            // The main route handler
            server.middlewares.use('/api/chat', (req, res) => {
                if (req.method === 'POST') {
                    const body = (req as any).body as ChatRequest;
                    // Provide default empty event if missing (for safety)
                    const { player_input, current_state, event } = body || {};
                    const eventType = event?.type || 'message';

                    let response: ChatResponse;

                    if (eventType === 'init') {
                        response = {
                            messages: [{
                                text: '你在一个潮湿的黄色房间里醒来。荧光灯的嗡嗡声震耳欲聋。你看到北边和东边有出口。',
                                sender: 'dm',
                                options: [
                                    '向北走深入这无尽的黄色走廊', 
                                    '向东走寻找那个发出声音的角落', 
                                    '仔细检查背包里的物资状况', 
                                    '用尽全力大喊一声看看有无回应'
                                ]
                            }],
                            new_state: INITIAL_GAME_STATE
                        };
                    } else if (eventType === 'use' || eventType === 'drop') {
                        // Handle Item events
                        console.log(`[Mock] Item Event: ${eventType} id=${event?.item_id} qty=${event?.quantity}`);
                        
                        let newState = current_state ? { ...current_state } : { ...INITIAL_GAME_STATE };
                        let responseMessage = "";
                        
                        const itemIndex = newState.inventory.findIndex(i => i?.id === event?.item_id);
                        if (itemIndex > -1) {
                            const item = newState.inventory[itemIndex];
                            if (!item) {
                                responseMessage = "Error: Item somehow null despite index check.";
                            } else {
                                if (eventType === 'use') {
                                    responseMessage = `(ViteMock) Used ${item.name}. Effects applied.`;
                                    // Logic to consume item...
                                    if (item.quantity > 1) {
                                        item.quantity -= 1;
                                    } else {
                                        newState.inventory[itemIndex] = null;
                                    }

                                    // --- Chaos Mode: Randomly Remove & Add Items ---
                                    
                                    // 1. Randomly remove 0-2 OTHER items
                                    const itemsToRemoveCount = Math.floor(Math.random() * 3); // 0, 1, or 2
                                    let removedCount = 0;
                                    // Find occupied slots that are NOT the current item (to avoid double remove logic issues)
                                    const otherIndices = newState.inventory
                                        .map((it, idx) => (it && idx !== itemIndex) ? idx : -1)
                                        .filter(idx => idx !== -1);
                                    
                                    // Shuffle and pick indices
                                    for (let i = otherIndices.length - 1; i > 0; i--) {
                                        const j = Math.floor(Math.random() * (i + 1));
                                        [otherIndices[i], otherIndices[j]] = [otherIndices[j], otherIndices[i]];
                                    }
                                    
                                    for (let i = 0; i < Math.min(itemsToRemoveCount, otherIndices.length); i++) {
                                        const idxToRemove = otherIndices[i];
                                        const itemToRemove = newState.inventory[idxToRemove];
                                        if (itemToRemove) {
                                            // Simply nulling it out or decreasing qty?
                                            // Let's decrease random amount or kill it
                                            const qtyToRemove = Math.floor(Math.random() * itemToRemove.quantity) + 1;
                                            console.log(`[Mock] Chaos Remove: ${itemToRemove.name} -${qtyToRemove}`);
                                            
                                            // Append to response message
                                            responseMessage += ` [Lost: ${itemToRemove.name} x${qtyToRemove}]`;

                                            if (itemToRemove.quantity > qtyToRemove) {
                                                itemToRemove.quantity -= qtyToRemove;
                                            } else {
                                                newState.inventory[idxToRemove] = null;
                                            }
                                        }
                                    }

                                    // 2. Randomly ADD 1-2 NEW items
                                    const itemsToAddCount = Math.floor(Math.random() * 2) + 1; // 1 or 2
                                    const potentialLoot = [
                                        { id: `chaos_1_${Date.now()}`, name: 'Chaos Orb', icon: '🔮', quantity: 1, category: 'special', description: 'Appeared from nowhere.' },
                                        { id: `chaos_2_${Date.now()}`, name: 'Void Dust', icon: '✨', quantity: 5, category: 'resource', description: 'Glittering dust.' },
                                        { id: `chaos_3_${Date.now()}`, name: 'Glitch Frag', icon: '🧩', quantity: 1, category: 'tool', description: 'A piece of reality.' },
                                        { id: `chaos_4_${Date.now()}`, name: 'Lost Sock', icon: '🧦', quantity: 1, description: 'Where did this come from?' }
                                    ];

                                    for (let k = 0; k < itemsToAddCount; k++) {
                                        const randomLoot = { 
                                            ...potentialLoot[Math.floor(Math.random() * potentialLoot.length)],
                                            id: `new_${Date.now()}_${k}` // Unique ID
                                        };
                                        
                                        // Try to find empty slot
                                        const emptyIndex = newState.inventory.findIndex(it => it === null);
                                        if (emptyIndex > -1) {
                                            newState.inventory[emptyIndex] = randomLoot;
                                            responseMessage += ` [Gained: ${randomLoot.name}]`;
                                            console.log(`[Mock] Chaos Add: ${randomLoot.name} at slot ${emptyIndex}`);
                                        }
                                    }

                                } else {
                                    const dropQty = event?.quantity || 1;
                                    responseMessage = `(ViteMock) Dropped ${dropQty}x ${item.name}.`;
                                    if (item.quantity > dropQty) {
                                        item.quantity -= dropQty;
                                    } else {
                                        newState.inventory[itemIndex] = null;
                                    }
                                }
                            }
                        } else {
                            responseMessage = "(ViteMock) Item not found in inventory.";
                        }

                         response = {
                            messages: [{
                                text: responseMessage,
                                sender: 'dm'
                            }],
                            new_state: newState
                        };

                    } else {
                        // Action / Message handling
                        console.log(`[Mock] User says: ${player_input}`);

                        let responseMessage = `(ViteMock) You said: "${player_input}". The void listens carefully.`;
                        let newState = current_state ? { ...current_state } : { ...INITIAL_GAME_STATE };

                        if (newState) {
                            if (player_input && player_input.toLowerCase().includes('hit')) {
                                responseMessage = "(ViteMock) Ouch! You took some damage from imaginary spikes.";
                                newState.vitals.hp = Math.max(0, newState.vitals.hp - 5);
                            } else if (player_input && player_input.toLowerCase().includes('heal')) {
                                responseMessage = "(ViteMock) You feel refreshed.";
                                newState.vitals.hp = Math.min(newState.vitals.maxHp, newState.vitals.hp + 10);
                            }
                        }

                        response = {
                            messages: [{
                                text: responseMessage,
                                sender: 'dm'
                            }],
                            new_state: newState
                        };
                    }

                    res.setHeader('Content-Type', 'application/json');
                    
                    // Simulate random latency between 1000ms and 3000ms
                    setTimeout(() => {
                        res.end(JSON.stringify(response));
                    }, Math.random() * 2000 + 1000);
                } else {
                    // Not a POST request
                    res.statusCode = 405;
                    res.end();
                }
            });
        },
    };
};
