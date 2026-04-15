#!/usr/bin/env python3
"""
Setup script for DDR5 AI Sandbox Simulator
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements
requirements = []
try:
    with open("requirements.txt", "r", encoding="utf-8") as f:
        requirements = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]
except FileNotFoundError:
    requirements = [
        "streamlit>=1.28.0",
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "scikit-learn>=1.0.0",
        "plotly>=5.0.0",
        "scipy>=1.7.0",
    ]

setup(
    name="ddr5-ai-sandbox-simulator",
    version="6.0.2",
    author="DDR5 AI Sandbox Simulator Team",
    author_email="",
    description=(
        "Professional AI-Powered DDR5 Memory Tuning Platform with Real-Time "
        "Hardware Integration & Enhanced Features"
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/killerbotofthenewworld/ddr5-ai-memory-tuner",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Scientific/Engineering",
        "Topic :: System :: Hardware",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "ddr5-simulator=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml"],
    },
    keywords=(
        "ddr5 memory tuning ai optimization simulator hardware real-time "
        "websocket 3d-charts llm damage-prevention automl predictive-maintenance"
    ),
    project_urls={
        "Bug Reports": (
            "https://github.com/killerbotofthenewworld/ddr5-ai-memory-tuner/issues"
        ),
        "Source": (
            "https://github.com/killerbotofthenewworld/ddr5-ai-memory-tuner"
        ),
        "Documentation": (
            "https://github.com/killerbotofthenewworld/ddr5-ai-memory-tuner#readme"
        ),
        "Ko-fi": "https://ko-fi.com/killerbotofthenewworld",
    },
)
