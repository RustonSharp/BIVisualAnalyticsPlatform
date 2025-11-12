"""
BI Visual Analytics Platform
轻量级 BI 数据可视化与分析平台
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="bi-visual-analytics",
    version="1.0.0",
    author="BI Platform Team",
    author_email="contact@example.com",
    description="轻量级 BI 数据可视化与分析平台",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/bi-visual-analytics",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Office/Business",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "bi-dashboard=app:main",
        ],
    },
    include_package_data=True,
    package_data={
        "bi_visual_analytics": [
            "config/*.yaml",
            "config/*.json",
            "data/*.csv",
        ],
    },
)
