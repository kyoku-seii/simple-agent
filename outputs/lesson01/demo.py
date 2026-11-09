"""第 1 课：Agent 循环。当前进度：完成循环并保存完整历史。

运行：python3 outputs/lesson01/demo.py
只模拟“17 + 25”这个任务，不连接真实模型 API。
"""
from typing import TypedDict, Literal, Union


class FinalResponse(TypedDict):
    type: Literal["final"]
    text: str

class ToolCallResponse(TypedDict):
    type: Literal["tool_call"]
    name: str
    arguments: dict

Response = Union[FinalResponse, ToolCallResponse]


def add(a, b):
    return a + b

TOOLS = {
    "add": add
}


def mock_model(messages) -> Response:
    """根据上下文返回工具调用或最终回答；响应格式是教学约定。"""

    last_message = messages[-1]

    if last_message["role"] == "tool":
        return {
            "type": "final",
            "text": f"17 + 25 = {last_message['content']}",
        }

    return {
        "type": "tool_call",
        "name": "add",
        "arguments": {"a": 17, "b": 25},
    }


def run_agent():
    messages = [{"role": "user", "content": "17 + 25 等于多少？"}]

    # 每轮保存模型响应；工具执行后再保存工具结果。
    while True:
        response = mock_model(messages)

        messages.append({
            "role": "assistant",
            "content": response,
        })

        if response["type"] == "final":
            print(response["text"])
            break

        if response["type"] == "tool_call":
            func = TOOLS[response["name"]]
            result = func(**response["arguments"])

            messages.append({
                "role": "tool",
                "name": response["name"],
                "content": str(result),
            })

    print(response)


if __name__ == "__main__":
    run_agent()
