# 项目结构与兼容性

比高版保留上游目录，避免已有提示词、时间轴和素材路径失效。

| 位置 | 职责 | 输入 → 输出 |
| --- | --- | --- |
| `bigao_shuziren/` | 品牌命令入口 | `python -m bigao_shuziren` → 同一个 istream 执行器 |
| `istream/__main__.py` | 参数校验、命令编排 | 命令 → 各业务模块 |
| `istream/environment.py` | 本地能力诊断 | Python/PATH/字体 → 文本或 JSON 报告 |
| `istream/identity.py`、`prompts.py` | 人物设定和提示词 | 参考图、配置 → 生成提示词包 |
| `istream/slicer.py`、`catalog.py` | 切片与素材目录 | 母片、标签、复核 → 镜头库与使用账本 |
| `istream/script.py`、`planner.py`、`timeline.py` | 文案驱动时间轴 | 文案、音频对齐、素材 → 时间轴与编辑差异 |
| `istream/lipsync.py` | 可见片段口型任务 | 时间轴、路由策略 → 任务清单、输入输出路径 |
| `istream/render.py` | FFmpeg 渲染与缓存 | 时间轴、素材、口型结果 → 视频、字幕与中间文件 |
| `istream/qc.py`、`cost.py` | 规则检查与历史成本估算 | 时间轴、标签、任务 → QC/估算报告 |
| `prompts/`、`catalog/`、`schema/` | 可复用提示词、示例目录、数据契约 | 原有格式继续兼容 |
| `recipes/`、`tools/`、`tests/` | 配方、构建工具、自动验证 | 复现流程与回归检查 |

处理顺序：文案 / 配音锁定 → 镜头规划 → 时间操作 → 可见片段口型 → 空间排版 / 动效 → 检查导出。配音与对齐数据由使用者准备；规划器也支持估算时长，但估算不能替代配音验收。

## 比高版行为变化

- 新入口和旧 `python -m istream` 共用实现。时间轴、标签、任务 JSON 的版本标识保留上游格式，避免破坏原数据。
- `--version` 输出比高版版本号；`doctor` 可用 `--render`、`--slicing`、`--json` 组合检查。
- 相同 ID 不再后写覆盖先写，合并素材库前须确保 ID 唯一。
- 未配置口型引擎、错误参数或缺文件返回退出码 **2**；环境诊断失败返回 **1**；成功返回 **0**。既有 `qc --strict` 仍以 **1** 表示检查失败。
- 真实引擎合成需要非空口型结果文件。存在文件不代表质量合格，仍需检查嘴型、声音、接缝和字幕。
- 内置外部引擎适配器是模板；本次没有接入新的收费服务，没有添加自动配音或模型权重。

完整能力与限制见 [ARCHITECTURE.md](../ARCHITECTURE.md)，原始制作演示见 [DEMO.md](../DEMO.md)，来源见 [NOTICE.md](../NOTICE.md)。
