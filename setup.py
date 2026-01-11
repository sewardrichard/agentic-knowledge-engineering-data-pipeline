from setuptools import setup, find_packages

setup(
    name="aura-knowledge-pipeline",
    version="1.0.0",
    description="Knowledge Engineering Pipeline for Aura AI Agent - Deloitte Submission",
    author="Seward Mupereri",
    packages=find_packages(),
    install_requires=[
        "dlt[duckdb]>=0.4.0",
        "fastapi>=0.104.0",
        "pandas>=2.1.0",
    ],
    python_requires=">=3.10",
)