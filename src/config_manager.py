"""
配置管理模块
"""
import os
import json
import configparser
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class LLMConfig:
    """LLM配置"""
    provider: str = "openai"
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 500


@dataclass
class CommitConfig:
    """提交配置"""
    language: str = "zh"
    use_conventional_commits: bool = True
    auto_commit: bool = False
    confirm_before_commit: bool = True
    max_subject_length: int = 50
    max_body_length: int = 72
    include_body: bool = True
    include_footer: bool = False


@dataclass
class AppConfig:
    """应用配置"""
    llm: LLMConfig
    commit: CommitConfig
    
    @classmethod
    def default(cls) -> 'AppConfig':
        return cls(
            llm=LLMConfig(),
            commit=CommitConfig()
        )


class ConfigManager:
    """配置管理器"""
    
    CONFIG_FILE_NAME = ".smartcommitrc"
    GLOBAL_CONFIG_DIR = Path.home() / ".config" / "smartcommit"
    GLOBAL_CONFIG_FILE = GLOBAL_CONFIG_DIR / "config.ini"
    
    def __init__(self):
        self.project_config_path: Optional[Path] = None
        self._find_project_config()
    
    def _find_project_config(self):
        """查找项目级配置文件"""
        current_dir = Path.cwd()
        
        # 向上查找.git目录
        while current_dir != current_dir.parent:
            git_dir = current_dir / ".git"
            if git_dir.exists():
                # 在git根目录查找配置文件
                config_file = current_dir / self.CONFIG_FILE_NAME
                if config_file.exists():
                    self.project_config_path = config_file
                break
            current_dir = current_dir.parent
    
    def load_config(self) -> AppConfig:
        """加载配置（项目级优先于全局配置）"""
        config = AppConfig.default()
        
        # 先加载全局配置
        if self.GLOBAL_CONFIG_FILE.exists():
            config = self._load_from_file(self.GLOBAL_CONFIG_FILE, config)
        
        # 再加载项目配置（覆盖全局配置）
        if self.project_config_path and self.project_config_path.exists():
            config = self._load_from_file(self.project_config_path, config)
        
        # 最后加载环境变量（最高优先级）
        config = self._load_from_env(config)
        
        return config
    
    def _load_from_file(self, file_path: Path, default_config: AppConfig) -> AppConfig:
        """从文件加载配置"""
        config = default_config
        
        try:
            parser = configparser.ConfigParser()
            parser.read(file_path, encoding='utf-8')
            
            # 加载LLM配置
            if 'llm' in parser.sections():
                llm_section = parser['llm']
                config.llm.provider = llm_section.get('provider', config.llm.provider)
                config.llm.api_key = llm_section.get('api_key', config.llm.api_key)
                config.llm.api_base = llm_section.get('api_base', config.llm.api_base)
                config.llm.model = llm_section.get('model', config.llm.model)
                config.llm.temperature = llm_section.getfloat('temperature', config.llm.temperature)
                config.llm.max_tokens = llm_section.getint('max_tokens', config.llm.max_tokens)
            
            # 加载提交配置
            if 'commit' in parser.sections():
                commit_section = parser['commit']
                config.commit.language = commit_section.get('language', config.commit.language)
                config.commit.use_conventional_commits = commit_section.getboolean(
                    'use_conventional_commits', config.commit.use_conventional_commits
                )
                config.commit.auto_commit = commit_section.getboolean(
                    'auto_commit', config.commit.auto_commit
                )
                config.commit.confirm_before_commit = commit_section.getboolean(
                    'confirm_before_commit', config.commit.confirm_before_commit
                )
                config.commit.max_subject_length = commit_section.getint(
                    'max_subject_length', config.commit.max_subject_length
                )
                config.commit.max_body_length = commit_section.getint(
                    'max_body_length', config.commit.max_body_length
                )
                config.commit.include_body = commit_section.getboolean(
                    'include_body', config.commit.include_body
                )
                config.commit.include_footer = commit_section.getboolean(
                    'include_footer', config.commit.include_footer
                )
        
        except Exception as e:
            print(f"Warning: Failed to load config from {file_path}: {e}")
        
        return config
    
    def _load_from_env(self, config: AppConfig) -> AppConfig:
        """从环境变量加载配置"""
        # LLM配置
        if os.getenv('SMARTCOMMIT_LLM_PROVIDER'):
            config.llm.provider = os.getenv('SMARTCOMMIT_LLM_PROVIDER')
        if os.getenv('SMARTCOMMIT_LLM_API_KEY'):
            config.llm.api_key = os.getenv('SMARTCOMMIT_LLM_API_KEY')
        if os.getenv('SMARTCOMMIT_LLM_API_BASE'):
            config.llm.api_base = os.getenv('SMARTCOMMIT_LLM_API_BASE')
        if os.getenv('SMARTCOMMIT_LLM_MODEL'):
            config.llm.model = os.getenv('SMARTCOMMIT_LLM_MODEL')
        if os.getenv('SMARTCOMMIT_LLM_TEMPERATURE'):
            try:
                config.llm.temperature = float(os.getenv('SMARTCOMMIT_LLM_TEMPERATURE'))
            except ValueError:
                pass
        if os.getenv('SMARTCOMMIT_LLM_MAX_TOKENS'):
            try:
                config.llm.max_tokens = int(os.getenv('SMARTCOMMIT_LLM_MAX_TOKENS'))
            except ValueError:
                pass
        
        # 提交配置
        if os.getenv('SMARTCOMMIT_LANGUAGE'):
            config.commit.language = os.getenv('SMARTCOMMIT_LANGUAGE')
        if os.getenv('SMARTCOMMIT_AUTO_COMMIT'):
            config.commit.auto_commit = os.getenv('SMARTCOMMIT_AUTO_COMMIT').lower() in ('true', '1', 'yes')
        
        # 兼容OpenAI/Anthropic官方环境变量
        if not config.llm.api_key:
            if config.llm.provider == 'openai' and os.getenv('OPENAI_API_KEY'):
                config.llm.api_key = os.getenv('OPENAI_API_KEY')
            elif config.llm.provider == 'anthropic' and os.getenv('ANTHROPIC_API_KEY'):
                config.llm.api_key = os.getenv('ANTHROPIC_API_KEY')
        
        return config
    
    def save_config(self, config: AppConfig, global_config: bool = False):
        """保存配置"""
        if global_config:
            self.GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            file_path = self.GLOBAL_CONFIG_FILE
        else:
            if not self.project_config_path:
                # 查找项目根目录
                current_dir = Path.cwd()
                while current_dir != current_dir.parent:
                    git_dir = current_dir / ".git"
                    if git_dir.exists():
                        self.project_config_path = current_dir / self.CONFIG_FILE_NAME
                        break
                    current_dir = current_dir.parent
                
                if not self.project_config_path:
                    raise ValueError("Not in a git repository")
            
            file_path = self.project_config_path
        
        parser = configparser.ConfigParser()
        
        # LLM配置
        parser['llm'] = {
            'provider': config.llm.provider,
            'api_key': config.llm.api_key or '',
            'api_base': config.llm.api_base or '',
            'model': config.llm.model,
            'temperature': str(config.llm.temperature),
            'max_tokens': str(config.llm.max_tokens)
        }
        
        # 提交配置
        parser['commit'] = {
            'language': config.commit.language,
            'use_conventional_commits': str(config.commit.use_conventional_commits),
            'auto_commit': str(config.commit.auto_commit),
            'confirm_before_commit': str(config.commit.confirm_before_commit),
            'max_subject_length': str(config.commit.max_subject_length),
            'max_body_length': str(config.commit.max_body_length),
            'include_body': str(config.commit.include_body),
            'include_footer': str(config.commit.include_footer)
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            parser.write(f)
    
    def get_default_config_content(self) -> str:
        """获取默认配置文件内容"""
        return """# SmartCommit-CLI 配置文件
# 项目级配置 (.smartcommitrc) 会覆盖全局配置

[llm]
# LLM提供商: openai, anthropic, ollama
provider = openai

# API密钥 (也可以通过环境变量 SMARTCOMMIT_LLM_API_KEY 或 OPENAI_API_KEY 设置)
api_key = 

# 自定义API基础URL (可选，用于代理或本地部署)
api_base = 

# 模型名称
model = gpt-3.5-turbo

# 温度参数 (0.0 - 2.0)
temperature = 0.7

# 最大生成token数
max_tokens = 500

[commit]
# 提交信息语言: zh (中文), en (英文), ja (日文)
language = zh

# 使用 Conventional Commits 规范
use_conventional_commits = true

# 自动生成后立即提交 (不经过确认)
auto_commit = false

# 提交前确认
confirm_before_commit = true

# 提交主题最大长度
max_subject_length = 50

# 提交正文行最大长度
max_body_length = 72

# 包含详细正文
include_body = true

# 包含页脚信息
include_footer = false
"""

    def init_config(self, global_config: bool = False) -> Path:
        """初始化配置文件"""
        if global_config:
            self.GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            file_path = self.GLOBAL_CONFIG_FILE
        else:
            current_dir = Path.cwd()
            while current_dir != current_dir.parent:
                git_dir = current_dir / ".git"
                if git_dir.exists():
                    file_path = current_dir / self.CONFIG_FILE_NAME
                    break
                current_dir = current_dir.parent
            else:
                raise ValueError("Not in a git repository")
        
        if file_path.exists():
            raise FileExistsError(f"Config file already exists: {file_path}")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.get_default_config_content())
        
        return file_path
