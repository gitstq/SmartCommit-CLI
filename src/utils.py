"""
工具函数模块
"""
import re
import os
import sys
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class Colors:
    """终端颜色定义"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    
    # 前景色
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # 亮前景色
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    # 背景色
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


def colorize(text: str, color: str) -> str:
    """为文本添加颜色"""
    return f"{color}{text}{Colors.RESET}"


def print_success(message: str):
    """打印成功消息"""
    print(f"{Colors.GREEN}✓{Colors.RESET} {message}")


def print_error(message: str):
    """打印错误消息"""
    print(f"{Colors.RED}✗{Colors.RESET} {message}", file=sys.stderr)


def print_warning(message: str):
    """打印警告消息"""
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")


def print_info(message: str):
    """打印信息消息"""
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {message}")


def print_header(title: str):
    """打印标题"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}  {title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.RESET}\n")


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """截断文本到指定长度"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def extract_code_entities(diff_content: str) -> Dict[str, List[str]]:
    """从diff内容中提取代码实体（函数名、类名等）"""
    entities = {
        "functions": [],
        "classes": [],
        "variables": [],
        "imports": []
    }
    
    # 提取Python函数和类
    func_pattern = r'^\+.*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
    class_pattern = r'^\+.*class\s+([a-zA-Z_][a-zA-Z0-9_]*)'
    import_pattern = r'^\+.*(?:import|from)\s+([a-zA-Z_][a-zA-Z0-9_.]*)'
    
    for line in diff_content.split('\n'):
        # 函数
        func_match = re.search(func_pattern, line)
        if func_match:
            func_name = func_match.group(1)
            if func_name not in entities["functions"]:
                entities["functions"].append(func_name)
        
        # 类
        class_match = re.search(class_pattern, line)
        if class_match:
            class_name = class_match.group(1)
            if class_name not in entities["classes"]:
                entities["classes"].append(class_name)
        
        # 导入
        import_match = re.search(import_pattern, line)
        if import_match:
            import_name = import_match.group(1)
            if import_name not in entities["imports"]:
                entities["imports"].append(import_name)
    
    return entities


def get_file_extension(filename: str) -> str:
    """获取文件扩展名"""
    return os.path.splitext(filename)[1].lower()


def detect_language(filename: str) -> str:
    """根据文件名检测编程语言"""
    ext = get_file_extension(filename)
    language_map = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'React',
        '.tsx': 'React TypeScript',
        '.java': 'Java',
        '.go': 'Go',
        '.rs': 'Rust',
        '.c': 'C',
        '.cpp': 'C++',
        '.h': 'C/C++ Header',
        '.hpp': 'C++ Header',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.r': 'R',
        '.m': 'Objective-C',
        '.cs': 'C#',
        '.fs': 'F#',
        '.ex': 'Elixir',
        '.exs': 'Elixir',
        '.erl': 'Erlang',
        '.hs': 'Haskell',
        '.lua': 'Lua',
        '.pl': 'Perl',
        '.sh': 'Shell',
        '.bash': 'Bash',
        '.zsh': 'Zsh',
        '.ps1': 'PowerShell',
        '.sql': 'SQL',
        '.html': 'HTML',
        '.htm': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.sass': 'Sass',
        '.less': 'Less',
        '.json': 'JSON',
        '.xml': 'XML',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.toml': 'TOML',
        '.ini': 'INI',
        '.cfg': 'Config',
        '.conf': 'Config',
        '.md': 'Markdown',
        '.rst': 'reStructuredText',
        '.txt': 'Text',
        '.dockerfile': 'Dockerfile',
        '.makefile': 'Makefile',
        '.cmake': 'CMake',
    }
    return language_map.get(ext, 'Unknown')


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def is_binary_file(filename: str) -> bool:
    """检查是否为二进制文件"""
    binary_extensions = {
        '.exe', '.dll', '.so', '.dylib', '.bin',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
        '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv',
        '.zip', '.tar', '.gz', '.bz2', '.7z', '.rar',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.db', '.sqlite', '.sqlite3',
        '.o', '.obj', '.a', '.lib',
        '.pyc', '.pyo', '.class',
    }
    return get_file_extension(filename) in binary_extensions


def sanitize_branch_name(name: str) -> str:
    """清理分支名称，使其符合Git规范"""
    # 替换非法字符
    name = re.sub(r'[^a-zA-Z0-9_\-\/]', '-', name)
    # 移除连续的连字符
    name = re.sub(r'-+', '-', name)
    # 移除首尾连字符
    name = name.strip('-')
    # 限制长度
    return name[:100]


def parse_conventional_commit(message: str) -> Dict[str, Optional[str]]:
    """解析Conventional Commit格式的提交信息"""
    pattern = r'^(\w+)(?:\(([^)]+)\))?!?:\s*(.+?)(?:\n\n(.+))?$'
    match = re.match(pattern, message, re.DOTALL)
    
    if match:
        return {
            'type': match.group(1),
            'scope': match.group(2),
            'subject': match.group(3).strip(),
            'body': match.group(4).strip() if match.group(4) else None,
            'is_valid': True
        }
    
    return {
        'type': None,
        'scope': None,
        'subject': message.strip(),
        'body': None,
        'is_valid': False
    }


def validate_commit_type(commit_type: str) -> bool:
    """验证提交类型是否有效"""
    valid_types = {
        'feat', 'fix', 'docs', 'style', 'refactor',
        'perf', 'test', 'build', 'ci', 'chore', 'revert'
    }
    return commit_type.lower() in valid_types


def get_commit_type_description(commit_type: str) -> str:
    """获取提交类型的描述"""
    descriptions = {
        'feat': '新功能',
        'fix': '修复',
        'docs': '文档',
        'style': '代码格式',
        'refactor': '重构',
        'perf': '性能优化',
        'test': '测试',
        'build': '构建',
        'ci': 'CI/CD',
        'chore': '杂项',
        'revert': '回滚'
    }
    return descriptions.get(commit_type.lower(), '未知类型')


def create_table(headers: List[str], rows: List[List[str]], max_width: int = 80) -> str:
    """创建简单的ASCII表格"""
    if not rows:
        return ""
    
    # 计算每列的最大宽度
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # 限制宽度
    col_widths = [min(w, max_width // len(headers)) for w in col_widths]
    
    # 创建分隔线
    separator = "+" + "+".join(["-" * (w + 2) for w in col_widths]) + "+"
    
    # 创建表头
    header_row = "|" + "|".join([f" {headers[i]:{col_widths[i]}} " for i in range(len(headers))]) + "|"
    
    # 创建数据行
    data_rows = []
    for row in rows:
        row_str = "|" + "|".join([f" {str(row[i] if i < len(row) else ''):{col_widths[i]}} " for i in range(len(headers))]) + "|"
        data_rows.append(row_str)
    
    # 组合表格
    table = [separator, header_row, separator] + data_rows + [separator]
    return "\n".join(table)


def spinner_frame(frame_index: int) -> str:
    """获取旋转动画帧"""
    frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    return frames[frame_index % len(frames)]


def clear_line():
    """清除当前行"""
    print('\r\033[K', end='', flush=True)


def get_terminal_width() -> int:
    """获取终端宽度"""
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80


def wrap_text(text: str, width: int = None) -> str:
    """自动换行文本"""
    if width is None:
        width = get_terminal_width() - 4
    
    lines = []
    current_line = ""
    
    for word in text.split():
        if len(current_line) + len(word) + 1 <= width:
            current_line += " " + word if current_line else word
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return "\n".join(lines)
