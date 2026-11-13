# 学习进度

更新日期：2026-11-13

## 当前课程

第 1 课“Agent 请求、工具调用与结束条件的循环机制”已由用户于 2026-11-13 明确确认结束。

当前阶段：车控动作与推荐任务的协同。课程设计见 COURSE_PLAN.md，第 2 课的任务生成、分派 Demo 与源码主线已完成；第 3 课已开始，第 4—6 课尚未实施。

第 3 课当前小步已完成：任务就绪检查已接到工具执行入口。outputs/lesson03/dependency_demo.py 使用 Pydantic Task(id, tool_name, depends_on) 与 TaskState(status, result)，由业务代码固定 A 查询→B 启动的可信依赖计划。模型不能改写计划或状态；若未来接收模型计划，需要额外业务校验。

用户已完成 can_run(task, states)，助手已原样同步实现：当前任务必须有记录且为 pending；遍历全部依赖，每个依赖必须有记录、状态为 succeeded 且 result is not None；全部满足才返回 True。运行 python3 outputs/lesson03/dependency_demo.py，既有八个就绪场景全部通过。can_run 仅判断就绪，不执行工具、不修改状态、不验证结果内容。

dispatch_task 复用同目录 demo.py 的 mock 工具及 ModeCatalog：查询结果保存为 JSON；启动参数从 A 结果中解析并选择舒缓模式，缺少结果或模式时抛出 ValueError。用户已提交 run_task(task_id, states)，执行顺序正确；三处将当前状态对象 state 误写为状态字典 states，助手已修正并保存：未就绪返回 False；执行前标记 running；调用分派并保存结果；最后标记 succeeded。说明 state 与 states[task.id] 引用同一对象，修改属性会保留在字典中。run_task 从可信 PLAN 查定义，本例 ValueError 时标记 failed 并向外抛出，不展开重试或失败分支课程。

已运行 B→A→B→B 的手动尝试序列：首次 B 被挡住，A 成功后 B 才执行，最后不重复执行 B；原八个 can_run 场景全部通过。额外在内存中观察分派/工具调用，验证未就绪及重复请求不执行或改状态、分派时为 running、完成后保存结果且为 succeeded、B 使用查询返回的新模式 ID、A 抛出 ValueError 后标为 failed 且 B 不启动。最小依赖执行入口已完成；本步是同步单任务入口，不含自动调度、并发或真实模型接入。下一步及时收束并对照源码，明确业务 depends_on 是 Demo 增加的约束，不能声称 Codex 有相同的通用依赖图执行器，不再复讲第一课的循环与历史。

下面保留最初的线性工具案例作为对照：教学假设为“查询主驾支持的按摩模式，再启动其中的舒缓模式”；与第 2 课 exclude_actions 来自输入不同，启动所需 mode_id 要等查询工具返回。

已创建 outputs/lesson03/demo.py 和 requirements.txt：沿用 Pydantic，提供两个 mock 工具及第一课已学过的非流式 Agent 循环。用户明确要求助手填写 mock_model，已实现：从工具消息解析 ModeCatalog，遍历模式找到“舒缓”，用 catalog.seat 和 mode.mode_id 生成 start_massage 调用；未找到则返回 FinalResponse 说明未启动。

验证通过：正常流程为三次模型请求、两次工具调用（查询→启动）；更换舒缓模式 ID 和排列顺序仍使用新 ID；缺少舒缓模式时两次模型请求、仅查询工具被调用，没有启动其他模式。模型代码只读取工具消息，不读取 DRIVER_MODES 常量。

用户已正确总结并确认理解：模型决定下一步，再逐步调用工具完成目标。已澄清此处 mock 以固定规则模拟模型决策；运行时工具反馈驱动后续决策，不要求一开始列出全部步骤；当前执行器尚未独立校验先后依赖，不能把模型通常遵守顺序当成程序强制保证。下一步先对照源码中工具结果写回及下一轮读取历史的路径，再引入程序保证依赖的机制。

