# 参与比高数字人

欢迎提交使用问题、文档修正和代码改进。先阅读 [中文入门](docs/QUICKSTART.md) 和 [项目结构](docs/PROJECT_GUIDE.md)。

提交问题时请附：操作系统、Python 版本、执行命令、预期结果、实际结果，以及 `python -m bigao_shuziren doctor --render --json` 的输出。请移除用户名、密钥和私人素材路径。

提交 PR 前执行：

```bash
python -m bigao_shuziren prompts verify
python -m unittest discover -s tests -v
```

核心逻辑需保持标准库可运行；NumPy 仅用于切片等可选功能。修复行为问题时增加对应回归用例。调整定稿提示词、标签契约或时间轴格式时，请说明兼容性影响并更新文档。

不要将 API Key、授权令牌、私人参考图、模型权重或未获授权的声音视频提交到仓库。原始上游来源与 MIT 许可证需保留。
