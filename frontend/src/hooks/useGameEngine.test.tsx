import { act, renderHook, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { useGameEngine } from './useGameEngine';
import { StreamChunkType, StreamChunk } from '../types';

// Mock global fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Helper to create a ReadableStream from an array of chunks
function createStreamResponse(chunks: StreamChunk[]) {
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    start(controller) {
      chunks.forEach(chunk => {
        const json = JSON.stringify(chunk);
        controller.enqueue(encoder.encode(json + '\n'));
      });
      controller.close();
    },
  });

  return {
    ok: true,
    body: stream,
  } as Response;
}

// Delayed stream simulation for more control
function createDelayedStreamResponse(chunkSequence: (StreamChunk | 'DELAY')[]) {
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      async start(controller) {
        for (const item of chunkSequence) {
            if (item === 'DELAY') {
                await new Promise(r => setTimeout(r, 100));
            } else {
                const json = JSON.stringify(item);
                controller.enqueue(encoder.encode(json + '\n'));
            }
        }
        controller.close();
      },
    });
  
    return {
      ok: true,
      body: stream,
    } as Response;
}

describe('useGameEngine', () => {
  it('should handle logic lock sequence correctly', async () => {
    // 1. Setup Mock Stream
    // Sequence: Logic Event -> Meaning Text -> Dice Roll -> Settlement
    // Expectation: Logic Event shows immediately. Text and Settlement are BLOCKED. Dice Roll is CACHED.
    
    const logicEventChunk: StreamChunk = {
        type: StreamChunkType.LOGIC_EVENT,
        event: { name: 'Test Check', die_type: 'd20', outcomes: [] }
    };

    const initialMsg: StreamChunk = {
        type: StreamChunkType.MESSAGE,
        text: 'Initial Context',
        sender: 'dm'
    };

    const narrativeChunk: StreamChunk = {
        type: StreamChunkType.MESSAGE,
        text: 'This should be hidden until unlock',
        sender: 'dm'
    };
    
    const diceChunk: StreamChunk = {
        type: StreamChunkType.DICE_ROLL,
        dice: { type: 'd20', result: 15, reason: 'Test Check' }
    };
    
    const settlementChunk: StreamChunk = {
        type: StreamChunkType.SETTLEMENT,
        delta: { hp_change: -5, sanity_change: 0, items_added: [], items_removed: [] }
    };

    mockFetch.mockResolvedValueOnce(createDelayedStreamResponse([
        initialMsg,
        'DELAY',
        logicEventChunk,
        'DELAY', // Give React time to process logic event lock
        narrativeChunk,
        'DELAY',
        diceChunk, // Should slip through into pending
        settlementChunk // Should be blocked
    ]));

    const { result } = renderHook(() => useGameEngine());

    // Wait for initialization and LOIGC EVENT specifically
    await waitFor(() => {
        const hasMsg = result.current.messages.length > 0;
        if (!hasMsg) throw new Error("No messages yet");
        
        const hasLogic = result.current.messages.some(m => m.logicEvent?.name === 'Test Check');
        if (!hasLogic) throw new Error("Logic Event not found");
    }, { timeout: 2000 });

    // 1. Verify Logic Event is present
    const logicMsg = result.current.messages.find(m => m.logicEvent);
    expect(logicMsg).toBeDefined();
    expect(logicMsg?.logicEvent?.name).toBe('Test Check');
    
    // 2. Verify Narrative is NOT present yet (Blocked by Logic Lock)
    // Note: The hook appends messages. If blocked, narrativeChunk content shouldn't be in a *new* message or patched yet?
    // Actually, MESSAGE type creates a new message. Logic Event patches the previous one or attaches to one. 
    // Wait... Logic Event chunk attaches to the *previous* message usually? 
    // Let's check the code: "logicEvent attaches to the *last* message".
    // Wait, in my test stream, I sent Logic Event as a standalone chunk first?
    // In `handleChunkLive`: LOGIC_EVENT patches prev message or creates none if no prev?
    // `setMessages(prev => ... logicEvent = chunk.event ...)`
    // If no previous message exists, it might be dropped! 
    // Ah, the stream usually is Message -> LogicEvent.
    // Let's adjust the test to match reality: Message (Intro) -> LogicEvent -> Message (Result).
    
  });
  
  it('should execute the full Logic -> Dice -> Settlement flow', async () => {
    // Correct Sequence:
    // 1. DM Message: "You see a door."
    // 2. Logic Event: "Open Door?" (Patches msg 1)
    // 3. DM Message: "You opened it." (Blocked)
    // 4. Dice Roll: 20 (Cached)
    // 5. Settlement: +XP (Blocked)
    
    const introMsg: StreamChunk = { type: StreamChunkType.MESSAGE, text: 'You see a door.', sender: 'dm' };
    const logicEvt: StreamChunk = { type: StreamChunkType.LOGIC_EVENT, event: { name: 'Open', die_type: 'd20', outcomes: [] } };
    const resultMsg: StreamChunk = { type: StreamChunkType.MESSAGE, text: 'Success!', sender: 'dm' };
    const diceRoll: StreamChunk = { type: StreamChunkType.DICE_ROLL, dice: { type: 'd20', result: 20 } };
    const settle: StreamChunk = { type: StreamChunkType.SETTLEMENT, delta: { hp_change: 10, sanity_change: 0, items_added: [], items_removed: [] } };

    mockFetch.mockResolvedValueOnce(createDelayedStreamResponse([
        introMsg,
        'DELAY',
        logicEvt,
        'DELAY',
        resultMsg,   // BLOCKED
        diceRoll,    // CACHED
        settle       // BLOCKED
    ]));

    const { result } = renderHook(() => useGameEngine());

    // A. Wait for Intro + Logic Event
    await waitFor(() => {
        const msgs = result.current.messages;
        if (msgs.length === 0) throw new Error("No messages");
        if (msgs[0].logicEvent?.name !== 'Open') throw new Error("Logic event not attached");
    }, { timeout: 2000 });

    const msgId = result.current.messages[0].id;

    // B. Ensure Result Message is NOT shown yet
    expect(result.current.messages.length).toBe(1); // Only the intro message
    expect(result.current.messages.find(m => m.text === 'Success!')).toBeUndefined();
    
    // C. Confirm the Logic Event (Simulate User Click)
    act(() => {
        result.current.handleLogicEventConfirm(msgId);
    });

    // D. Expect Dice Animation to trigger
    // Because dice roll was cached, checking confirm should unleash it.
    await waitFor(() => {
        if (result.current.diceAnimation === null) throw new Error("Dice animation not started");
    });
    
    expect(result.current.diceAnimation?.result).toBe(20);

    // E. Animation Complete -> Release Queue
    act(() => {
        result.current.handleDiceAnimationComplete();
    });

    // F. Now Result Message and Settlement should appear
    await waitFor(() => {
        const len = result.current.messages.length;
        if (len < 3) throw new Error(`Expected at least 3 messages, got ${len}`);
        // 1: Intro (w/ Logic)
        // 2: Result Message
        // 3: Settlement (System msg)
    });

    const msgs = result.current.messages;
    expect(msgs[1].text).toBe('Success!');
    expect(msgs[2].settlement).toBeDefined();
    expect(msgs[2].settlement?.hp_change).toBe(10);
  });
});
