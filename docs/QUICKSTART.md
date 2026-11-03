# 比高数字人：从下载到跑通

## 1. 准备环境

- Python **3.10 或以上**，推荐 3.12；先执行 `python3 --version`。macOS 自带 Python 3.9 时请改用已安装的 `python3.12` 等新版解释器。
- Git 用于下载和更新；也可以在 GitHub 点击 **Code → Download ZIP**，解压后在项目目录打开终端。
- 规划、提示词和目录管理只用标准库。切片需要 NumPy；渲染需要 FFmpeg、ffprobe 和中文字体，推荐 FFmpeg 7+，实际能力以诊断结果为准。

macOS / Linux：

```bash
git clone https://github.com/bigao123456/bigao-shuziren.git
cd bigao-shuziren
python3 -m venv .venv
source .venv/bin/activate
python -m bigao_shuziren --version
python -m bigao_shuziren doctor
```

Windows PowerShell：

```powershell
git clone https://github.com/bigao123456/bigao-shuziren.git
cd bigao-shuziren
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m bigao_shuziren --version
.\.venv\Scripts\python.exe -m bigao_shuziren doctor
```

以下示例使用 `python`；Windows 可替换成 `.\.venv\Scripts\python.exe`，无需修改系统执行策略。所有命令都在仓库根目录运行；本项目尚未发布到 PyPI。

需要切片时安装依赖：

```bash
python -m pip install -r requirements.txt
python -m bigao_shuziren doctor --slicing
```

渲染能力检查：

```bash
python -m bigao_shuziren doctor --render
python -m bigao_shuziren doctor --render --json
```

诊断需找到 `ffmpeg`、`ffprobe`、`drawtext`、`subtitles`、`libx264` 和中文字体。macOS 可以安装带完整滤镜的 FFmpeg；Linux 可安装 `ffmpeg` 与 `fonts-noto-cjk`。Windows 默认搜索微软雅黑和黑体；其他字体用 `ISTREAM_FONT` 环境变量指定实际字体文件路径。字体本身的授权由提供方决定。

## 2. 先验证规划，不调用模型

仓库已包含提示词库和预期标签目录：

```bash
python -m bigao_shuziren prompts verify
python -m bigao_shuziren catalog validate --cat catalog/spec/plates.json
python -m bigao_shuziren plan recipes/gesture/script.md --cat catalog/gesture/plates.json --out build/quickstart/timeline.json
python -m bigao_shuziren qc build/quickstart/timeline.json --cat catalog/gesture/plates.json --strict
python -m bigao_shuziren lipsync plan build/quickstart/timeline.json --cat catalog/gesture/plates.json --engine passthrough --out build/quickstart/jobs.json
```

这一步的结果是时间轴、字幕规划、素材选择与口型任务清单。`catalog/spec` 和 `catalog/gesture` 是预期标签，生成自己的母片后必须复核，不能视作真实素材已验收。

## 3. 验证本地合成

先用短脚本验证，避免一开始就渲染长片。新建 `build/quickstart/script.md`：

```markdown
[开场] 大家好，今天演示比高数字人的素材复用流程。
[强调] 母片先准备，文案决定时间轴。
[关注] 欢迎收藏这个开源项目。
```

执行：

```bash
python -m bigao_shuziren plan build/quickstart/script.md --cat catalog/spec/plates.json --out build/quickstart/preview-timeline.json
python -m bigao_shuziren lipsync plan build/quickstart/preview-timeline.json --cat catalog/spec/plates.json --engine passthrough --out build/quickstart/preview-jobs.json
python -m bigao_shuziren render build/quickstart/preview-timeline.json --cat catalog/spec/plates.json --jobs build/quickstart/preview-jobs.json --workdir build/quickstart/render --out build/quickstart/preview.mp4 --scale 0.25 --engine passthrough
```

没有真实母片时，结果会显示 `SPEC PLACEHOLDER` 占位动画；没有配音时使用静音。预览证明本地装配可运行，不代表完成了真实数字人生成或口型同步。

## 4. 换成自己的素材

1. 准备有使用权的人物参考图、母片、文案和配音。`identity set --photo ...` 只整理参考图与生成提示词，不会自动生成人物视频或分析人脸身份。
2. 按 [SKILL.md](../SKILL.md) 准备母片，用 `slice` 生成待复核镜头，再用 `catalog merge-review` 合并人工复核。每个母片、镜头编号需唯一。
3. 用文案和对齐后的配音规划时间轴；配音在先，画面在后。未知标签会显示警告。
4. 运行 `render --stage inputs` 准备口型输入。实际调用自己的模型或服务，按任务清单把结果放进工作目录的 `lipsync/out/`。
5. 真实结果齐全后，使用 `render --stage composite --engine latentsync`（或对应的引擎标识）合成；此阶段只读取结果，不负责调用外部模型。检查输出后，再用 `ledger record` 记录素材使用。

`latentsync`、`musetalk` 等现有适配器仍是命令模板。直接运行未配置的引擎会返回退出码 2，不会假装成功。`--engine passthrough` 专供未同步预览；不要把预览当作真实口型成片。

## 常见问题

| 现象 | 处理 |
| --- | --- |
| `No module named bigao_shuziren` | 切换到仓库根目录，确认下载完整，再用虚拟环境的 Python 执行。 |
| Python 版本过低 | 换成 Python 3.10+ 创建虚拟环境，不要复用 3.9 创建的旧环境。 |
| 找不到 FFmpeg 或缺滤镜 | 安装完整构建，将其目录加入当前终端 PATH，然后重跑 `doctor --render`。 |
| 中文方块或字体缺失 | 安装中文字体，设置 `ISTREAM_FONT`，重新打开终端再诊断。 |
| `duplicate plate/shot id` | 两个素材库有相同编号。先统一修改母片编号、镜头编号及其引用，再合并。 |
| 多素材库指定独立 shots 文件 | 重复使用 `--cat plates.json`；显式文件对可写为 `--cat 'plates.json::shots.json'`，兼容旧的冒号写法。 |
| `NOT run` / `template adapter` | 服务尚未接入。按模板自行运行后合成，或明确选择 passthrough 预览。 |
| 成本看起来很低 | 内置数字是上游的历史估算，不是报价，且未覆盖所有配音、硬件、电力与人工成本。 |

## 验证和反馈

```bash
python tools/build_library.py
python -m bigao_shuziren prompts verify
python -m unittest discover -s tests -v
```

未安装 FFmpeg 时渲染测试会跳过；完整验证需先通过 `doctor --render`。提交 Issue 时附操作系统、Python 版本、诊断结果和最小复现步骤；不要提交密钥、私人参考图或未授权素材。欢迎在 [GitHub 仓库](https://github.com/bigao123456/bigao-shuziren) 点击 **Star** 收藏。
