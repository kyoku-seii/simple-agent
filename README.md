# Agent 与 Codex 源码学习

学习节奏：一个小主题 → Python 小 Demo → 对照 Codex Rust 源码。
所有模型和车控接口均为 mock，不需要 API 密钥，不连接真实车辆。

## 获取代码

```bash
git clone https://github.com/kyoku-seii/simple-agent.git
cd simple-agent
```

已经克隆过时，在仓库目录运行 `git pull --ff-only origin main`。
如果本地有自己的修改，先提交或暂存，再拉取。
也可以在 GitHub 仓库页面选择 **Code → Download ZIP** 下载。

## 安装与运行

使用 Python 3.10 或更新版本。第 1 课只需标准库；第 2、3 课使用 Pydantic 2。
建议在自己创建的 Python 虚拟环境中安装依赖。

```bash
python3 -m pip install -r outputs/lesson03/requirements.txt
python3 outputs/lesson03/dependency_demo.py
```

Windows 上如果没有 `python3` 命令，可以改用 `python` 或 `py`。

| 示例 | 主题 | 运行命令 |
| --- | --- | --- |
| [第 1 课](outputs/lesson01/demo.py) | Agent 循环、流式事件，计算 17 + 25 | `python3 outputs/lesson01/demo.py` |
| [第 2 课](outputs/lesson02/demo.py) | 生成车控与推荐任务，并分派执行 | `python3 outputs/lesson02/demo.py` |
| [第 3 课：线性工具案例](outputs/lesson03/demo.py) | 模型根据查询结果构造下一次工具调用 | `python3 outputs/lesson03/demo.py` |
| [第 3 课：当前示例](outputs/lesson03/dependency_demo.py) | 程序检查 A→B 依赖，维护状态与结果 | `python3 outputs/lesson03/dependency_demo.py` |

当前示例的预期轨迹：先尝试 B 被跳过 → A 查询成功 → B 使用查询结果启动 mock 按摩 → 再次尝试 B 被跳过。
目前为同步单任务执行入口，尚未实现自动调度或并发。

## 接续学习

- [教学约定](AGENTS.md)
- [当前学习进度](LEARNING_PROGRESS.md)
- [后续课程设计](COURSE_PLAN.md)

换电脑或开启新聊天时，提供这个仓库并先阅读教学约定和学习进度，即可从当前步骤继续。
进度文档保存课程摘要，不包含原聊天的逐条历史。

Codex 源码参考仓库为 [openai/codex](https://github.com/openai/codex/tree/e54a5713caf331f42a6eef0166186df5f7563c29)，
固定提交 `e54a5713caf331f42a6eef0166186df5f7563c29`。本仓库不复制该参考仓库；
进度文档中的 `/workspace/codex-reference` 是云端路径，在其他电脑上需自行克隆参考仓库。
