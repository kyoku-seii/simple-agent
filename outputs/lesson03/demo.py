"""第 3 课第一步：工具 B 的参数来自工具 A 的结果。

运行：python3 outputs/lesson03/demo.py
依赖：python3 -m pip install -r outputs/lesson03/requirements.txt
mock_model() 从查询结果中选择舒缓模式，构造下一次工具调用。
模型、车辆接口和模式 ID 均为教学模拟；消息格式为自定义格式。
复用第一课的非流式 Agent 循环，不连接真实车辆或模型 API。
"""
from typing import Literal

from pydantic import BaseModel


class MassageMode(BaseModel):
    mode_id: str
    name: str


class ModeCatalog(BaseModel):
    seat: str
    modes: list[MassageMode]


class ToolCall(BaseModel):
    type: Literal["tool_call"] = "tool_call"
    name: Literal["get_massage_modes", "start_massage"]
    arguments: dict[str, str]


class FinalResponse(BaseModel):
    type: Literal["final"] = "final"
    text: str


class Message(BaseModel):
    role: Literal["user", "assistant", "tool"]
    content: str
    name: str | None = None


Response = ToolCall | FinalResponse

# 模拟车辆提供的数据。mock_model 只能从工具返回消息读取，不能直接查此常量。
DRIVER_MODES = [
    MassageMode(mode_id="m_12", name="活力"),
    MassageMode(mode_id="m_37", name="舒缓"),
]


def get_massage_modes(seat: str) -> str:
    if seat != "driver":
        raise ValueError("本课 mock 只支持主驾")
    return ModeCatalog(seat=seat, modes=DRIVER_MODES).model_dump_json()


def start_massage(seat: str, mode_id: str) -> str:
    if seat != "driver":
        raise ValueError("本课 mock 只支持主驾")
    for mode in DRIVER_MODES:
        if mode.mode_id == mode_id:
            return f"[mock] 已启动主驾{mode.name}按摩，mode_id={mode_id}"
    raise ValueError(f"车辆不支持该模式 ID：{mode_id}")


TOOLS = {
    "get_massage_modes": get_massage_modes,
    "start_massage": start_massage,
}


def mock_model(messages: list[Message]) -> Response:
    """只模拟固定请求：查询主驾模式，再启动其中的舒缓模式。"""
    last_message = messages[-1]

    if last_message.role == "user":
        return ToolCall(name="get_massage_modes", arguments={"seat": "driver"})

    if last_message.role == "tool" and last_message.name == "get_massage_modes":
        catalog = ModeCatalog.model_validate_json(last_message.content)
        for mode in catalog.modes:
            if mode.name == "舒缓":
                return ToolCall(
                    name="start_massage",
                    arguments={"seat": catalog.seat, "mode_id": mode.mode_id},
                )
        return FinalResponse(text="查询结果中没有舒缓模式，未启动按摩。")

    if last_message.role == "tool" and last_message.name == "start_massage":
        return FinalResponse(text=last_message.content)

    raise ValueError("mock_model 收到了本课未覆盖的上下文")


def run_agent(max_rounds: int = 3) -> list[Message]:
    messages = [Message(role="user", content="查询主驾支持的按摩模式，再启动其中的舒缓模式")]

    for round_index in range(max_rounds):
        print(f"\n[模型请求 {round_index + 1}]")
        response = mock_model(messages)
        messages.append(Message(role="assistant", content=response.model_dump_json()))

        if response.type == "final":
            print(response.text)
            break

        print("工具调用：", response.model_dump_json())
        result = TOOLS[response.name](**response.arguments)
        messages.append(Message(role="tool", name=response.name, content=result))
        print("工具结果：", result)
    else:
        print("达到模型请求轮数上限，停止")

    return messages


if __name__ == "__main__":
    run_agent()
