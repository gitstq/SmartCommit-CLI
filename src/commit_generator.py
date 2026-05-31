"""
提交信息生成器模块
"""
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from .llm_client import LLMClient, LLMResponse
from .git_analyzer import FileChange, ChangeSummary


@dataclass
class CommitMessage:
    """提交信息"""
    type: str
    scope: Optional[str]
    subject: str
    body: Optional[str]
    breaking_change: Optional[str]
    is_breaking: bool
    raw_message: str
    
    def format_message(self, include_body: bool = True, include_footer: bool = True) -> str:
        """格式化提交信息"""
        # 构建主题行
        if self.scope:
            header = f"{self.type}({self.scope}): {self.subject}"
        else:
            header = f"{self.type}: {self.subject}"
        
        if self.is_breaking:
            header = header.replace(':', '!:')
        
        lines = [header]
        
        # 添加正文
        if include_body and self.body:
            lines.append("")
            lines.append(self.body)
        
        # 添加破坏性变更说明
        if include_footer and self.breaking_change:
            lines.append("")
            lines.append(f"BREAKING CHANGE: {self.breaking_change}")
        
        return "\n".join(lines)
    
    def format_oneline(self) -> str:
        """单行格式"""
        if self.scope:
            return f"{self.type}({self.scope}): {self.subject}"
        return f"{self.type}: {self.subject}"


