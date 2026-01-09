import asyncio
from typing import AsyncGenerator, List, cast, Any

from langchain_core.messages import AIMessage, HumanMessage

from backroom_agent.constants import GraphKeys
from backroom_agent.graph import graph
from backroom_agent.state import State
from backroom_agent.protocol import (ChatRequest, DiceRoll, GameState,
                                     LogicEvent, StreamChunkDice,
                                     StreamChunkLogicEvent, StreamChunkMessage,
                                     StreamChunkState, StreamChunkSuggestions,
                                     StreamChunkType)


async def handle_message(
    request: ChatRequest, current_state: GameState
) -> AsyncGenerator[str, None]:
    # Construct the initial state for the graph execution
    # For a message event, we include the user's input as a HumanMessage
    input_state: State = {
        GraphKeys.EVENT: request.event,
        GraphKeys.USER_INPUT: request.player_input,
        GraphKeys.SESSION_ID: request.session_id,
        GraphKeys.CURRENT_GAME_STATE: current_state,
        GraphKeys.MESSAGES: [HumanMessage(content=request.player_input)],
        GraphKeys.LOGIC_EVENT: None,
        GraphKeys.DICE_ROLL: None,
        GraphKeys.RAW_LLM_OUTPUT: None,
        GraphKeys.LEVEL_CONTEXT: None,
        GraphKeys.VALID_ACTIONS: None,
        GraphKeys.SUGGESTIONS: None,
    }

    # Stream updates from the agent graph
    async for chunk in graph.astream(input_state, stream_mode="updates"):
        for _, updates in chunk.items():
            if not updates:
                continue

            # 1. Dice Roll (Processed first to ensure animation triggers before result text)
            if GraphKeys.DICE_ROLL in updates:
                dice = updates[GraphKeys.DICE_ROLL]
                if isinstance(dice, DiceRoll):
                    # Trigger animation on client
                    yield StreamChunkDice(
                        type=StreamChunkType.DICE_ROLL, dice=dice
                    ).model_dump_json() + "\n"
                    # Wait for animation (client needs 3s)
                    await asyncio.sleep(3.0)

            # 2. Messages (from LLM or other nodes)
            if GraphKeys.MESSAGES in updates:
                msgs = updates[GraphKeys.MESSAGES]
                if not isinstance(msgs, list):
                    msgs = [msgs]

                for msg in cast(List[Any], msgs):
                    # We typically only send back AIMessages to the frontend
                    if isinstance(msg, AIMessage) and msg.content:
                        content_str = str(msg.content)
                        yield StreamChunkMessage(
                            type=StreamChunkType.MESSAGE,
                            text=content_str,
                            sender="dm",
                        ).model_dump_json() + "\n"

            # 3. Game State
            if GraphKeys.CURRENT_GAME_STATE in updates:
                new_state = updates[GraphKeys.CURRENT_GAME_STATE]
                if isinstance(new_state, GameState):
                    yield StreamChunkState(
                        type=StreamChunkType.STATE, state=new_state
                    ).model_dump_json() + "\n"

            # 4. Logic Event
            if GraphKeys.LOGIC_EVENT in updates:
                evt = updates[GraphKeys.LOGIC_EVENT]
                if isinstance(evt, LogicEvent):
                    yield StreamChunkLogicEvent(
                        type=StreamChunkType.LOGIC_EVENT, event=evt
                    ).model_dump_json() + "\n"
                    await asyncio.sleep(5.0)

            # 5. Suggestions
            if GraphKeys.SUGGESTIONS in updates:
                suggs = updates[GraphKeys.SUGGESTIONS]
                if isinstance(suggs, list):
                    suggs = cast(List[str], suggs)
                    yield StreamChunkSuggestions(
                        type=StreamChunkType.SUGGESTIONS, options=suggs
                    ).model_dump_json() + "\n"
