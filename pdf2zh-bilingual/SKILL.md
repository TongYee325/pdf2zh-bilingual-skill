---
name: pdf2zh-bilingual
description: 使用固定版本的 PDF2zh-Next 将本地英文 PDF 全文翻译为左英右中对照 PDF，适合翻译学术论文、报告和其他带文字层的 PDF，支持批量处理。用于用户要求 PDF2zh 翻译或生成中英对照 PDF 时。
---

# PDF 中英对照翻译

1. 确定本次要处理的本地 PDF 文件和目标目录。默认在每份原文同目录生成 `<原名>_中英对照.pdf`。批量使用明确的文件清单。
2. 翻译前检查工具链。将下文的脚本占位符替换为此 Skill 目录中 `scripts/translate.py` 的绝对路径。

   - 先运行 `uv --version`。找不到命令时，检查当前用户的安装目录，例如 `~/.local/bin` 和 Windows 的 `%LOCALAPPDATA%\Microsoft\WinGet\Links`。仍缺失时帮用户安装。Windows 优先用 `winget install --id astral-sh.uv --exact`，有 Homebrew 的 macOS 用 `brew install uv`，其他环境使用 [Astral 官方独立安装器](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer)。安装后用新 shell 或 `uv` 的绝对路径复查。
   - 用 `uv python find --no-python-downloads 3.12` 检查 Python 3.12。缺失时执行 `uv python install 3.12`，再复查。
   - 先运行 `uv run --offline --no-python-downloads --script "/path/to/pdf2zh-bilingual/scripts/translate.py" --check-toolchain`。如果本地依赖环境或缓存不足，去掉 `--offline` 再运行一次，由 `uv` 安装脚本声明的依赖。检查成功后继续翻译。遇到系统权限、依赖加载或网络错误，处理具体报错并复查。

3. 用命令执行工具运行固定翻译入口。

   ```sh
   uv run --script "/path/to/pdf2zh-bilingual/scripts/translate.py" "paper.pdf" "another-paper.pdf" --output-dir "译文"
   ```

   翻译固定使用 PDF2zh-Next 2.9.0 的 Python API 和 SiliconFlow Free，英文到简体中文，全文左右并排。初次翻译会准备版面识别模型和字体。该服务会接收待翻译文本。遵循用户给出的数据处理范围。扫描件需要先获得可提取的文字层。
4. 等待脚本退出，逐项报告已生成、同名文件已存在或失败，并给出成品路径。脚本依次处理每份文件，核验页数、左右版式和译文侧文字，可用原清单重跑其余文件。若已有同名译文且原文更新了，使用新输出目录。用户要求放入 Zotero 时，完成翻译后将结果挂到相应文献条目。