第 3 课源码阅读当前小步：固定提交下，从外层 run_turn 的 turn.rs:642 clone_history / 647 run_sampling_request 看每轮输入，再回看 try_run_sampling_request:3799 调用 drain_in_flight，以及2856—2870等待工具结果并调用 record_annotated_conversation_items 写回。run_sampling_request:1948 使用 history.for_prompt、1957 build_prompt 构建下一次请求。已核对 session/mod.rs:5330 的 clone_history 读取会话状态、session/inject.rs:140 的记录入口。教学只讲结果→历史→下次模型请求，不深入存储、元数据或并发队列实现；不把读取历史等同于硬编码 A→B 调度规则。

用户指出以上内容仍属于第一课。确认反馈成立：当前 lesson03 的线性工具 Demo 与结果回传源码主要是已学 Agent loop 的复用，不能作为新增依赖调度机制已经完成。停止重复讲解该路径。第 3 课真正的新内容尚未实施：将任务清单变为可执行的依赖计划，执行器维护任务状态/结果并检查启动条件，B 必须在 A 成功且所需数据可用后执行，即使模型提前提出 B 也不能绕过。严格业务依赖由程序规则校验或补充，不能仅信任模型提供的 depends_on。下一步从最小 A→B 计划及就绪判断开始，不再展开模型自主循环、流式事件、历史回传或重复问答。已有 lesson03 代码保留作基线。

以下保留第 2 课学习记录。

用户真实场景：A 是执行车控，B 是推荐车控动作；例如“我累了，帮我打开座椅按摩”，明确执行指令之外，业务规则还要求推荐。后续案例统一使用此场景；推荐不等于授权执行。先讲任务与依赖，再做顺序执行、并发、失败处理。

第 2 课已完成的小闭环：固定输入解析结果 → 应用业务规则 → 生成任务清单 → 分派到 mock 处理函数 → 对照 Rust 工具查找与执行。以 user_state、control_actions、recommendation_preference 表达解析结果；推荐偏好区分 requested/declined/unspecified，未提及推荐不等于拒绝推荐。

用户认为 source 字段当前业务不需要，已从第 2 课设计和外壳中移除。控制任务含 kind/action，推荐任务现含 kind/exclude_actions。保留概念上的显式请求与业务规则区别，不要求记录来源字段。

用户已提交 build_tasks 实现，并明确更新业务规则：只要用户没有明确拒绝，就生成一个 recommend 任务；不再要求疲劳状态或主动请求推荐。已按该规则同步到 outputs/lesson02/demo.py，并将 TypedDict 的属性访问 parsed.control_actions / parsed.recommendation_preference 修正为字典下标访问。保留用户用 ControlTask(...) / RecommendTask(...) 创建字典的写法。user_state 暂不参与是否推荐的判断，保留供后续推荐内容使用。

已更新“打开座椅按摩”用例的期望为控制加推荐，运行 python3 outputs/lesson02/demo.py，五个用例全部通过。第 2 课的任务生成小步骤已完成；尚未实现自然语言解析或缺参校验。

用户补充任务关联规则：推荐不需要等待控制执行成功与否，但不能重复推荐用户已明确要求的动作。当前通过 RecommendTask.exclude_actions 显式传递 parsed.control_actions 的副本，mock 推荐函数从固定候选中排除这些动作。去重基于已请求动作，不是成功执行的动作。这是共享输入产生的数据关联，不强制 A 执行后才能开始 B；未来遇到依赖运行结果的规则再增加执行依赖。

用户要求不再使用 TypedDict。第 2 课的 ParsedRequest、ControlTask、RecommendTask 已改为 Pydantic BaseModel，使用 parsed.control_actions、task.kind、task.action、task.exclude_actions 等属性访问；示例输入、期望结果和 JSON 展示同步迁移。依赖记在 outputs/lesson02/requirements.txt（pydantic>=2,<3），当前环境已有 2.13.4。第 1 课归档实现保留。

用户已完成 run_tasks：遍历任务、按 kind 分派、传入各自参数、收集结果。助手已同步实现，将 result 的类型由 list[Task] 修正为 list[str]、文档字符串移至函数首行，并用 elif 表达互斥分支（原两个 if 在当前类型下也正确）。任务生成五个用例仍全部通过；额外验证空列表、仅推荐不调用车控、控制加推荐传递排除列表、拒绝推荐不调用推荐、去重与字符串结果。

第 2 课当前 Python 小 Demo 已完成：固定解析输入 → 按业务规则生成任务 → 携带 exclude_actions 顺序分派 → 汇集 mock 结果。自然语言解析、缺参校验、依赖调度和并发均未实现，不把本例宣称为完整生产方案。

