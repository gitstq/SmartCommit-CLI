#!/usr/bin/env python3
"""
SmartCommit-CLI 安装配置
"""
from setuptools import setup, find_packages
from pathlib import Path

# 读取README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding='utf-8') if readme_path.exists() else ""

# 读取版本
version_file = Path(__file__).parent / "src" / "__init__.py"
version = "1.0.0"
if version_file.exists():
    for line in version_file.read_text().split('\n'):
        if line.startswith('__version__'):
            version = line.split('=')[1].strip().strip('"\'')
            break

setup(
    name="smartcommit-cli",
    version=version,
    author="SmartCommit Team",
    author_email="smartcommit@example.com",
    description="AI驱动的智能Git提交助手",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/smartcommit-cli",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Version Control :: Git",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "gitpython>=3.1.0",
        "rich>=13.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "smartcommit=cli:main",
            "sc=cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="git, commit, ai, llm, conventional-commits, cli, developer-tools",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/smartcommit-cli/issues",
        "Source": "https://github.com/yourusername/smartcommit-cli",
        "Documentation": "https://github.com/yourusername/smartcommit-cli#readme",
    },
)
