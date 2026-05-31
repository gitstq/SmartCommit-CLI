"""
LLM客户端模块
支持OpenAI、Anthropic、Ollama等多种LLM提供商
"""
import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List, Generator
from dataclasses import dataclass
from .utils import print_error, print_warning


@dataclass
class LLMResponse:
    """LLM响应"""
    content: str
    tokens_used: int = 0
    tokens_prompt: int = 0
    tokens_completion: int = 0
    model: str = ""
    success: bool = True
    error_message: Optional[str] = None


class LLMClient:
    """LLM客户端"""
    
    def __init__(
        self,
        provider: str = "openai",
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 500,
        timeout: int = 60
    ):
        self.provider = provider.lower()
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        
        # 设置默认API基础URL
        self._set_default_api_base()
    
    def _set_default_api_base(self):
        """设置默认API基础URL"""
        if self.api_base:
            return
        
        defaults = {
            'openai': 'https://api.openai.com/v1',
            'anthropic': 'https://api.anthropic.com/v1',
            'ollama': 'http://localhost:11434',
        }
        self.api_base = defaults.get(self.provider, 'https://api.openai.com/v1')
    
    def _make_request(self, url: str, headers: Dict[str, str], data: Dict[str, Any]) -> Dict[str, Any]:
        """发送HTTP请求"""
        try:
            request = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode('utf-8'))
        
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            try:
                error_json = json.loads(error_body)
                error_message = error_json.get('error', {}).get('message', error_body)
            except:
                error_message = error_body or str(e)
            
            return {
                'error': True,
                'error_message': f"HTTP {e.code}: {error_message}"
            }
        
        except Exception as e:
            return {
                'error': True,
                'error_message': str(e)
            }
    
    def generate_commit_message(
        self,
        file_changes: List[Dict[str, Any]],
        summary: Dict[str, Any],
        language: str = "zh"
    ) -> LLMResponse:
        """生成提交信息"""
        
        # 构建prompt
        prompt = self._build_commit_prompt(file_changes, summary, language)
        
        # 根据提供商调用不同的API
        if self.provider == 'openai':
            return self._call_openai(prompt)
        elif self.provider == 'anthropic':
            return self._call_anthropic(prompt)
        elif self.provider == 'ollama':
            return self._call_ollama(prompt)
        else:
            return LLMResponse(
                content="",
                success=False,
                error_message=f"Unsupported provider: {self.provider}"
            )
    
    def _build_commit_prompt(
        self,
        file_changes: List[Dict[str, Any]],
        summary: Dict[str, Any],
        language: str
    ) -> str:
        """构建提交信息生成prompt"""
        
        # 语言设置
        lang_names = {
            'zh': '中文',
            'en': 'English',
            'ja': '日本語'
        }
        lang_name = lang_names.get(language, '中文')
        
        # 构建文件列表描述
        file_descriptions = []
        for change in file_changes[:10]:  # 限制文件数量
            desc = f"- {change['path']} ({change['change_type']}, +{change['additions']}/-{change['deletions']})"
            if change.get('entities', {}).get('functions'):
                funcs = ', '.join(change['entities']['functions'][:3])
                desc += f" [函数: {funcs}]"
            if change.get('entities', {}).get('classes'):
                classes = ', '.join(change['entities']['classes'][:2])
                desc += f" [类: {classes}]"
            file_descriptions.append(desc)
        
        if len(file_changes) > 10:
            file_descriptions.append(f"... 还有 {len(file_changes) - 10} 个文件")
        
        file_list = '\n'.join(file_descriptions)
        
        # 构建统计信息
        stats = f"""总文件数: {summary['total_files']}
新增行数: {summary['additions']}
删除行数: {summary['deletions']}"""
        
        if summary.get('files_by_type'):
            stats += f"\n文件类型分布: {summary['files_by_type']}"
        
        if summary.get('functions_changed'):
            stats += f"\n涉及函数: {', '.join(summary['functions_changed'][:5])}"
        
        if summary.get('classes_changed'):
            stats += f"\n涉及类: {', '.join(summary['classes_changed'][:3])}"
        
        # 构建完整prompt
        prompt = f"""你是一位专业的Git提交信息撰写专家。请根据以下代码变更信息，生成符合Conventional Commit规范的提交信息。

## 变更文件列表
{file_list}

## 统计信息
{stats}

## 要求
1. 提交类型必须是以下之一:
   - feat: 新功能
   - fix: 修复bug
   - docs: 文档更新
   - style: 代码格式调整(不影响代码逻辑)
   - refactor: 代码重构
   - perf: 性能优化
   - test: 测试相关
   - build: 构建系统或外部依赖
   - ci: CI/CD配置
   - chore: 其他杂项

2. 提交描述要求:
   - 使用{lang_name}撰写
   - 简洁明了，不超过50个字符
   - 使用动词开头(如: 添加、修复、更新、重构等)
   - 描述做了什么，而不是怎么做的

3. 提交正文要求(可选):
   - 详细说明变更原因
   - 描述主要变更内容
   - 每行不超过72个字符

4. 如果有破坏性变更，请在页脚标注

## 输出格式
请严格按照以下格式输出，不要添加任何其他内容:

type(scope): subject

body

BREAKING CHANGE: description (if applicable)

其中scope是可选的，表示变更范围(如api, ui, core等)。
"""
        
        return prompt
    
    def _call_openai(self, prompt: str) -> LLMResponse:
        """调用OpenAI API"""
        if not self.api_key:
            return LLMResponse(
                content="",
                success=False,
                error_message="OpenAI API key is required"
            )
        
        url = f"{self.api_base}/chat/completions"
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        data = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': 'You are a Git commit message expert.'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': self.temperature,
            'max_tokens': self.max_tokens
        }
        
        response = self._make_request(url, headers, data)
        
        if 'error' in response:
            return LLMResponse(
                content="",
                success=False,
                error_message=response.get('error_message', 'Unknown error')
            )
        
        try:
            choice = response['choices'][0]
            content = choice['message']['content']
            usage = response.get('usage', {})
            
            return LLMResponse(
                content=content.strip(),
                tokens_used=usage.get('total_tokens', 0),
                tokens_prompt=usage.get('prompt_tokens', 0),
                tokens_completion=usage.get('completion_tokens', 0),
                model=response.get('model', self.model),
                success=True
            )
        except (KeyError, IndexError) as e:
            return LLMResponse(
                content="",
                success=False,
                error_message=f"Failed to parse response: {e}"
            )
    
    def _call_anthropic(self, prompt: str) -> LLMResponse:
        """调用Anthropic API"""
        if not self.api_key:
            return LLMResponse(
                content="",
                success=False,
                error_message="Anthropic API key is required"
            )
        
        url = f"{self.api_base}/messages"
        
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01'
        }
        
        data = {
            'model': self.model or 'claude-3-haiku-20240307',
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'messages': [
                {'role': 'user', 'content': prompt}
            ]
        }
        
        response = self._make_request(url, headers, data)
        
        if 'error' in response:
            return LLMResponse(
                content="",
                success=False,
                error_message=response.get('error_message', 'Unknown error')
            )
        
        try:
            content = response['content'][0]['text']
            usage = response.get('usage', {})
            
            return LLMResponse(
                content=content.strip(),
                tokens_used=usage.get('input_tokens', 0) + usage.get('output_tokens', 0),
                tokens_prompt=usage.get('input_tokens', 0),
                tokens_completion=usage.get('output_tokens', 0),
                model=response.get('model', self.model),
                success=True
            )
        except (KeyError, IndexError) as e:
            return LLMResponse(
                content="",
                success=False,
                error_message=f"Failed to parse response: {e}"
            )
    
    def _call_ollama(self, prompt: str) -> LLMResponse:
        """调用Ollama本地API"""
        url = f"{self.api_base}/api/generate"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': self.model or 'llama2',
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': self.temperature
            }
        }
        
        response = self._make_request(url, headers, data)
        
        if 'error' in response:
            return LLMResponse(
                content="",
                success=False,
                error_message=response.get('error_message', 'Unknown error')
            )
        
        try:
            content = response['response']
            
            return LLMResponse(
                content=content.strip(),
                tokens_used=response.get('eval_count', 0) + response.get('prompt_eval_count', 0),
                tokens_prompt=response.get('prompt_eval_count', 0),
                tokens_completion=response.get('eval_count', 0),
                model=response.get('model', self.model),
                success=True
            )
        except KeyError as e:
            return LLMResponse(
                content="",
                success=False,
                error_message=f"Failed to parse response: {e}"
            )
    
    def test_connection(self) -> bool:
        """测试LLM连接"""
        if self.provider == 'ollama':
            try:
                url = f"{self.api_base}/api/tags"
                request = urllib.request.Request(url, method='GET')
                with urllib.request.urlopen(request, timeout=5) as response:
                    return response.status == 200
            except:
                return False
        else:
            # 对于云API，简单测试API key是否存在
            return bool(self.api_key)