已开始第 2 课源码阅读，固定提交仍为 e54a5713caf331f42a6eef0166186df5f7563c29。当前只讲分派层：tools/parallel.rs:328 调用 ToolRouter::dispatch_tool_call_with_state（tools/router.rs:374），委托到 dispatch_tool_call_with_code_mode_result_inner（397）。其主流程是解构 ToolCall → 组装 ToolInvocation → registry.dispatch_any_with_state 返回工具结果。registry 暂视为按工具名查找并调用处理函数的黑盒；对照 Demo 的 run_tasks 分派部分，注意这两个 Router 方法一次处理单个调用，不负责遍历整个任务列表，也不负责车控业务的任务生成。用户尚未确认掌握本层。下一步再读 tools/registry.rs:729 的工具查找与执行路径。

用户补充提问：模型如何生成合法工具名与参数，以及上万工具如何处理。本步概念讲解 schema/支持时的 strict 输出约束/程序端名称白名单及 Pydantic 参数与业务校验；用座椅按摩参数举例。已核对 client.rs:1295 的 tools 请求字段、router.rs:278 将协议 name/arguments 转为内部 ToolCall、plan.rs:109 的参数反序列化，以及 tool_search_spec.rs 的 BM25 延迟工具发现描述。大工具集先按能力与上下文过滤、检索少量候选并提供 schema，检索不到或歧义时扩展检索/澄清；不把检索视为保证正确。仅解释，不新增真实模型接入或检索实现，之后返回工具路由主线。

用户已自行定位 registry.rs:773 的 registered_tool 查找，以及927行 log_tool_result_with_tags 包装的执行入口。确认主线理解正确；当前解释第934行闭包交给包装器执行，第二个闭包提取日志信息；handle_any_tool 内1061行 tool.handle(invocation.clone()).await? 才是具体处理器的统一调用点。不展开监控、动态分派或其他旁支。

用户已明确表示理解单工具调用，提出多个工具如何配合、严格顺序以及何时创建子 Agent，并要求合理安排、逐步推进。课程已更新：第 3 课先做单 Agent 的 A→结果→B 参数传递（mock 查询支持的按摩模式→启动相应模式），之后按需要引入显式依赖；第 4 课工具并发；第 5 课失败/条件分支；第 6 课子 Agent 委派。强调当前业务的 exclude_actions 来自已知输入，不依赖动作执行结果；普通工具并发不需要子 Agent。本次只调整设计，没有新建子 Agent 或实现后续 Demo。下次从第 3 课的两个工具串行协作这个小步开始。

以下保留第 1 课代码及学习记录。

Demo：`outputs/lesson01/demo.py`。
运行：`python3 outputs/lesson01/demo.py`。仅需 Python 标准库，不需要 API 密钥。

## 已完成

- 用户已理解：模型返回 tool_call 后，程序执行工具，将结果写回上下文，然后再请求模型；返回 final 后退出。
- 用户亲手实现 while 循环、TOOLS 函数映射、参数展开、工具执行和结果回传，并添加 TypedDict 响应类型。
- 助手按用户要求补齐模型响应的历史记录，放在模型响应之后、分支判断之前。
- 已运行验证：输出 `17 + 25 = 42`，历史角色顺序是 user → assistant(tool_call) → tool → assistant(final)。
- 循环外还保留了打印最终响应字典的调试语句。
- 用户已正确回答：漏掉工具结果回传时，当前 mock 会反复请求工具，循环无法正常结束；只有最后一条消息为 tool 时才返回 final。
- 用户已正确回答：正常 Demo 至少需要两轮模型请求，第一轮返回工具调用，第二轮看到工具结果后返回 final。
- 用户已亲手实现 max_rounds = 3 和 for ... else，保留 final 时的 break，达到上限时打印停止提示；助手已按用户提供的代码同步到项目。
- 已加入用户的 messages 类型标注 list[dict[str, str | Response]] 和 response = None 初始化。当前仅在循环后打印最后的响应字典。
- 已验证两条退出路径：正常 mock 请求两次后得到 final（17 + 25 = 42）；临时替换为始终请求工具的 mock 后，请求三次并打印达到上限提示。验证未修改项目中的 mock。
- 用户已正确回答 max_rounds = 1 的边界问题：最后的 response 仍为 tool_call，因为工具执行后已无法再次请求模型生成 final。Python 小 Demo 已完成，进入对应的 Codex Rust 源码阅读。
- 在阅读 Codex 响应事件后，用户明确要求将 Demo 改成流式；已将 mock_model 改为生成器 mock_model_stream，保留原 Response 类型和 messages 标注，新增六种 TypedDict 事件类型。
- 当前实现：外层按模型请求轮数循环，内层消费 created、output_item_added、tool_call_input_delta、output_text_delta、output_item_done、completed；增量即时打印，只在 output_item_done 保存完整 assistant 响应并执行工具、回传结果。completed 仅结束内层循环，外层根据每轮重置的 needs_follow_up 决定是否继续。
- 流式验证通过：正常运行两次模型请求、16 个事件、一次工具执行，输出 17 + 25 = 42，历史角色顺序正确；参数片段到达期间不执行工具，done 后恰好执行一次，文字片段即时显示。max_rounds=1 和持续请求工具到三轮上限均验证通过。
- run_agent(max_rounds=3, delay=0.2) 允许调整请求上限和片段延迟，并返回消息历史供检查；delay=0 可快速验证。末尾保留最后响应字典的调试输出。

