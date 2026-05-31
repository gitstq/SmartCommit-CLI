# SmartCommit-CLI 项目设计方案

## 🎯 项目定位

**SmartCommit-CLI** 是一款AI驱动的智能Git提交助手，通过分析代码变更的语义内容，自动生成高质量的提交信息和代码审查建议，帮助开发者遵循Conventional Commit规范，提升代码提交质量和工作效率。

## 🌟 核心价值

1. **智能提交信息生成** - 基于代码变更的语义分析，自动生成清晰、规范的提交信息
2. **Conventional Commit自动格式化** - 自动识别提交类型(feat/fix/docs等)，规范化提交格式
3. **提交前代码质量检查** - 集成代码质量分析，在提交前发现潜在问题
4. **多LLM后端支持** - 支持OpenAI、Anthropic、Ollama等多种LLM提供商
5. **零依赖轻量化** - 纯Python实现，仅依赖标准库和少量必要库

## 🏗️ 技术架构

```
smartcommit/
├── src/
│   ├── __init__.py
│   ├── cli.py              # CLI入口和命令处理
│   ├── git_analyzer.py     # Git变更分析器
│   ├── llm_client.py       # LLM客户端封装
│   ├── commit_generator.py # 提交信息生成器
│   ├── commit_linter.py    # 提交信息检查器
│   ├── config_manager.py   # 配置管理
│   └── utils.py            # 工具函数
├── tests/
│   ├── __init__.py
│   ├── test_git_analyzer.py
│   ├── test_commit_generator.py
│   └── test_cli.py
├── docs/
│   ├── README_CN.md        # 简体中文文档
│   ├── README_TW.md        # 繁体中文文档
│   └── README_EN.md        # 英文文档
├── .github/
│   └── workflows/
│       └── ci.yml          # CI/CD配置
├── requirements.txt        # 依赖管理
├── setup.py               # 包配置
├── pyproject.toml         # 现代Python项目配置
├── LICENSE                # MIT许可证
└── README.md              # 主文档
```

## 📋 核心功能清单

### 1. Git变更分析 (git_analyzer.py)
- [x] 获取暂存区(staged)变更文件列表
- [x] 分析每个文件的变更类型(新增/修改/删除)
- [x] 提取代码变更的语义信息(函数名、类名、变量等)
- [x] 计算变更统计信息(行数、文件数等)
- [x] 识别变更的影响范围

### 2. LLM客户端 (llm_client.py)
- [x] 支持OpenAI API (GPT-3.5/4)
- [x] 支持Anthropic API (Claude)
- [x] 支持Ollama本地模型
- [x] 支持自定义API端点
- [x] 自动重试和错误处理
- [x] Token使用量追踪

### 3. 提交信息生成 (commit_generator.py)
- [x] 基于变更分析生成提交信息草稿
- [x] 自动识别Conventional Commit类型
- [x] 生成清晰的提交描述
- [x] 支持生成详细的提交正文
- [x] 支持生成Breaking Change标记
- [x] 多语言提交信息支持(中英日)

### 4. 提交信息检查 (commit_linter.py)
- [x] 验证Conventional Commit格式
- [x] 检查提交信息长度限制
- [x] 检查提交类型有效性
- [x] 检查Scope格式
- [x] 提供修复建议

### 5. CLI界面 (cli.py)
- [x] `smartcommit` / `sc` 主命令
- [x] `sc generate` - 生成提交信息
- [x] `sc commit` - 生成并执行提交
- [x] `sc config` - 配置管理
- [x] `sc lint` - 检查提交信息
- [x] `sc history` - 分析提交历史
- [x] 交互式TUI界面
- [x] 彩色输出和进度指示

### 6. 配置管理 (config_manager.py)
- [x] 配置文件读取和写入
- [x] 环境变量支持
- [x] 多配置文件支持(全局/项目级)
- [x] 配置验证
- [x] 默认配置生成

## 🔧 技术选型

| 组件 | 选择 | 理由 |
|------|------|------|
| CLI框架 | Click | 成熟稳定，支持命令嵌套和参数解析 |
| TUI界面 | Rich | 现代化终端UI，支持表格、面板、进度条 |
| Git操作 | GitPython | 功能完整，API友好 |
| HTTP请求 | urllib (标准库) | 零额外依赖，轻量级 |
| 配置解析 | configparser (标准库) | 标准库支持，无需额外依赖 |
| 测试框架 | pytest | 行业标准，功能强大 |

## 📐 数据模型

### 变更分析结果
```python
@dataclass
class GitChange:
    file_path: str
    change_type: str  # added, modified, deleted, renamed
    diff_content: str
    additions: int
    deletions: int
    functions_changed: List[str]
    classes_changed: List[str]
```

### 提交信息
```python
@dataclass
class CommitMessage:
    type: str  # feat, fix, docs, style, refactor, test, chore
    scope: Optional[str]
    subject: str
    body: Optional[str]
    breaking_change: Optional[str]
    is_breaking: bool
```

### LLM配置
```python
@dataclass
class LLMConfig:
    provider: str  # openai, anthropic, ollama
    api_key: Optional[str]
    api_base: Optional[str]
    model: str
    temperature: float
    max_tokens: int
```

## 🎨 用户交互流程

```
1. 用户在项目目录运行 `sc commit`
   ↓
2. 检查是否有暂存区变更
   ↓
3. 分析Git变更内容
   ↓
4. 调用LLM生成提交信息
   ↓
5. 显示生成的提交信息预览
   ↓
6. 用户确认/编辑/重新生成
   ↓
7. 执行git commit
   ↓
8. 显示提交结果
```

## 📝 Prompt设计

### 提交信息生成Prompt
```
你是一位专业的Git提交信息撰写专家。请根据以下代码变更信息，生成符合Conventional Commit规范的提交信息。

变更文件列表:
{file_list}

变更详情:
{diff_summary}

统计信息:
- 新增文件: {added_files} 个
- 修改文件: {modified_files} 个
- 删除文件: {deleted_files} 个
- 新增行数: {additions} 行
- 删除行数: {deletions} 行

请生成:
1. 提交类型 (feat/fix/docs/style/refactor/test/chore)
2. 影响范围 (可选，如api, ui, core等)
3. 简短的提交描述 (不超过50字符)
4. 详细的提交正文 (可选，说明变更原因和影响)
5. 是否有破坏性变更

输出格式:
type(scope): subject

body

BREAKING CHANGE: description (if any)
```

## 🧪 测试策略

1. **单元测试** - 覆盖所有核心模块
2. **集成测试** - 测试Git操作和LLM调用
3. **CLI测试** - 使用click.testing测试命令
4. **Mock测试** - 模拟LLM响应和Git操作

## 📦 打包与发布

### 支持的安装方式
1. pip安装: `pip install smartcommit-cli`
2. 源码安装: `python setup.py install`
3. 独立可执行文件: PyInstaller打包

### 发布平台
- PyPI (Python包索引)
- GitHub Releases (独立可执行文件)

## 🚀 迭代规划

### v1.0.0 (MVP)
- [x] 基础Git变更分析
- [x] OpenAI/Anthropic支持
- [x] 提交信息生成
- [x] 基础CLI界面

### v1.1.0
- [ ] Ollama本地模型支持
- [ ] 提交历史分析
- [ ] 多语言支持完善

### v1.2.0
- [ ] 提交信息模板自定义
- [ ] CI/CD集成
- [ ] VS Code插件

### v2.0.0
- [ ] 团队协作功能
- [ ] 提交规范检查预提交钩子
- [ ] Web Dashboard
