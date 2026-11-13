"""第 1 课：Agent 循环。当前进度：流式接收、工具回传和轮数上限。

运行：python3 outputs/lesson01/demo.py
只模拟“17 + 25”这个任务，不连接真实模型 API。仅使用 Python 标准库。
消息和事件均为自定义教学格式，不是正式 API 格式。
每次请求只生成一个输出项；用同步生成器和短暂停顿模拟流式到达。
"""
import json
import time
from collections.abc import Iterator
from typing import TypedDict, Literal, Union


class FinalResponse(TypedDict):
    type: Literal["final"]
    text: str

class ToolCallResponse(TypedDict):
    type: Literal["tool_call"]
    name: str
    arguments: dict

Response = Union[FinalResponse, ToolCallResponse]


class CreatedEvent(TypedDict):
    type: Literal["created"]


class OutputItemAddedEvent(TypedDict):
    type: Literal["output_item_added"]
    item_type: Literal["tool_call", "final"]


class ToolCallInputDeltaEvent(TypedDict):
    type: Literal["tool_call_input_delta"]
    delta: str


class OutputTextDeltaEvent(TypedDict):
    type: Literal["output_text_delta"]
    delta: str


class OutputItemDoneEvent(TypedDict):
    type: Literal["output_item_done"]
    item: Response


class CompletedEvent(TypedDict):
    type: Literal["completed"]


ResponseEvent = Union[
    CreatedEvent,
    OutputItemAddedEvent,
    ToolCallInputDeltaEvent,
    OutputTextDeltaEvent,
    OutputItemDoneEvent,
    CompletedEvent,
]


def add(a, b):
    return a + b

TOOLS = {
    "add": add
}


def mock_model_stream(
    messages: list[dict[str, str | Response]], delay: float = 0.2
) -> Iterator[ResponseEvent]:
    """一次请求内逐个 yield 事件；done 携带完整项，completed 结束本次响应。"""
    last_message = messages[-1]
    yield {"type": "created"}

    if last_message["role"] == "tool":
        yield {"type": "output_item_added", "item_type": "final"}
        text = ""
        for chunk in ["17", " + ", "25", " = ", str(last_message["content"])]:
            time.sleep(delay)
            text += chunk
            yield {"type": "output_text_delta", "delta": chunk}
        yield {
            "type": "output_item_done",
            "item": {"type": "final", "text": text},
        }
    else:
        yield {"type": "output_item_added", "item_type": "tool_call"}
        arguments_json = ""
        for chunk in ['{"a":', '17, "b":', '25}']:
            time.sleep(delay)
            arguments_json += chunk
            yield {"type": "tool_call_input_delta", "delta": chunk}
        yield {
            "type": "output_item_done",
            "item": {
                "type": "tool_call",
                "name": "add",
                "arguments": json.loads(arguments_json),
            },
        }

    yield {"type": "completed"}


def run_agent(max_rounds: int = 3, delay: float = 0.2) -> list[dict[str, str | Response]]:
    messages: list[dict[str, str | Response]] = [{"role": "user", "content": "17 + 25 等于多少？"}]
    response: Response | None = None
    # 外层：模型请求轮数。内层：同一次请求中的事件数量。
    for current_index in range(max_rounds):
        needs_follow_up = False  # 每次请求都重新累计。
        for event in mock_model_stream(messages, delay=delay):
            if event["type"] == "created":
                print(f"[模型请求 {current_index + 1}]")
            elif event["type"] == "output_item_added":
                if event["item_type"] == "tool_call":
                    print("工具参数片段：", end="", flush=True)
            elif event["type"] == "tool_call_input_delta":
                # 片段可能不是合法 JSON，只展示；尚不执行工具。
                print(event["delta"], end="", flush=True)
            elif event["type"] == "output_text_delta":
                print(event["delta"], end="", flush=True)
            elif event["type"] == "output_item_done":
                print()  # 结束上面的片段输出行。
                response = event["item"]
                # 只保存完整响应，避免把文字片段重复写入历史。
                messages.append({"role": "assistant", "content": response})
                if response["type"] == "tool_call":
                    # done 携带完整名称和参数，此时才执行工具。
                    result = TOOLS[response["name"]](**response["arguments"])
                    messages.append({
                        "role": "tool",
                        "name": response["name"],
                        "content": str(result),
                    })
                    print(f"工具结果：{result}")
                    needs_follow_up = True
            elif event["type"] == "completed":
                break  # 只结束本次响应的事件循环。

        if not needs_follow_up:
            break  # 当前 mock 只会产生工具调用或最终回答。
    else:
        print("达到请求轮数上限，停止")

    print(response)
    return messages


if __name__ == "__main__":
    run_agent()