## Demo 的简化

- mock_model_stream 仅模拟固定任务 17 + 25，最后一条消息是 tool 时流式生成 final，否则流式生成 add 工具调用。
- 每次模型响应只含一个工具调用或一个最终回答。
- 消息、响应和事件格式为自定义教学约定，不是正式 API 格式；output_item_done 携带完整响应项，参数片段只展示，执行使用完整项中的参数。
- 已实现请求轮数上限和流式事件消费；同步生成器配合 time.sleep 模拟事件逐段到达，没有真实网络请求、异步调度或并行工具执行。尚未实现错误处理、流中断恢复或会话持久化。

## 第 1 课阅读记录（归档）

以下记录保留讨论过程；第 1 课已经结束，不以其中旧的“当前/待理解”描述重新开启已结束的内容。

1. 漏掉工具结果和正常请求轮数的思考题均已完成。
2. 请求轮数上限及边界思考题已完成，不再重复 Demo 阶段的问题。
3. 流式 Demo 已按用户要求实现并验证。当前从外层 for、内层 for 和 output_item_done 分支讲解改动，等待用户消化；不把代码实现完成等同于用户已理解。
4. 已开始对照 Codex 源码：openai/codex，固定提交 e54a5713caf331f42a6eef0166186df5f7563c29，云端只读参考目录 /workspace/codex-reference。
5. 当前阅读点：codex-rs/core/src/session/turn.rs 的 run_turn（217 行），外层 loop（543 行）、clone_history / run_sampling_request（642 / 647 行）、needs_follow_up（690 行）和结束分支（805 行）。工具调用在 codex-rs/core/src/stream_events_utils.rs:404 设置 needs_follow_up = true。当前讲解简化为普通工具调用路径，真实代码还处理待输入消息、hooks 等情况，不将其等同于 Demo 的固定轮数限制。
6. 已解释 turn 是一轮 Agent 执行，可以包含多次模型请求；完整任务可以跨多个 turn。
7. 已讲解 handle_output_item_done 的 Ok(Some(call)) 分支和 turn.rs:3337 的 |= 汇总。用户已复述“接收处理结果、判断继续”的主线；当前澄清：OutputItemResult 由处理函数返回，不是工具本身的结果，工具结果通过 tool_future 获取；该状态经模型请求处理层汇总后传回 run_turn，并非 run_turn 直接调用 handle_output_item_done。
8. 已解释一次模型响应可含多个输出项，事件循环每项创建局部 output_result，循环外 needs_follow_up 用 |= 累积；下一次模型请求重新初始化为 false。用户已正确指出 Ok(None) 分支的 output.needs_follow_up 沿用 Default 的 false；已核对该分支确实没有修改它。强调这是当前输出项的状态，不会覆盖本次响应此前累计的 true。
9. 用户询问 ResponseEvent::OutputItemDone 和其他事件，已核对固定版本 codex-rs/codex-api/src/common.rs:82 的枚举定义。本步介绍 Created、OutputItemAdded、文本/工具参数 Delta、OutputItemDone、Completed，说明输出项完成不等于工具执行完成或整个 turn 完成；其余推理事件和元数据事件仅概览。
10. 用户询问 try_run_sampling_request 的背景。已核对并讲解调用层次：run_turn 管理 Agent 继续/结束；run_sampling_request 准备请求并处理可重试错误；try_run_sampling_request 执行请求尝试、消费响应事件、安排工具处理并等待未完成工具，返回 SamplingRequestResult 或错误。当前只解释正常路径和职责，未展开特殊重采样逻辑。try_ 是命名，不是 Rust 关键字；重试次数与 Demo 的请求轮数上限不同。
11. 已定位 try_run_sampling_request 中模型请求入口：turn.rs:2994 定义异步闭包 stream_request，内部调用 client_session.stream(...).await；3009–3011 调用闭包并 await，实际驱动请求，获取响应流。用户当前在核对这一调用位置，后续事件循环读取该流。
12. 用户询问 resampling.next(&mut stream).await 是否把响应处理成事件。已核对 guardian/response_resampling.rs:44：此处读取下一个已类型化的 ResponseEvent（优先缓冲项，否则 stream.next()），后面的 match 才分发处理。以 SSE 为例，底层 codex-api/src/sse/responses.rs 将服务端事件解析成 OutputItemDone、OutputTextDelta 等。区分底层解析、读取事件、分发处理三步。
13. 已解释外层 run_turn 循环负责多次模型请求，try_run_sampling_request 的事件循环消费当前响应；let outcome = loop 通过 break Ok(...) 得到返回值。用户正在梳理两层循环，不假定已掌握。
14. 当前问题是 model_needs_follow_up 如何决定继续：核对 turn.rs:663 的解构重命名，说明它来自 SamplingRequestResult.needs_follow_up，而不是在该行重新判断；工具处理状态经 |= 汇总返回，再与 has_pending_input 做或运算。额外核对 Completed.end_turn = Some(false) 也会设为 true，避免误认为仅工具调用能触发继续。
15. 已定位正常退出外层循环的代码：turn.rs:805 的 if !needs_follow_up 分支，最终在913行 break；915行 continue 用于继续外层循环。说明结束钩子可在842行要求继续，故 false 表示进入结束检查，并非无条件立刻退出。
16. 用户提交 run_turn 学习笔记，已正确概括外层请求、解构后续标记、合并待处理输入和退出判断。校正笔记：解构而非析构；Ok 返回二元组；needs_follow_up 判断须在 Ok 分支作用域内；异步调用要 await；Rust 注释用 //。同时保留 false 先进入结束检查的边界，不展开新主题。
17. 用户将 run_sampling_request:1934 的 loop 与事件循环混淆，当前明确区分三层：run_turn:543 的 Agent 继续循环；run_sampling_request:1934 的请求重试循环（调用 try_run_sampling_request，成功即 return，可恢复错误才重试）；try_run_sampling_request:3064 的响应事件循环。Demo 对应第一层与第三层，未实现中间的请求重试层。
18. 用户在整理文章后询问流式事件如何产生。已核对 client.rs:1303 的 ResponsesApiRequest.stream = true 和 codex-api/src/sse/responses.rs:375 的协议解析。解释：服务端根据响应生命周期及生成内容发送协议事件，客户端解析为 ResponseEvent，并非提示词要求模型生成 created/done 字符串；Demo 的 yield 模拟了服务端与解析后的事件接口。以 SSE 路径说明，避免认为所有传输或模型 API 都使用相同事件名。
19. 工具执行结果写回 session 历史的细读路径转入后续第 3 课，结合真实车控业务的数据依赖讲解。

## 跨设备接续说明

课程发布仓库为 https://github.com/kyoku-seii/simple-agent，使用 main 分支。下载、拉取和运行方式见 README.md；当前依赖执行示例是 outputs/lesson03/dependency_demo.py。同目录 demo.py 提供它导入的 mock 工具，请获取整个仓库而非仅复制单个文件。

这是课程摘要，不是原聊天逐条历史。云端新聊天应读取本文件与 AGENTS.md，再从当前进度继续。
云端聊天已从 main 提交 d9e6d573dac21ab8218d648c1af715eff7827ac3 取回三个课程文件，并运行 Demo 验证输出 `17 + 25 = 42`，迁移接续验证已完成。
