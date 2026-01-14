import asyncio
import json
from typing import AsyncGenerator, Dict

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backroom_agent.agent.graph import graph
from backroom_agent.protocol import (Attributes, EventType, GameState,
                                     StreamChunkInitContext, StreamChunkType,
                                     StreamInitRequest, StreamMessageRequest,
                                     Vitals)
from backroom_agent.utils.common import truncate_text
from backroom_agent.utils.logger import logger
from backroom_agent.utils.session_manager import get_session_manager

app = FastAPI(title="Backroom Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Helper Methods ---


def get_initial_state() -> GameState:
    """Returns the default initial game state."""
    return GameState(
        level="Level 0",
        attributes=Attributes(STR=10, DEX=10, CON=10, INT=10, WIS=10, CHA=10),
        vitals=Vitals(hp=10, maxHp=10, sanity=100),
        inventory=[],
    )


async def sse_stream_generator(
    request: StreamInitRequest | StreamMessageRequest,
) -> AsyncGenerator[str, None]:
    """
    SSE 流式响应生成器
    根据事件类型处理 init 或 message 事件
    """
    from langchain_core.messages import HumanMessage

    from backroom_agent.agent.state import State

    session_manager = get_session_manager()
    session_id = request.session_id or "NO_SESSION"

    if isinstance(request, StreamInitRequest):
        # init 事件：重建会话
        current_state = request.game_state or get_initial_state()
        session = session_manager.create_or_reset_session(session_id, current_state)

        # 发送完整上下文（此时消息历史为空）
        messages_dict = []
        for msg in session.messages:
            if hasattr(msg, "content") and hasattr(msg, "type"):
                messages_dict.append({"type": msg.type, "content": msg.content})

        init_context = StreamChunkInitContext(
            type=StreamChunkType.INIT_CONTEXT,
            messages=messages_dict,
            game_state=current_state,
        )
        yield f"data: {init_context.model_dump_json()}\n\n"

        # 构建输入状态
        input_state: State = {
            "event": request.event,
            "user_input": "",
            "session_id": session_id,
            "current_game_state": current_state,
            "messages": [],
            "logic_event": None,
            "logic_outcome": None,
            "dice_roll": None,
            "raw_llm_output": None,
            "level_context": None,
            "valid_actions": None,
            "suggestions": None,
            "settlement_delta": None,
            "turn_loop_count": 0,
        }

        # 收集所有消息和状态
        all_messages = []
        final_state = current_state

        # 处理流式更新
        async for chunk in graph.astream(input_state, stream_mode="updates"):
            for node_name, updates in chunk.items():
                if not updates:
                    continue

                logger.info(f"Graph Update from {node_name}: {list(updates.keys())}")

                # 收集消息和状态
                if "messages" in updates:
                    msgs = updates["messages"]
                    if not isinstance(msgs, list):
                        msgs = [msgs]
                    all_messages.extend(msgs)

                if "current_game_state" in updates:
                    final_state = updates["current_game_state"]

                # 生成流式响应
                async for sse_chunk in _format_stream_chunks(updates, is_init=True):
                    yield sse_chunk

        # 更新会话
        if all_messages or final_state != current_state:
            session_manager.update_session(session_id, all_messages, final_state)

    elif isinstance(request, StreamMessageRequest):
        # message 事件：复用会话
        current_state = request.game_state or get_initial_state()
        session = session_manager.get_or_create_session(session_id, current_state)

        # 从会话获取消息历史
        history_messages = session.messages

        # 构建输入状态（使用历史消息 + 新消息）
        input_state: State = {
            "event": request.event,
            "user_input": request.player_input,
            "session_id": session_id,
            "current_game_state": current_state,
            "messages": history_messages + [HumanMessage(content=request.player_input)],
            "logic_event": None,
            "logic_outcome": None,
            "dice_roll": None,
            "raw_llm_output": None,
            "level_context": None,
            "valid_actions": None,
            "suggestions": None,
            "settlement_delta": None,
            "turn_loop_count": 0,
        }

        # 收集所有消息和状态
        all_messages = history_messages + [HumanMessage(content=request.player_input)]
        final_state = current_state

        # 处理流式更新
        async for chunk in graph.astream(input_state, stream_mode="updates"):
            for node_name, updates in chunk.items():
                if not updates:
                    continue

                logger.info(f"Graph Update from {node_name}: {list(updates.keys())}")

                # 收集消息和状态
                if "messages" in updates:
                    msgs = updates["messages"]
                    if not isinstance(msgs, list):
                        msgs = [msgs]
                    all_messages.extend(msgs)

                if "current_game_state" in updates:
                    final_state = updates["current_game_state"]

                # 生成流式响应
                async for sse_chunk in _format_stream_chunks(updates, is_init=False):
                    yield sse_chunk

        # 更新会话
        if (
            all_messages
            != (history_messages + [HumanMessage(content=request.player_input)])
            or final_state != current_state
        ):
            session_manager.update_session(session_id, all_messages, final_state)


async def _format_stream_chunks(
    updates: Dict, is_init: bool = False
) -> AsyncGenerator[str, None]:
    """格式化流式响应块"""
    from langchain_core.messages import AIMessage, SystemMessage

    from backroom_agent.protocol import (DiceRoll, GameState, LogicEvent,
                                         SettlementDelta, StreamChunkDice,
                                         StreamChunkInit,
                                         StreamChunkLogicEvent,
                                         StreamChunkMessage,
                                         StreamChunkSettlement,
                                         StreamChunkState,
                                         StreamChunkSuggestions,
                                         StreamChunkType)

    # Dice Roll
    if "dice_roll" in updates:
        dice = updates["dice_roll"]
        if dice:
            try:
                if isinstance(dice, dict):
                    dice = DiceRoll(**dice)
                if isinstance(dice, DiceRoll):
                    yield f"data: {StreamChunkDice(type=StreamChunkType.DICE_ROLL, dice=dice).model_dump_json()}\n\n"
                    await asyncio.sleep(2.0)
            except Exception as e:
                logger.error(f"Error yielding DiceRoll: {e}")

    # Settlement Delta
    if "settlement_delta" in updates:
        delta_data = updates["settlement_delta"]
        if delta_data:
            try:
                if isinstance(delta_data, dict):
                    delta_obj = SettlementDelta(**delta_data)
                elif isinstance(delta_data, SettlementDelta):
                    delta_obj = delta_data
                else:
                    delta_obj = None

                if delta_obj:
                    yield f"data: {StreamChunkSettlement(type=StreamChunkType.SETTLEMENT, delta=delta_obj).model_dump_json()}\n\n"
            except Exception as e:
                logger.error(f"Error yielding SettlementDelta: {e}")

    # Messages
    if "messages" in updates:
        msgs = updates["messages"]
        if not isinstance(msgs, list):
            msgs = [msgs]

        for msg in msgs:
            if isinstance(msg, AIMessage) and msg.content:
                if is_init:
                    # init 事件使用 StreamChunkInit
                    yield f"data: {StreamChunkInit(type=StreamChunkType.INIT, text=str(msg.content)).model_dump_json()}\n\n"
                else:
                    # message 事件使用 StreamChunkMessage
                    yield f"data: {StreamChunkMessage(type=StreamChunkType.MESSAGE, text=str(msg.content), sender='dm').model_dump_json()}\n\n"
            elif isinstance(msg, SystemMessage) and msg.content:
                yield f"data: {StreamChunkMessage(type=StreamChunkType.MESSAGE, text=str(msg.content), sender='system').model_dump_json()}\n\n"

    # Game State
    if "current_game_state" in updates:
        new_state = updates["current_game_state"]
        if isinstance(new_state, GameState):
            yield f"data: {StreamChunkState(type=StreamChunkType.STATE, state=new_state).model_dump_json()}\n\n"

    # Logic Event
    if "logic_event" in updates:
        evt = updates["logic_event"]
        if isinstance(evt, LogicEvent):
            yield f"data: {StreamChunkLogicEvent(type=StreamChunkType.LOGIC_EVENT, event=evt).model_dump_json()}\n\n"
            await asyncio.sleep(5.0)

    # Suggestions
    if "suggestions" in updates:
        suggs = updates["suggestions"]
        if isinstance(suggs, list):
            yield f"data: {StreamChunkSuggestions(type=StreamChunkType.SUGGESTIONS, options=suggs).model_dump_json()}\n\n"


# --- Routes ---


@app.post("/api/chat/stream")
async def chat_stream_endpoint(
    request: StreamInitRequest | StreamMessageRequest,
) -> StreamingResponse:
    """
    SSE streaming endpoint for chat interactions.
    Supports init and message events with session management.
    """
    session_id = request.session_id or "NO_SESSION"
    event_type = request.event.type

    if isinstance(request, StreamInitRequest):
        logger.info(f"[{session_id}] Init event: Establishing SSE connection")
    elif isinstance(request, StreamMessageRequest):
        logger.info(
            f"[{session_id}] Message event: {event_type} | Input: {request.player_input}"
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid request type")

    return StreamingResponse(
        sse_stream_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


def start() -> None:
    """Launched with `python -m backroom_agent.server`"""
    # Assuming running from the project root
    uvicorn.run("backroom_agent.server:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    start()
