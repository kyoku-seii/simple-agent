"""第 2 课：把解析结果转换成控制任务与推荐任务。

运行：python3 outputs/lesson02/demo.py
依赖：python3 -m pip install -r outputs/lesson02/requirements.txt
build_tasks() 生成任务；run_tasks() 将任务分派给对应 mock 函数。
数据结构为自定义教学格式，不是正式模型 API 格式。
输入解析与车控服务均为 mock，不连接模型或车辆，不执行真实车控动作。
"""
import json
from typing import Literal

from pydantic import BaseModel


class ParsedRequest(BaseModel):
    user_state: Literal["tired", "unknown"]
    control_actions: list[str]
    recommendation_preference: Literal["requested", "declined", "unspecified"]


class ControlTask(BaseModel):
    kind: Literal["control"] = "control"
    action: str


class RecommendTask(BaseModel):
    kind: Literal["recommend"] = "recommend"
    exclude_actions: list[str]


Task = ControlTask | RecommendTask


def build_tasks(parsed: ParsedRequest) -> list[Task]:
    """根据解析结果生成任务列表，控制任务在前，推荐任务在后。

    规则：
    1. 每个明确控制动作生成一个 control 任务。
    2. 用户没有明确拒绝推荐时，生成一个 recommend 任务。
    3. 推荐排除用户已要求的动作，不等待这些动作的执行结果。
    """
    tasks: list[Task] = []

    for control_item in parsed.control_actions:
        control = ControlTask(kind="control", action=control_item)
        tasks.append(control)

    if parsed.recommendation_preference != "declined":
        tasks.append(RecommendTask(
            kind="recommend",
            exclude_actions=list(parsed.control_actions),
        ))

    return tasks


def execute_control(action: str) -> str:
    """模拟车控服务：只返回说明文字。"""
    return f"[mock 控制] 执行动作：{action}"


def recommend_actions(exclude_actions: list[str]) -> str:
    """从固定候选中排除已请求动作；不读取执行结果，不调用车控服务。"""
    candidates = {
        "seat_massage_on": "座椅按摩",
        "seat_heating_on": "座椅加热",
    }
    suggestions = [
        label for action, label in candidates.items()
        if action not in exclude_actions
    ]
    if not suggestions:
        return "[mock 推荐] 暂无其他推荐"
    return f"[mock 推荐] 可以考虑{'、'.join(suggestions)}（仅建议，未执行）"


def run_tasks(tasks: list[Task]) -> list[str]:
    """逐个分派任务，收集处理结果；此处尚未实现依赖或并发调度。"""
    result: list[str] = []
    for task in tasks:
        if task.kind == "control":
            result.append(execute_control(task.action))
        elif task.kind == "recommend":
            result.append(recommend_actions(task.exclude_actions))
    return result


# 固定解析结果模拟模型输出；expected 用于检查你写的业务逻辑。
# 不需要在这一课实现自然语言识别。
CASES: list[tuple[str, ParsedRequest, list[Task]]] = [
    (
        "我累了，帮我打开座椅按摩",
        ParsedRequest(
            user_state="tired",
            control_actions=["seat_massage_on"],
            recommendation_preference="unspecified",
        ),
        [
            ControlTask(action="seat_massage_on"),
            RecommendTask(exclude_actions=["seat_massage_on"]),
        ],
    ),
    (
        "给我推荐一些车内功能",
        ParsedRequest(
            user_state="unknown",
            control_actions=[],
            recommendation_preference="requested",
        ),
        [RecommendTask(exclude_actions=[])],
    ),
    (
        "我累了，只打开按摩，不用推荐",
        ParsedRequest(
            user_state="tired",
            control_actions=["seat_massage_on"],
            recommendation_preference="declined",
        ),
        [ControlTask(action="seat_massage_on")],
    ),
    (
        "打开座椅按摩",
        ParsedRequest(
            user_state="unknown",
            control_actions=["seat_massage_on"],
            recommendation_preference="unspecified",
        ),
        [
            ControlTask(action="seat_massage_on"),
            RecommendTask(exclude_actions=["seat_massage_on"]),
        ],
    ),
    (
        "我累了，给我推荐一些放松功能",
        ParsedRequest(
            user_state="tired",
            control_actions=[],
            recommendation_preference="requested",
        ),
        [RecommendTask(exclude_actions=[])],
    ),
]


def main():
    passed = 0
    for user_text, parsed, expected in CASES:
        print(f"\n用户：{user_text}")
        print("解析：", parsed.model_dump_json())
        actual = build_tasks(parsed)
        print("任务：", json.dumps([task.model_dump() for task in actual], ensure_ascii=False))
        if actual == expected:
            passed += 1
            print("检查通过")
        else:
            print("检查未通过，期望：", json.dumps(
                [task.model_dump() for task in expected], ensure_ascii=False,
            ))

    print(f"\n检查结果：{passed}/{len(CASES)} 通过")

    print("\n分派示例：", CASES[0][0])
    tasks = build_tasks(CASES[0][1])
    results = run_tasks(tasks)
    for result in results:
        print(result)


if __name__ == "__main__":
    main()
