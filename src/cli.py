"""
CLI模块 - SmartCommit-CLI主入口
"""
import sys
import time
import click
from pathlib import Path
from typing import Optional

from . import __version__, __title__, __description__
from .config_manager import ConfigManager, AppConfig
from .git_analyzer import GitAnalyzer
from .llm_client import LLMClient
from .commit_generator import CommitGenerator, CommitMessage
from .commit_linter import CommitLinter, LintReport
from .utils import (
    Colors, colorize, print_success, print_error, print_warning, print_info,
    print_header, create_table, spinner_frame, clear_line, get_terminal_width
)


# 自定义Click参数类型
class ConfigParamType(click.ParamType):
    name = 'config'
    
    def convert(self, value, param, ctx):
        if value is None:
            return None
        return value


def get_analyzer() -> GitAnalyzer:
    """获取Git分析器"""
    analyzer = GitAnalyzer()
    if not analyzer.is_git_repository():
        print_error("当前目录不是Git仓库")
        sys.exit(1)
    return analyzer


def get_config() -> AppConfig:
    """获取配置"""
    config_manager = ConfigManager()
    return config_manager.load_config()


def get_llm_client(config: AppConfig) -> LLMClient:
    """获取LLM客户端"""
    return LLMClient(
        provider=config.llm.provider,
        api_key=config.llm.api_key,
        api_base=config.llm.api_base,
        model=config.llm.model,
        temperature=config.llm.temperature,
        max_tokens=config.llm.max_tokens
    )


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name=__title__)
@click.pass_context
def cli(ctx):
    """🚀 SmartCommit-CLI - AI驱动的智能Git提交助手
    
    使用AI自动生成高质量的Git提交信息，支持Conventional Commit规范
    
    示例:
        sc commit          # 生成并执行提交
        sc generate        # 仅生成提交信息
        sc config          # 配置管理
        sc lint            # 检查提交信息
        sc history         # 查看提交历史
    """
    if ctx.invoked_subcommand is None:
        # 默认执行generate命令
        ctx.invoke(generate)


@cli.command()
@click.option('--dry-run', '-d', is_flag=True, help='仅显示生成的提交信息，不执行提交')
@click.option('--edit', '-e', is_flag=True, help='编辑生成的提交信息')
@click.option('--language', '-l', type=click.Choice(['zh', 'en', 'ja']), help='提交信息语言')
def generate(dry_run: bool, edit: bool, language: Optional[str]):
    """生成提交信息"""
    print_header(f"{__title__} v{__version__}")
    
    # 初始化
    analyzer = get_analyzer()
    config = get_config()
    
    # 检查是否有暂存区变更
    if not analyzer.has_staged_changes():
        print_warning("暂存区没有变更")
        print_info("使用 'git add <files>' 添加要提交的文件")
        return
    
    # 分析变更
    print_info("正在分析代码变更...")
    file_changes, summary = analyzer.analyze_staged_changes()
    
    if not file_changes:
        print_error("无法分析变更")
        return
    
    # 显示变更摘要
    _display_changes_summary(file_changes, summary)
    
    # 检查LLM配置
    llm_client = get_llm_client(config)
    
    if not llm_client.api_key and llm_client.provider != 'ollama':
        print_error(f"未配置{config.llm.provider} API密钥")
        print_info(f"请设置环境变量: SMARTCOMMIT_LLM_API_KEY 或 {config.llm.provider.upper()}_API_KEY")
        print_info(f"或使用 'sc config' 命令进行配置")
        return
    
    # 生成提交信息
    print_info("正在生成提交信息...")
    
    # 显示进度动画
    _show_progress("AI思考中", 2)
    
    commit_gen = CommitGenerator(llm_client)
    lang = language or config.commit.language
    
    commit_message = commit_gen.generate(file_changes, summary, lang)
    
    if not commit_message:
        print_error("生成提交信息失败")
        return
    
    # 显示生成的提交信息
    print()
    _display_commit_message(commit_message, commit_gen)
    
    if dry_run:
        return
    
    # 编辑模式
    if edit or config.commit.confirm_before_commit:
        if not _confirm_commit(commit_message):
            print_info("已取消提交")
            return
    
    # 执行提交
    print_info("正在执行提交...")
    
    formatted_message = commit_message.format_message(
        include_body=config.commit.include_body,
        include_footer=config.commit.include_footer
    )
    
    if analyzer.commit(formatted_message):
        print_success("提交成功!")
        print()
        print(colorize("提交详情:", Colors.BOLD))
        print(f"  分支: {colorize(analyzer.get_current_branch(), Colors.CYAN)}")
        print(f"  提交: {colorize(commit_message.format_oneline(), Colors.GREEN)}")
    else:
        print_error("提交失败")


