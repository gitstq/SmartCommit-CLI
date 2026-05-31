"""
Git变更分析模块
"""
import subprocess
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from .utils import extract_code_entities, detect_language, is_binary_file


@dataclass
class FileChange:
    """文件变更信息"""
    path: str
    change_type: str  # added, modified, deleted, renamed
    old_path: Optional[str] = None
    additions: int = 0
    deletions: int = 0
    diff_content: str = ""
    language: str = ""
    is_binary: bool = False
    entities: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class GitStatus:
    """Git状态信息"""
    staged_files: List[FileChange] = field(default_factory=list)
    unstaged_files: List[FileChange] = field(default_factory=list)
    untracked_files: List[str] = field(default_factory=list)
    is_clean: bool = True


@dataclass
class ChangeSummary:
    """变更摘要"""
    total_files: int = 0
    additions: int = 0
    deletions: int = 0
    files_by_type: Dict[str, int] = field(default_factory=dict)
    files_by_change_type: Dict[str, int] = field(default_factory=dict)
    functions_changed: List[str] = field(default_factory=list)
    classes_changed: List[str] = field(default_factory=list)


class GitAnalyzer:
    """Git分析器"""
    
    def __init__(self, repo_path: Optional[str] = None):
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.git_cmd = ['git', '-C', str(self.repo_path)]
    
    def _run_git_command(self, args: List[str]) -> Tuple[str, str, int]:
        """运行Git命令"""
        cmd = self.git_cmd + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            return "", str(e), 1
    
    def is_git_repository(self) -> bool:
        """检查是否为Git仓库"""
        _, _, code = self._run_git_command(['rev-parse', '--git-dir'])
        return code == 0
    
    def get_current_branch(self) -> str:
        """获取当前分支名"""
        stdout, _, code = self._run_git_command(['rev-parse', '--abbrev-ref', 'HEAD'])
        if code == 0:
            return stdout.strip()
        return "unknown"
    
    def get_status(self) -> GitStatus:
        """获取Git状态"""
        status = GitStatus()
        
        # 获取暂存区文件
        stdout, _, code = self._run_git_command([
            'diff', '--cached', '--name-status', '--diff-filter=ACDMRT'
        ])
        if code == 0:
            status.staged_files = self._parse_name_status(stdout)
        
        # 获取未暂存文件
        stdout, _, code = self._run_git_command([
            'diff', '--name-status', '--diff-filter=ACDMRT'
        ])
        if code == 0:
            status.unstaged_files = self._parse_name_status(stdout)
        
        # 获取未跟踪文件
        stdout, _, code = self._run_git_command([
            'ls-files', '--others', '--exclude-standard'
        ])
        if code == 0:
            status.untracked_files = [f for f in stdout.strip().split('\n') if f]
        
        status.is_clean = (
            not status.staged_files and
            not status.unstaged_files and
            not status.untracked_files
        )
        
        return status
    
    def _parse_name_status(self, output: str) -> List[FileChange]:
        """解析name-status输出"""
        files = []
        for line in output.strip().split('\n'):
            if not line:
                continue
            
            parts = line.split('\t')
            if len(parts) < 2:
                continue
            
            change_type_code = parts[0][0]
            change_type_map = {
                'A': 'added',
                'C': 'copied',
                'D': 'deleted',
                'M': 'modified',
                'R': 'renamed',
                'T': 'type_changed',
                'U': 'updated',
                'X': 'unknown'
            }
            
            change_type = change_type_map.get(change_type_code, 'unknown')
            
            if change_type == 'renamed' and len(parts) >= 3:
                file_change = FileChange(
                    path=parts[2],
                    change_type=change_type,
                    old_path=parts[1]
                )
            else:
                file_change = FileChange(
                    path=parts[1],
                    change_type=change_type
                )
            
            file_change.language = detect_language(file_change.path)
            file_change.is_binary = is_binary_file(file_change.path)
            files.append(file_change)
        
        return files
    
    def get_staged_diff(self, file_path: Optional[str] = None) -> str:
        """获取暂存区diff"""
        args = ['diff', '--cached', '--no-color']
        if file_path:
            args.extend(['--', file_path])
        
        stdout, _, _ = self._run_git_command(args)
        return stdout
    
    def get_file_diff_stats(self, file_change: FileChange) -> FileChange:
        """获取文件diff统计"""
        if file_change.is_binary:
            return file_change
        
        args = ['diff', '--cached', '--numstat', '--no-color', '--', file_change.path]
        stdout, _, _ = self._run_git_command(args)
        
        if stdout:
            parts = stdout.strip().split('\t')
            if len(parts) >= 2:
                try:
                    file_change.additions = int(parts[0]) if parts[0] != '-' else 0
                    file_change.deletions = int(parts[1]) if parts[1] != '-' else 0
                except ValueError:
                    pass
        
        # 获取diff内容
        args = ['diff', '--cached', '--no-color', '--', file_change.path]
        stdout, _, _ = self._run_git_command(args)
        file_change.diff_content = stdout
        
        # 提取代码实体
        if not file_change.is_binary:
            file_change.entities = extract_code_entities(stdout)
        
        return file_change
    
    def analyze_staged_changes(self) -> Tuple[List[FileChange], ChangeSummary]:
        """分析暂存区变更"""
        status = self.get_status()
        
        if not status.staged_files:
            return [], ChangeSummary()
        
        # 获取每个文件的详细信息
        detailed_files = []
        for file_change in status.staged_files:
            detailed_file = self.get_file_diff_stats(file_change)
            detailed_files.append(detailed_file)
        
        # 生成摘要
        summary = self._generate_summary(detailed_files)
        
        return detailed_files, summary
    
    def _generate_summary(self, files: List[FileChange]) -> ChangeSummary:
        """生成变更摘要"""
        summary = ChangeSummary()
        summary.total_files = len(files)
        
        for file_change in files:
            summary.additions += file_change.additions
            summary.deletions += file_change.deletions
            
            # 按文件类型统计
            lang = file_change.language
            summary.files_by_type[lang] = summary.files_by_type.get(lang, 0) + 1
            
            # 按变更类型统计
            change_type = file_change.change_type
            summary.files_by_change_type[change_type] = summary.files_by_change_type.get(change_type, 0) + 1
            
            # 收集变更的函数和类
            summary.functions_changed.extend(file_change.entities.get('functions', []))
            summary.classes_changed.extend(file_change.entities.get('classes', []))
        
        # 去重
        summary.functions_changed = list(set(summary.functions_changed))
        summary.classes_changed = list(set(summary.classes_changed))
        
        return summary
    
    def get_last_commit_message(self) -> str:
        """获取最后一次提交信息"""
        stdout, _, code = self._run_git_command(['log', '-1', '--pretty=%B'])
        if code == 0:
            return stdout.strip()
        return ""
    
    def get_commit_history(self, count: int = 10) -> List[Dict[str, str]]:
        """获取提交历史"""
        format_str = '%H|%s|%an|%ae|%ad'
        stdout, _, code = self._run_git_command([
            'log', f'-{count}', f'--pretty=format:{format_str}', '--date=short'
        ])
        
        commits = []
        if code == 0:
            for line in stdout.strip().split('\n'):
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 5:
                        commits.append({
                            'hash': parts[0][:7],
                            'message': parts[1],
                            'author': parts[2],
                            'email': parts[3],
                            'date': parts[4]
                        })
        
        return commits
    
    def stage_files(self, files: List[str]) -> bool:
        """暂存文件"""
        if not files:
            return False
        
        args = ['add'] + files
        _, _, code = self._run_git_command(args)
        return code == 0
    
    def unstage_files(self, files: List[str]) -> bool:
        """取消暂存文件"""
        if not files:
            return False
        
        args = ['reset', 'HEAD'] + files
        _, _, code = self._run_git_command(args)
        return code == 0
    
    def commit(self, message: str, allow_empty: bool = False) -> bool:
        """执行提交"""
        args = ['commit', '-m', message]
        if allow_empty:
            args.append('--allow-empty')
        
        _, _, code = self._run_git_command(args)
        return code == 0
    
    def has_staged_changes(self) -> bool:
        """检查是否有暂存区变更"""
        stdout, _, code = self._run_git_command([
            'diff', '--cached', '--quiet'
        ])
        # 返回码1表示有变更
        return code == 1
    
    def get_repo_root(self) -> Path:
        """获取仓库根目录"""
        stdout, _, code = self._run_git_command(['rev-parse', '--show-toplevel'])
        if code == 0:
            return Path(stdout.strip())
        return self.repo_path