class CommitGenerator:
    """提交信息生成器"""
    
    # Conventional Commit 类型定义
    COMMIT_TYPES = {
        'feat': {'description': '新功能', 'emoji': '✨'},
        'fix': {'description': '修复', 'emoji': '🐛'},
        'docs': {'description': '文档', 'emoji': '📚'},
        'style': {'description': '代码格式', 'emoji': '💎'},
        'refactor': {'description': '重构', 'emoji': '♻️'},
        'perf': {'description': '性能优化', 'emoji': '🚀'},
        'test': {'description': '测试', 'emoji': '🧪'},
        'build': {'description': '构建', 'emoji': '📦'},
        'ci': {'description': 'CI/CD', 'emoji': '🔧'},
        'chore': {'description': '杂项', 'emoji': '🔨'},
        'revert': {'description': '回滚', 'emoji': '⏪'},
    }
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
    
    def generate(
        self,
        file_changes: List[FileChange],
        summary: ChangeSummary,
        language: str = "zh"
    ) -> Optional[CommitMessage]:
        """生成提交信息"""
        
        # 转换数据格式
        changes_data = []
        for change in file_changes:
            changes_data.append({
                'path': change.path,
                'change_type': change.change_type,
                'additions': change.additions,
                'deletions': change.deletions,
                'language': change.language,
                'entities': change.entities
            })
        
        summary_data = {
            'total_files': summary.total_files,
            'additions': summary.additions,
            'deletions': summary.deletions,
            'files_by_type': summary.files_by_type,
            'files_by_change_type': summary.files_by_change_type,
            'functions_changed': summary.functions_changed,
            'classes_changed': summary.classes_changed
        }
        
        # 调用LLM生成
        response = self.llm_client.generate_commit_message(
            changes_data, summary_data, language
        )
        
        if not response.success:
            return None
        
        # 解析生成的提交信息
        return self._parse_commit_message(response.content)
    
    def _parse_commit_message(self, raw_message: str) -> Optional[CommitMessage]:
        """解析提交信息"""
        lines = raw_message.strip().split('\n')
        if not lines:
            return None
        
        # 解析主题行
        header_line = lines[0]
        parsed_header = self._parse_header(header_line)
        
        if not parsed_header:
            # 如果解析失败，尝试将整个内容作为主题
            return CommitMessage(
                type='chore',
                scope=None,
                subject=header_line[:50],
                body=None,
                breaking_change=None,
                is_breaking=False,
                raw_message=raw_message
            )
        
        commit_type, scope, subject, is_breaking = parsed_header
        
        # 解析正文和页脚
        body_lines = []
        breaking_change = None
        in_body = False
        
        for i, line in enumerate(lines[1:], 1):
            line = line.strip()
            
            # 检查是否是BREAKING CHANGE
            if line.startswith('BREAKING CHANGE:'):
                breaking_change = line[len('BREAKING CHANGE:'):].strip()
                is_breaking = True
                continue
            
            # 检查是否是页脚的其他部分
            if re.match(r'^[\w-]+:', line):
                continue
            
            # 空行分隔
            if line == '':
                if in_body and body_lines:
                    body_lines.append('')
                continue
            
            body_lines.append(line)
            in_body = True
        
        # 清理正文
        body = '\n'.join(body_lines).strip() if body_lines else None
        
        return CommitMessage(
            type=commit_type,
            scope=scope,
            subject=subject,
            body=body if body else None,
            breaking_change=breaking_change,
            is_breaking=is_breaking,
            raw_message=raw_message
        )
    
    def _parse_header(self, header: str) -> Optional[tuple]:
        """解析主题行"""
        # 匹配格式: type(scope): subject 或 type!: subject 或 type(scope)!: subject
        pattern = r'^(\w+)(?:\(([^)]+)\))?(!)?:\s*(.+)$'
        match = re.match(pattern, header)
        
        if not match:
            return None
        
        commit_type = match.group(1).lower()
        scope = match.group(2)
        breaking_mark = match.group(3) == '!'
        subject = match.group(4).strip()
        
        # 验证类型
        if commit_type not in self.COMMIT_TYPES:
            # 如果类型未知，使用chore
            commit_type = 'chore'
        
        return (commit_type, scope, subject, breaking_mark)
    
    def validate_message(self, message: CommitMessage) -> List[str]:
        """验证提交信息"""
        errors = []
        
        # 验证类型
        if message.type not in self.COMMIT_TYPES:
            errors.append(f"未知的提交类型: {message.type}")
        
        # 验证主题长度
        if len(message.subject) > 50:
            errors.append(f"主题过长: {len(message.subject)} > 50字符")
        
        # 验证主题格式
        if message.subject.endswith('.'):
            errors.append("主题不应以句号结尾")
        
        # 验证主题首字母
        if message.subject and message.subject[0].isupper():
            errors.append("主题首字母不应大写")
        
        # 验证正文行长度
        if message.body:
            for i, line in enumerate(message.body.split('\n'), 1):
                if len(line) > 72:
                    errors.append(f"正文第{i}行过长: {len(line)} > 72字符")
        
        return errors
    
    def improve_message(self, message: CommitMessage) -> CommitMessage:
        """改进提交信息"""
        # 修复主题首字母大写
        subject = message.subject
        if subject and subject[0].isupper():
            subject = subject[0].lower() + subject[1:]
        
        # 移除主题末尾的句号
        if subject.endswith('.'):
            subject = subject[:-1]
        
        # 截断过长的主题
        if len(subject) > 50:
            subject = subject[:47] + '...'
        
        # 创建改进后的消息
        improved = CommitMessage(
            type=message.type,
            scope=message.scope,
            subject=subject,
            body=message.body,
            breaking_change=message.breaking_change,
            is_breaking=message.is_breaking,
            raw_message=message.raw_message
        )
        
        return improved
    
    def get_type_description(self, commit_type: str, language: str = "zh") -> str:
        """获取提交类型描述"""
        type_info = self.COMMIT_TYPES.get(commit_type)
        if not type_info:
            return commit_type
        
        descriptions = {
            'zh': type_info['description'],
            'en': commit_type,
            'ja': type_info['description']  # 简化处理
        }
        
        return descriptions.get(language, type_info['description'])
    
    def get_type_emoji(self, commit_type: str) -> str:
        """获取提交类型对应的emoji"""
        type_info = self.COMMIT_TYPES.get(commit_type)
        return type_info['emoji'] if type_info else '🔹'
    
    def suggest_scope(self, file_changes: List[FileChange]) -> Optional[str]:
        """建议scope"""
        # 从文件路径中提取可能的scope
        scopes = set()
        
        for change in file_changes:
            path = change.path
            
            # 提取目录名作为scope候选
            parts = path.split('/')
            if len(parts) > 1:
                # 使用第一级目录
                scopes.add(parts[0])
        
        # 返回最常见的scope
        if scopes:
            # 优先返回特定目录
            priority_scopes = ['src', 'api', 'ui', 'core', 'utils', 'tests', 'docs']
            for scope in priority_scopes:
                if scope in scopes:
                    return scope
            
            return min(scopes, key=len)  # 返回最短的
        
        return None
