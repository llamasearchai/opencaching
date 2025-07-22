#!/usr/bin/env python3
"""Setup script for the OpenAI-Style Caching Infrastructure Platform."""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "OpenAI-Style Caching Infrastructure Platform"

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="caching-platform",
    version="1.0.0",
    author="Nik Jois",
    author_email="nikjois@llamasearch.ai",
    description="OpenAI-Style multi-tenant caching infrastructure platform with autonomous management",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/llamasearchai/opencaching",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Database",
        "Topic :: System :: Distributed Computing",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "myst-parser>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "caching-platform=caching_platform.cli.interface:main",
        ],
    },
    include_package_data=True,
    package_data={
        "caching_platform": [
            "config/*.yaml",
            "config/*.yml",
            "config/*.json",
            "monitoring/dashboards/*.json",
            "monitoring/rules/*.yml",
        ],
    },
    zip_safe=False,
    keywords=[
        "caching",
        "redis",
        "distributed",
        "multi-tenant",
        "autonomous",
        "ai",
        "ml",
        "scaling",
        "monitoring",
        "infrastructure",
        "platform",
    ],
    project_urls={
        "Bug Reports": "https://github.com/llamasearchai/caching-platform/issues",
        "Source": "https://github.com/llamasearchai/caching-platform",
        "Documentation": "https://caching-platform.readthedocs.io/",
    },
)