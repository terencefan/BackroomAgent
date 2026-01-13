import asyncio
from typing import Any, AsyncGenerator, List, cast

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from backroom_agent.agent.graph import graph
from backroom_agent.agent.state import State
from backroom_agent.constants import GraphKeys
from backroom_agent.protocol import (ChatRequest, DiceRoll, GameState,
                                     LogicEvent, SettlementDelta,
                                     StreamChunkDice, StreamChunkLogicEvent,
                                     StreamChunkMessage, StreamChunkSettlement,
                                     StreamChunkState, StreamChunkSuggestions,
                                     StreamChunkType)
from backroom_agent.utils.logger import logger


async def handle_message(
    request: ChatRequest, current_state: GameState
) -> AsyncGenerator[str, None]:
    # Construct the initial state for the graph execution
    # For a message event, we include the user's input as a HumanMessage
    input_state: State = cast(
        State,
        {
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
            GraphKeys.SETTLEMENT_DELTA: None,
        },
    )

    # Stream updates from the agent graph
    async for chunk in graph.astream(input_state, stream_mode="updates"):
        for node_name, updates in chunk.items():
            if not updates:
                continue

            logger.info(f"Graph Update from {node_name}: {list(updates.keys())}")

            # 1. Dice Roll (Processed first to ensure animation triggers before result text)
            if GraphKeys.DICE_ROLL in updates:
                dice = updates[GraphKeys.DICE_ROLL]
                if dice:
                    try:
                        if isinstance(dice, dict):
                            logger.info(f"Converting DiceRoll from dict: {dice}")
                            dice = DiceRoll(**dice)

                        if isinstance(dice, DiceRoll):
                            logger.info(f"Yielding DiceRoll to frontend: {dice}")
                            # Trigger animation on client
                            yield StreamChunkDice(
                                type=StreamChunkType.DICE_ROLL, dice=dice
                            ).model_dump_json() + "\n"
                            # Wait for animation (client needs time to show it)
                            await asyncio.sleep(2.0)
                    except Exception as e:
                        logger.error(f"Error yielding DiceRoll: {e}")

            # Settlement Delta (Visual Log)
            if GraphKeys.SETTLEMENT_DELTA in updates:
                delta_data = updates[GraphKeys.SETTLEMENT_DELTA]
                if delta_data:
                    try:
                        logger.info(
                            f"Yielding SettlementDelta to frontend: {delta_data}"
                        )
                        # Ensure it is a valid object
                        if isinstance(delta_data, dict):
                            delta_obj = SettlementDelta(**delta_data)
                        elif isinstance(delta_data, SettlementDelta):
                            delta_obj = delta_data
                        else:
                            # Fallback or error
                            logger.warning(
                                f"Unexpected type for SettlementDelta: {type(delta_data)}"
                            )
                            delta_obj = None

                        if delta_obj:
                            yield StreamChunkSettlement(
                                type=StreamChunkType.SETTLEMENT,
                                delta=delta_obj,
                            ).model_dump_json() + "\n"
                    except Exception as e:
                        logger.error(f"Error yielding SettlementDelta: {e}")

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

                    # Also send SystemMessages - though direct HTML settlement logs are deprecated
                    # favor of SETTLEMENT_DELTA, we keep this for other generic system messages
                    if isinstance(msg, SystemMessage) and msg.content:
                        content_str = str(msg.content)
                        yield StreamChunkMessage(
                            type=StreamChunkType.MESSAGE,
                            text=content_str,
                            sender="system",
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
