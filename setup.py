"""
Setup configuration for foodScrapper package.
"""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="foodScrapper",
    version="0.1.0",
    author="Reyad Hassan",
    description="Multi-website food delivery scraper using Playwright",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/reyadhsupto/foodScrapper-pyPlay",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
        "playwright>=1.40.0",
        "playwright-stealth>=1.0.1",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.0",
    ],
)
