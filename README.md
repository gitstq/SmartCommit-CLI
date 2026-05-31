<div align="center">

# 🚀 SmartCommit-CLI

**AI驱动的智能Git提交助手**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.0.0-orange.svg)](https://github.com/gitstq/SmartCommit-CLI/releases)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

[简体中文](#简体中文) | [繁體中文](#繁體中文) | [English](#english)

</div>

---

## 简体中文

### 🎉 项目介绍

**SmartCommit-CLI** 是一款AI驱动的智能Git提交助手，通过分析代码变更的语义内容，自动生成高质量的提交信息，帮助开发者遵循[Conventional Commits](https://www.conventionalcommits.org/)规范，提升代码提交质量和工作效率。

**灵感来源**: 在日常开发中，编写清晰、规范的Git提交信息是一项耗时且容易出错的任务。SmartCommit-CLI利用AI技术自动化这一过程，让开发者能够专注于代码本身。

**差异化亮点**:
- 🤖 **智能语义分析** - 不仅分析代码变更，更理解变更的意图
- 🎯 **多LLM支持** - 支持OpenAI、Anthropic、Ollama等多种AI模型
- 🌐 **多语言输出** - 支持中文、英文、日文提交信息生成
- ⚡ **零依赖轻量化** - 核心功能仅依赖Python标准库
- 🔒 **隐私优先** - 支持本地LLM，代码不上传云端

### ✨ 核心特性

| 特性 | 描述 | 状态 |
|------|------|------|
| 🤖 **AI智能生成** | 基于代码变更自动生成提交信息 | ✅ |
| 📝 **Conventional Commits** | 严格遵循规范，自动识别类型 | ✅ |
| 🌍 **多语言支持** | 中文/英文/日文提交信息 | ✅ |
| 🔧 **多LLM后端** | OpenAI、Anthropic、Ollama | ✅ |
| 🎨 **美观TUI** | 彩色终端界面，进度动画 | ✅ |
| 📊 **变更分析** | 详细的代码变更统计 | ✅ |
| ✅ **提交检查** | 自动检查提交信息格式 | ✅ |
| ⚙️ **灵活配置** | 项目级+全局配置支持 | ✅ |

### 🚀 快速开始

#### 环境要求

- **Python**: 3.8 或更高版本
- **Git**: 2.0 或更高版本
- **操作系统**: Windows / macOS / Linux

#### 安装

**方式一：通过 pip 安装（推荐）**

```bash
pip install smartcommit-cli
```

**方式二：从源码安装**

```bash
git clone https://github.com/gitstq/SmartCommit-CLI.git
cd SmartCommit-CLI
pip install -e .
```

#### 配置

**1. 初始化配置**

```bash
# 创建项目级配置
sc config --init

# 或创建全局配置
sc config --global --init
```

**2. 设置API密钥（环境变量方式）**

```bash
# OpenAI
export OPENAI_API_KEY="your-api-key"

# 或 Anthropic
export ANTHROPIC_API_KEY="your-api-key"

# 或使用 SmartCommit 专用变量
export SMARTCOMMIT_LLM_API_KEY="your-api-key"
```

**3. 编辑配置文件**

配置文件位于 `.smartcommitrc`（项目级）或 `~/.config/smartcommit/config.ini`（全局）：

```ini
[llm]
provider = openai
api_key = your-api-key
model = gpt-3.5-turbo
temperature = 0.7

[commit]
language = zh
use_conventional_commits = true
auto_commit = false
```

#### 使用

**基本使用**

```bash
# 进入Git仓库
cd your-git-repo

# 添加文件到暂存区
git add .

# 生成并执行提交
sc commit

# 或仅生成提交信息（不执行）
sc generate --dry-run

# 生成后编辑再提交
sc generate --edit
```

**其他命令**

```bash
# 检查提交信息格式
sc lint "feat: add new feature"

# 查看提交历史
sc history

# 查看配置
sc config
```

### 📖 详细使用指南

#### 命令详解

| 命令 | 别名 | 描述 | 示例 |
|------|------|------|------|
| `sc generate` | `sc` | 生成提交信息 | `sc generate --dry-run` |
| `sc commit` | - | 生成并提交 | `sc commit -m "manual message"` |
| `sc lint` | - | 检查提交信息 | `sc lint "feat: add feature"` |
| `sc history` | - | 查看历史 | `sc history -n 20` |
| `sc config` | - | 配置管理 | `sc config --init` |

#### 支持的提交类型

| 类型 | 描述 | Emoji |
|------|------|-------|
| `feat` | 新功能 | ✨ |
| `fix` | 修复Bug | 🐛 |
| `docs` | 文档更新 | 📚 |
| `style` | 代码格式 | 💎 |
| `refactor` | 代码重构 | ♻️ |
| `perf` | 性能优化 | 🚀 |
| `test` | 测试相关 | 🧪 |
| `build` | 构建系统 | 📦 |
| `ci` | CI/CD配置 | 🔧 |
| `chore` | 其他杂项 | 🔨 |

### 💡 设计思路与迭代规划

#### 技术选型

- **Click**: 成熟的Python CLI框架，支持命令嵌套
- **GitPython**: 功能完整的Git操作库
- **Rich**: 现代化终端UI库
- **urllib**: 标准库HTTP客户端，零额外依赖

#### 后续迭代计划

**v1.1.0**
- [ ] Ollama本地模型深度集成
- [ ] 提交历史智能分析
- [ ] 自定义提交模板

**v1.2.0**
- [ ] VS Code插件
- [ ] JetBrains插件
- [ ] CI/CD集成

**v2.0.0**
- [ ] 团队协作功能
- [ ] 提交规范统计Dashboard
- [ ] Web管理界面

### 📦 打包与部署

#### 构建独立可执行文件

```bash
# 安装PyInstaller
pip install pyinstaller

# 构建
pyinstaller --onefile --name smartcommit src/cli.py

# 输出在 dist/ 目录
```

#### 发布到PyPI

```bash
# 安装构建工具
pip install build twine

# 构建
python -m build

# 发布
python -m twine upload dist/*
```

### 🤝 贡献指南

欢迎提交Issue和Pull Request！

**提交规范**:
- 使用Conventional Commits格式
- 确保代码通过flake8检查
- 添加必要的测试用例
- 更新相关文档

**开发流程**:
```bash
# 克隆仓库
git clone https://github.com/gitstq/SmartCommit-CLI.git

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black src

# 类型检查
mypy src
```

### 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

---

## 繁體中文

### 🎉 專案介紹

**SmartCommit-CLI** 是一款AI驅動的智能Git提交助手，通過分析程式碼變更的語義內容，自動生成高品質的提交資訊，幫助開發者遵循[Conventional Commits](https://www.conventionalcommits.org/)規範，提升程式碼提交品質和工作效率。

**核心價值**:
- 🤖 **智慧語義分析** - 理解變更意圖，不只是分析檔案
- 🎯 **多LLM支援** - OpenAI、Anthropic、Ollama等
- 🌐 **多語言輸出** - 支援繁體中文、英文、日文
- ⚡ **輕量化設計** - 核心功能僅依賴Python標準庫
- 🔒 **隱私優先** - 支援本地LLM，程式碼不上傳

### ✨ 核心特性

- ✅ AI智慧生成提交資訊
- ✅ 嚴格遵循Conventional Commits規範
- ✅ 多語言支援（繁體中文/英文/日文）
- ✅ 多LLM後端支援
- ✅ 美觀的終端介面
- ✅ 詳細的變更分析
- ✅ 提交資訊格式檢查
- ✅ 靈活的配置管理

### 🚀 快速開始

#### 安裝

```bash
pip install smartcommit-cli
```

#### 配置

```bash
# 設定API金鑰
export OPENAI_API_KEY="your-api-key"

# 初始化配置
sc config --init
```

#### 使用

```bash
# 添加檔案到暫存區
git add .

# 生成並執行提交
sc commit
```

### 📖 詳細文檔

更多詳細資訊請參考[简体中文](#简体中文)部分或訪問我們的[文檔站點](https://github.com/gitstq/SmartCommit-CLI/wiki)。

### 📄 開源協議

[MIT License](LICENSE)

---

## English

### 🎉 Introduction

**SmartCommit-CLI** is an AI-powered intelligent Git commit assistant that automatically generates high-quality commit messages by analyzing the semantic content of code changes. It helps developers follow the [Conventional Commits](https://www.conventionalcommits.org/) specification, improving commit quality and productivity.

**Key Features**:
- 🤖 **AI-Powered Generation** - Understands the intent behind code changes
- 🎯 **Multi-LLM Support** - OpenAI, Anthropic, Ollama, and more
- 🌐 **Multi-Language** - Chinese, English, Japanese commit messages
- ⚡ **Lightweight** - Core functionality uses only Python standard library
- 🔒 **Privacy-First** - Supports local LLMs, code never leaves your machine

### ✨ Features

- ✅ AI-powered commit message generation
- ✅ Strict Conventional Commits compliance
- ✅ Multi-language support (Chinese/English/Japanese)
- ✅ Multiple LLM backend support
- ✅ Beautiful terminal UI
- ✅ Detailed change analysis
- ✅ Commit message linting
- ✅ Flexible configuration

### 🚀 Quick Start

#### Installation

```bash
pip install smartcommit-cli
```

#### Configuration

```bash
# Set API key
export OPENAI_API_KEY="your-api-key"

# Initialize configuration
sc config --init
```

#### Usage

```bash
# Stage your changes
git add .

# Generate and commit
sc commit
```

### 📖 Documentation

For detailed documentation, please refer to the [简体中文](#简体中文) section or visit our [Wiki](https://github.com/gitstq/SmartCommit-CLI/wiki).

### 📄 License

[MIT License](LICENSE)

---

<div align="center">

**Made with ❤️ by SmartCommit Team**

[⭐ Star us on GitHub](https://github.com/gitstq/SmartCommit-CLI) | [🐛 Report Issue](https://github.com/gitstq/SmartCommit-CLI/issues) | [💡 Feature Request](https://github.com/gitstq/SmartCommit-CLI/issues)

</div>