@cli.command()
@click.option('--message', '-m', help='提交信息（如果不提供则自动生成）')
@click.option('--language', '-l', type=click.Choice(['zh', 'en', 'ja']), help='提交信息语言')
def commit(message: Optional[str], language: Optional[str]):
    """生成并执行提交（generate的别名）"""
    if message:
        # 使用提供的提交信息
        analyzer = get_analyzer()
        if analyzer.commit(message):
            print_success("提交成功!")
        else:
            print_error("提交失败")
    else:
        # 自动生成
        ctx = click.get_current_context()
        ctx.invoke(generate, dry_run=False, edit=False, language=language)


@cli.command()
@click.argument('message', required=False)
def lint(message: Optional[str]):
    """检查提交信息格式"""
    linter = CommitLinter()
    
    if not message:
        # 获取最后一次提交信息作为示例
        analyzer = get_analyzer()
        message = analyzer.get_last_commit_message()
        
        if not message:
            print_error("无法获取提交信息")
            return
        
        print_info("检查最后一次提交信息:")
        print()
    
    # 显示要检查的提交信息
    print(colorize("提交信息:", Colors.BOLD))
    print("-" * 50)
    print(message)
    print("-" * 50)
    print()
    
    # 执行检查
    report = linter.lint(message)
    
    # 显示结果
    print(linter.format_report(report, verbose=True))
    
    if not report.is_valid:
        print()
        print_info("尝试自动修复...")
        fixed_message = linter.fix_message(message)
        
        if fixed_message != message:
            print(colorize("\n修复后的提交信息:", Colors.BOLD))
            print("-" * 50)
            print(fixed_message)
            print("-" * 50)


@cli.command()
@click.option('--global', 'global_config', is_flag=True, help='编辑全局配置')
@click.option('--init', 'init_config', is_flag=True, help='初始化配置文件')
def config(global_config: bool, init_config: bool):
    """配置管理"""
    config_manager = ConfigManager()
    
    if init_config:
        try:
            config_path = config_manager.init_config(global_config)
            print_success(f"配置文件已创建: {config_path}")
            print_info("请编辑配置文件设置您的API密钥和其他选项")
        except FileExistsError as e:
            print_warning(str(e))
        except ValueError as e:
            print_error(str(e))
        return
    
    # 显示当前配置
    config = config_manager.load_config()
    
    print_header("当前配置")
    
    # LLM配置
    print(colorize("LLM配置:", Colors.BOLD))
    print(f"  提供商: {colorize(config.llm.provider, Colors.CYAN)}")
    print(f"  模型: {colorize(config.llm.model, Colors.CYAN)}")
    api_key_status = colorize("已设置", Colors.GREEN) if config.llm.api_key else colorize("未设置", Colors.RED)
    print(f"  API密钥: {api_key_status}")
    if config.llm.api_base:
        print(f"  API基础URL: {config.llm.api_base}")
    print(f"  温度: {config.llm.temperature}")
    print(f"  最大Token: {config.llm.max_tokens}")
    print()
    
    # 提交配置
    print(colorize("提交配置:", Colors.BOLD))
    lang_names = {'zh': '中文', 'en': 'English', 'ja': '日本語'}
    print(f"  语言: {lang_names.get(config.commit.language, config.commit.language)}")
    print(f"  使用Conventional Commits: {'是' if config.commit.use_conventional_commits else '否'}")
    print(f"  自动提交: {'是' if config.commit.auto_commit else '否'}")
    print(f"  提交前确认: {'是' if config.commit.confirm_before_commit else '否'}")
    print(f"  最大主题长度: {config.commit.max_subject_length}")
    print()
    
    # 配置文件位置
    print(colorize("配置文件位置:", Colors.BOLD))
    if config_manager.project_config_path:
        print(f"  项目级: {config_manager.project_config_path}")
    else:
        print(f"  项目级: {colorize('未创建', Colors.YELLOW)}")
    print(f"  全局: {config_manager.GLOBAL_CONFIG_FILE}")
    print()
    
    print_info("使用 'sc config --init' 创建项目级配置")
    print_info("使用 'sc config --global --init' 创建全局配置")


