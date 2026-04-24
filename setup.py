"""TradingLab Pro — Setup"""
from setuptools import setup, find_packages

setup(
    name="tradinglab-pro",
    version="2.0",
    description="Desktop algorithmic trading research platform",
    author="TradingLab",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=[
        "PyQt6>=6.6.0",
        "yfinance>=0.2.36",
        "pandas>=2.1.0",
        "numpy>=1.26.0",
        "matplotlib>=3.8.0",
        "scipy>=1.11.0",
        "requests>=2.31.0",
    ],
    entry_points={
        "console_scripts": [
            "tradinglab-pro=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)