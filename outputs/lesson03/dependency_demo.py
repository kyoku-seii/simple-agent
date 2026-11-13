"""第 3 课：由程序检查任务依赖，并通过 run_task() 执行。

运行：python3 outputs/lesson03/dependency_demo.py
依赖：outputs/lesson03/requirements.txt
本例的 A→B 依赖由业务代码固定，模型不能修改计划或任务状态。
can_run() 检查就绪，run_task() 管理执行状态，dispatch_task() 分派工具。
本步同步执行，无并发、自动调度或重试。
数据结构为自定义教学格式，不连接真实车辆。
"""
from typing import Literal

from pydantic import BaseModel, Field

from demo import ModeCatalog, get_massage_modes, start_massage


class Task(BaseModel):
    id: str
    tool_name: str
    depends_on: list[str] = Field(default_factory=list)


class TaskState(BaseModel):
    status: Literal["pending", "running", "succeeded", "failed"] = "pending"
    result: str | None = None


# 本例只有这一份可信业务计划，不接收模型生成的 depends_on。
PLAN = [
    Task(id="A", tool_name="get_massage_modes"),
    Task(id="B", tool_name="start_massage", depends_on=["A"]),
]


def can_run(task: Task, states: dict[str, TaskState]) -> bool:
    """判断任务是否满足本例的数据依赖条件，不执行任务、不修改状态。

    1. 当前任务必须有状态记录，且 status 为 pending。
    2. 每个依赖必须有状态记录、status 为 succeeded、result 不为 None。
    3. 上述条件全部满足才返回 True；没有依赖时第 2 条自然满足。

    这里只检查结果是否已保存；结果格式与具体工具参数由 dispatch_task 检查。
    """
    # 使用 states.get(task.id) 检查当前任务。
    task_state = states.get(task.id)
    if task_state is None:
        return False

    if task_state.status != "pending":
        return False

    # 遍历 task.depends_on，检查每个前置任务的状态和结果。
    for dep in task.depends_on:
        dep_state = states.get(dep)
        if dep_state is None or dep_state.status != "succeeded" or dep_state.result is None:
            return False

    # 返回判断结果。
    return True


def dispatch_task(task: Task, states: dict[str, TaskState]) -> str:
    """已准备的分派函数：调用 mock 工具，B 的参数从 A 的结果中取得。

    教学执行入口统一使用 run_task()；本函数不负责依赖检查和状态管理。
    """
    if task.tool_name == "get_massage_modes":
        print("[调用工具] get_massage_modes")
        return get_massage_modes(seat="driver")

    if task.tool_name == "start_massage":
        query_result = states["A"].result
        if query_result is None:
            raise ValueError("缺少 A 的查询结果")
        catalog = ModeCatalog.model_validate_json(query_result)
        for mode in catalog.modes:
            if mode.name == "舒缓":
                print(f"[调用工具] start_massage，mode_id={mode.mode_id}")
                return start_massage(seat=catalog.seat, mode_id=mode.mode_id)
        raise ValueError("查询结果中没有舒缓模式，未启动按摩")

    raise ValueError(f"未知工具：{task.tool_name}")


def run_task(task_id: str, states: dict[str, TaskState]) -> bool:
    """尝试执行一次指定任务：完成返回 True，未就绪返回 False。

    只接收任务 ID，从可信 PLAN 中查找定义，不接收调用方改写的依赖。
    未就绪时不调用工具，也不修改状态；就绪后标为 running，执行分派，
    保存结果，最后标为 succeeded。本例的 ValueError 会标为 failed 并向外抛出。
    """
    task = next((item for item in PLAN if item.id == task_id), None)
    if task is None:
        raise ValueError(f"未知任务：{task_id}")

    # 用 can_run(task, states) 检查；未就绪直接返回 False。
    if not can_run(task, states):
        return False

    state: TaskState = states[task.id]
    # 把 state.status 改为 running。
    state.status = "running"

    try:
        # 调用 dispatch_task(task, states)，将返回值保存到 state.result。
        state.result = dispatch_task(task, states)
        # 保存结果后，把 state.status 改为 succeeded。
        state.status = "succeeded"
    except ValueError:
        # 本例已知的参数/工具错误：记录失败并交给调用方处理，不自动重试。
        state.status = "failed"
        raise

    return True


def run_execution_demo():
    """故意先尝试 B，观察入口是否阻止提前启动和重复执行。"""
    states = {task.id: TaskState() for task in PLAN}
    attempts = [("B", False), ("A", True), ("B", True), ("B", False)]
    for task_id, expected in attempts:
        print(f"\n尝试执行 {task_id}")
        executed = run_task(task_id, states)
        print("执行完成" if executed else "未就绪或已执行，跳过")
        print(f"状态：A={states['A'].status}，B={states['B'].status}")
        assert executed is expected, f"任务 {task_id} 的执行结果不符合预期"

    print(f"\nB 的结果：{states['B'].result}")


def main():
    query, start = PLAN
    query_result = (
        '{"seat":"driver","modes":[{"mode_id":"m_37","name":"舒缓"}]}'
    )
    cases: list[tuple[str, Task, dict[str, TaskState], bool]] = [
        (
            "A 尚未执行且没有依赖，可以开始",
            query,
            {"A": TaskState(), "B": TaskState()},
            True,
        ),
        (
            "A 尚未开始，B 不能执行",
            start,
            {"A": TaskState(), "B": TaskState()},
            False,
        ),
        (
            "A 仍在运行，B 不能执行",
            start,
            {"A": TaskState(status="running"), "B": TaskState()},
            False,
        ),
        (
            "A 失败，即使留有结果文本，B 也不能执行",
            start,
            {"A": TaskState(status="failed", result="查询失败"), "B": TaskState()},
            False,
        ),
        (
            "A 标为成功但没有保存结果，B 不能执行",
            start,
            {"A": TaskState(status="succeeded"), "B": TaskState()},
            False,
        ),
        (
            "A 成功且结果已保存，B 可以开始",
            start,
            {"A": TaskState(status="succeeded", result=query_result), "B": TaskState()},
            True,
        ),
        (
            "B 已经执行成功，不能重复启动",
            start,
            {
                "A": TaskState(status="succeeded", result=query_result),
                "B": TaskState(status="succeeded", result="已启动"),
            },
            False,
        ),
        (
            "缺少 A 的状态记录，B 不能执行",
            start,
            {"B": TaskState()},
            False,
        ),
    ]

    passed = 0
    for label, task, states, expected in cases:
        actual = can_run(task, states)
        matched = actual is expected
        passed += matched
        print(f"{'通过' if matched else '未通过'}：{label}；实际={actual}，期望={expected}")

    print(f"\n检查结果：{passed}/{len(cases)} 通过")
    assert passed == len(cases), "就绪检查未全部通过"

    print("\n接下来检查工具执行入口：")
    run_execution_demo()


if __name__ == "__main__":
    main()