@cli.command()
@click.option('--count', '-n', default=10, help='显示的提交数量')
def history(count: int):
    """查看提交历史"""
    analyzer = get_analyzer()
    commits = analyzer.get_commit_history(count)
    
    if not commits:
        print_warning("没有提交历史")
        return
    
    print_header(f"最近 {len(commits)} 次提交")
    
    linter = CommitLinter()
    
    for i, commit in enumerate(commits, 1):
        # 检查提交信息格式
        report = linter.lint(commit['message'])
        
        status = colorize("✓", Colors.GREEN) if report.is_valid else colorize("✗", Colors.RED)
        
        print(f"{status} {colorize(commit['hash'], Colors.YELLOW)} {commit['date']}")
        
        # 截断过长的提交信息
        message = commit['message'].split('\n')[0]
        if len(message) > 60:
            message = message[:57] + '...'
        print(f"  {message}")
        
        if i < len(commits):
            print()


# 辅助函数
def _display_changes_summary(file_changes: list, summary: 'ChangeSummary'):
    """显示变更摘要"""
    print()
    print(colorize("变更摘要:", Colors.BOLD))
    print("-" * 50)
    
    # 统计信息
    stats_data = [
        ["文件数", str(summary.total_files)],
        ["新增行", colorize(f"+{summary.additions}", Colors.GREEN)],
        ["删除行", colorize(f"-{summary.deletions}", Colors.RED)],
    ]
    
    for stat in stats_data:
        print(f"  {stat[0]:10s} {stat[1]}")
    
    print()
    
    # 文件列表
    print(colorize("变更文件:", Colors.BOLD))
    
    change_type_colors = {
        'added': Colors.GREEN,
        'modified': Colors.YELLOW,
        'deleted': Colors.RED,
        'renamed': Colors.CYAN,
    }
    
    for change in file_changes[:10]:  # 最多显示10个文件
        color = change_type_colors.get(change.change_type, Colors.WHITE)
        type_symbol = {
            'added': 'A',
            'modified': 'M',
            'deleted': 'D',
            'renamed': 'R',
        }.get(change.change_type, '?')
        
        stats = f"+{change.additions}/-{change.deletions}"
        print(f"  {colorize(type_symbol, color)} {change.path:40s} {stats:>10s}")
    
    if len(file_changes) > 10:
        print(f"  ... 还有 {len(file_changes) - 10} 个文件")
    
    print("-" * 50)
    print()


def _display_commit_message(commit_message: CommitMessage, generator: CommitGenerator):
    """显示提交信息"""
    print(colorize("生成的提交信息:", Colors.BOLD))
    print("=" * 50)
    
    # 类型和emoji
    emoji = generator.get_type_emoji(commit_message.type)
    type_desc = generator.get_type_description(commit_message.type)
    
    print(f"{emoji} {colorize(commit_message.type, Colors.CYAN)} - {type_desc}")
    
    if commit_message.scope:
        print(f"范围: {colorize(commit_message.scope, Colors.YELLOW)}")
    
    print()
    print(colorize("主题:", Colors.BOLD))
    print(f"  {commit_message.subject}")
    
    if commit_message.body:
        print()
        print(colorize("正文:", Colors.BOLD))
        for line in commit_message.body.split('\n'):
            print(f"  {line}")
    
    if commit_message.is_breaking:
        print()
        print(colorize("⚠️  破坏性变更", Colors.RED))
        if commit_message.breaking_change:
            print(f"  {commit_message.breaking_change}")
    
    print("=" * 50)
    print()


def _confirm_commit(commit_message: CommitMessage) -> bool:
    """确认提交"""
    print()
    
    # 提供选项
    print(colorize("请选择操作:", Colors.BOLD))
    print("  [y] 确认提交")
    print("  [n] 取消")
    print("  [e] 编辑提交信息")
    print("  [r] 重新生成")
    print()
    
    choice = click.prompt("您的选择", type=str, default='y').lower().strip()
    
    if choice == 'y':
        return True
    elif choice == 'n':
        return False
    elif choice == 'e':
        # 编辑提交信息（简化版，实际可以使用编辑器）
        print_info("编辑功能暂未实现，请使用--edit参数")
        return click.confirm("是否继续提交?", default=True)
    elif choice == 'r':
        print_info("重新生成...")
        # 这里可以重新调用生成逻辑
        return False
    else:
        print_warning("无效的选择")
        return False


def _show_progress(message: str, duration: float = 2.0):
    """显示进度动画"""
    start_time = time.time()
    frame = 0
    
    while time.time() - start_time < duration:
        spinner = spinner_frame(frame)
        print(f'\r{colorize(spinner, Colors.CYAN)} {message}...', end='', flush=True)
        time.sleep(0.1)
        frame += 1
    
    clear_line()


# 主入口
def main():
    """主入口函数"""
    try:
        cli()
    except KeyboardInterrupt:
        print()
        print_warning("操作已取消")
        sys.exit(130)
    except Exception as e:
        print_error(f"发生错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
