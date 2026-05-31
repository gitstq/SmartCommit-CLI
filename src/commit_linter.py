"""
提交信息检查模块
"""
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class LintRule:
    """检查规则"""
    id: str
    name: str
    description: str
    severity: str  # error, warning, info
    check: callable


@dataclass
class LintResult:
    """检查结果"""
    rule_id: str
    message: str
    severity: str
    line: Optional[int] = None
    column: Optional[int] = None


@dataclass
class LintReport:
    """检查报告"""
    is_valid: bool = True
    errors: List[LintResult] = field(default_factory=list)
    warnings: List[LintResult] = field(default_factory=list)
    infos: List[LintResult] = field(default_factory=list)
    
    def add_result(self, result: LintResult):
        """添加结果"""
        if result.severity == 'error':
            self.errors.append(result)
            self.is_valid = False
        elif result.severity == 'warning':
            self.warnings.append(result)
        else:
            self.infos.append(result)
    
    def get_all_results(self) -> List[LintResult]:
        """获取所有结果"""
        return self.errors + self.warnings + self.infos


class CommitLinter:
    """提交信息检查器"""
    
    # Conventional Commit 有效类型
    VALID_TYPES = {
        'feat', 'fix', 'docs', 'style', 'refactor',
        'perf', 'test', 'build', 'ci', 'chore', 'revert'
    }
    
    # 最大长度限制
    MAX_SUBJECT_LENGTH = 50
    MAX_BODY_LINE_LENGTH = 72
    MAX_SCOPE_LENGTH = 20
    
    def __init__(self):
        self.rules = self._init_rules()
    
    def _init_rules(self) -> List[LintRule]:
        """初始化检查规则"""
        return [
            LintRule(
                id='CC01',
                name='type-required',
                description='提交必须包含类型',
                severity='error',
                check=self._check_type_exists
            ),
            LintRule(
                id='CC02',
                name='type-valid',
                description='提交类型必须有效',
                severity='error',
                check=self._check_type_valid
            ),
            LintRule(
                id='CC03',
                name='subject-required',
                description='提交必须包含主题描述',
                severity='error',
                check=self._check_subject_exists
            ),
            LintRule(
                id='CC04',
                name='subject-length',
                description=f'主题描述不能超过{MAX_SUBJECT_LENGTH}个字符',
                severity='error',
                check=self._check_subject_length
            ),
            LintRule(
                id='CC05',
                name='subject-no-period',
                description='主题描述不应以句号结尾',
                severity='warning',
                check=self._check_subject_no_period
            ),
            LintRule(
                id='CC06',
                name='subject-lowercase',
                description='主题描述首字母不应大写',
                severity='warning',
                check=self._check_subject_lowercase
            ),
            LintRule(
                id='CC07',
                name='subject-imperative',
                description='主题描述应使用祈使语气',
                severity='info',
                check=self._check_subject_imperative
            ),
            LintRule(
                id='CC08',
                name='scope-length',
                description=f'影响范围不能超过{MAX_SCOPE_LENGTH}个字符',
                severity='error',
                check=self._check_scope_length
            ),
            LintRule(
                id='CC09',
                name='scope-format',
                description='影响范围格式应正确',
                severity='warning',
                check=self._check_scope_format
            ),
            LintRule(
                id='CC10',
                name='body-line-length',
                description=f'正文每行不能超过{MAX_BODY_LINE_LENGTH}个字符',
                severity='warning',
                check=self._check_body_line_length
            ),
            LintRule(
                id='CC11',
                name='body-blank-line',
                description='主题和正文之间应有空行',
                severity='warning',
                check=self._check_body_blank_line
            ),
            LintRule(
                id='CC12',
                name='breaking-change-format',
                description='破坏性变更格式应正确',
                severity='error',
                check=self._check_breaking_change_format
            ),
        ]
    
    def lint(self, commit_message: str) -> LintReport:
        """检查提交信息"""
        report = LintReport()
        
        # 解析提交信息
        parsed = self._parse_message(commit_message)
        
        # 应用所有规则
        for rule in self.rules:
            result = rule.check(commit_message, parsed)
            if result:
                report.add_result(result)
        
        return report
    
    def _parse_message(self, message: str) -> Dict[str, any]:
        """解析提交信息"""
        lines = message.strip().split('\n')
        
        result = {
            'header': lines[0] if lines else '',
            'body_lines': [],
            'footer_lines': [],
            'type': None,
            'scope': None,
            'subject': None,
            'is_breaking': False,
            'body': None,
            'breaking_change': None
        }
        
        if not lines:
            return result
        
        # 解析header
        header = lines[0]
        result['header'] = header
        
        # 匹配格式: type(scope): subject 或 type!: subject
        pattern = r'^(\w+)(?:\(([^)]+)\))?(!)?:\s*(.+)$'
        match = re.match(pattern, header)
        
        if match:
            result['type'] = match.group(1).lower()
            result['scope'] = match.group(2)
            result['is_breaking'] = match.group(3) == '!'
            result['subject'] = match.group(4).strip()
        
        # 分离body和footer
        in_footer = False
        for i, line in enumerate(lines[1:], 1):
            # 检查是否是footer开始
            if re.match(r'^[\w-]+(:| #)', line):
                in_footer = True
            
            if in_footer:
                result['footer_lines'].append((i + 1, line))
                
                # 检查BREAKING CHANGE
                if line.startswith('BREAKING CHANGE:'):
                    result['breaking_change'] = line[len('BREAKING CHANGE:'):].strip()
                    result['is_breaking'] = True
            else:
                result['body_lines'].append((i + 1, line))
        
        # 合并body
        if result['body_lines']:
            result['body'] = '\n'.join(line for _, line in result['body_lines'])
        
        return result
    
    # 规则检查方法
    def _check_type_exists(self, message: str, parsed: Dict) -> Optional[LintResult]:
        """检查类型是否存在"""
        if not parsed['type']:
            return LintResult(
                rule_id='CC01',
                message='提交信息缺少类型，格式应为: type: subject',
                severity='error',
                line=1
            )
        return None
    
    def _check_type_valid(self, message: str, parsed: Dict) -> Optional[LintResult]:
        """检查类型是否有效"""
        if parsed['type'] and parsed['type'] not in self.VALID_TYPES:
            valid_types = ', '.join(sorted(self.VALID_TYPES))
            return LintResult(
                rule_id='CC02',
                message=f"无效的提交类型 '{parsed['type']}'，有效类型: {valid_types}",
                severity='error',
                line=1
            )
        return None
    
    def _check_subject_exists(self, message: str, parsed: Dict) -> Optional[LintResult]:
        """检查主题是否存在"""
        if not parsed['subject'] or not parsed['subject'].strip():
            return LintResult(
                rule_id='CC03',
                message='提交信息缺少主题描述',
                severity='error',
                line=1
            )
        return None
    
    def _check_subject_length(self, message: str, parsed: Dict) -> Optional[LintResult]:
        """检查主题长度"""
        if parsed['subject'] and len(parsed['subject']) > self.MAX_SUBJECT_LENGTH:
            return LintResult(
                rule_id='CC04',
                message=f"主题描述过长: {len(parsed['subject'])} > {self.MAX_SUBJECT_LENGTH}字符",
                severity='error',
                line=1
            )
        return None
    
    def _check_subject_no_period(self, message: str, parsed: Dict) -> Optional[LintResult]:
        """检查主题是否以句号结尾"""
        if parsed['subject'] and parsed['subject'].endswith('.'):
            return LintResult(
                rule_id='CC05',
                message='主题描述不应以句号结尾',
                severity='warning',
                line=1
            )
        return None
    
    def _check_subject_lowercase(self, message: str, parsed: Dict) -> Optional[LintResult]:
        """检查主题首字母是否小写"""
        if parsed['subject']:
            subject = parsed['subject']
            # 允许以大写字母开头的情况（如专有名词）
            if subject[0].isupper() and not subject.startswith(('AI', 'API', 'UI', 'UX', 'HTTP', 'URL')):
                return LintResult(
                    rule_id='CC06',
                    message='主题描述首字母建议小写（除非是专有名词）',
                    severity='warning',
                    line=1
                )
        return None
    
    def _check_subject_imperative(self, message: str, parsed: Dict) -> Optional[LintResult]:
        """检查主题是否使用祈使语气"""
        if parsed['subject']:
            # 简单的启发式检查
            non_imperative_words = ['added', 'fixed', 'updated', 'changed', 'modified', 'removed', 'deleted']
            first_word = parsed['subject'].split()[0].lower().rstrip('ed')
            
            if first_word + 'ed' in non_imperative_words:
                return LintResult(
                    rule_id='CC07',
                    message=f"主题描述建议使用祈使语气，如 'add' 而非 'added'",
                    severity='info',
                    line=1
                )
        return None
    
    def _check_scope_length(self, message: str, parsed: Dict) -> Optional[LintResult]:
        """检查scope长度"""
        if parsed['scope'] and len(parsed['scope']) > self.MAX_SCOPE_LENGTH:
            return LintResult(
                rule_id='CC08',
                message=f"影响范围过长: {len(parsed['scope'])} > {self.MAX_SCOPE_LENGTH}字符",
                severity='error',
                line=1
            )
        return None
    
    def _check_scope_format(self, message: str, parsed: Dict) -> Optional[LintResult]:
        """检查scope格式"""
        if parsed['scope']:
            # scope应该使用kebab-case或camelCase
            if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', parsed['scope']):
                return LintResult(
                    rule_id='CC09',
                    message='影响范围应使用字母、数字、连字符或下划线，且以字母开头',
                    severity='warning',
                    line=1
                )
        return None
    
    def _check_body_line_length(self, message: str, parsed: Dict) -> Optional[LintResult]:
        """检查正文行长度"""
        for line_num, line in parsed['body_lines']:
            if len(line) > self.MAX_BODY_LINE_LENGTH:
                return LintResult(
                    rule_id='CC10',
                    message=f"正文第{line_num}行过长: {len(line)} > {self.MAX_BODY_LINE_LENGTH}字符",
                    severity='warning',
                    line=line_num
                )
        return None
    
    def _check_body_blank_line(self, message: str, parsed: Dict) -> Optional[LintResult]:
        """检查主题和正文之间是否有空行"""
        lines = message.split('\n')
        if len(lines) > 1 and parsed['body_lines']:
            if lines[1].strip() != '':
                return LintResult(
                    rule_id='CC11',
                    message='主题和正文之间应有空行分隔',
                    severity='warning',
                    line=2
                )
        return None
    
    def _check_breaking_change_format(self, message: str, parsed: Dict) -> Optional[LintResult]:
        """检查破坏性变更格式"""
        for line_num, line in parsed['footer_lines']:
            if line.startswith('BREAKING CHANGE') and not line.startswith('BREAKING CHANGE:'):
                return LintResult(
                    rule_id='CC12',
                    message='破坏性变更格式应为: BREAKING CHANGE: description',
                    severity='error',
                    line=line_num
                )
        return None
    
    def format_report(self, report: LintReport, verbose: bool = False) -> str:
        """格式化检查报告"""
        lines = []
        
        if not report.is_valid:
            lines.append("❌ 提交信息检查未通过")
        elif report.warnings:
            lines.append("⚠️  提交信息有警告")
        else:
            lines.append("✅ 提交信息格式正确")
        
        if report.errors:
            lines.append("\n错误:")
            for error in report.errors:
                lines.append(f"  [{error.rule_id}] {error.message}")
        
        if report.warnings:
            lines.append("\n警告:")
            for warning in report.warnings:
                lines.append(f"  [{warning.rule_id}] {warning.message}")
        
        if verbose and report.infos:
            lines.append("\n提示:")
            for info in report.infos:
                lines.append(f"  [{info.rule_id}] {info.message}")
        
        return '\n'.join(lines)
    
    def fix_message(self, message: str) -> str:
        """自动修复提交信息"""
        lines = message.strip().split('\n')
        if not lines:
            return message
        
        # 修复header
        header = lines[0]
        
        # 确保格式正确
        if ':' not in header:
            header = f"chore: {header}"
        
        # 修复主题首字母大写
        match = re.match(r'^(\w+)(?:\([^)]+\))?!?:\s*(.+)$', header)
        if match:
            commit_type = match.group(1)
            subject = match.group(2)
            
            # 首字母小写
            if subject and subject[0].isupper():
                subject = subject[0].lower() + subject[1:]
            
            # 移除末尾句号
            if subject.endswith('.'):
                subject = subject[:-1]
            
            # 截断过长主题
            if len(subject) > self.MAX_SUBJECT_LENGTH:
                subject = subject[:47] + '...'
            
            header = f"{commit_type}: {subject}"
        
        lines[0] = header
        
        # 修复正文行长度
        fixed_lines = [lines[0]]
        
        for i, line in enumerate(lines[1:], 1):
            if len(line) > self.MAX_BODY_LINE_LENGTH:
                # 尝试在单词边界处截断
                words = line.split()
                current_line = ""
                for word in words:
                    if len(current_line) + len(word) + 1 <= self.MAX_BODY_LINE_LENGTH:
                        current_line += " " + word if current_line else word
                    else:
                        if current_line:
                            fixed_lines.append(current_line)
                        current_line = word
                if current_line:
                    fixed_lines.append(current_line)
            else:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
