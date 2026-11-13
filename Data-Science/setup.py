from setuptools import setup, find_packages

setup(
    name="trend_detective",
    version="1.0.0",
    description="NASA Earth Observation Statistical Trend Engine & Physical Driver Attribution",
    author="Trend Detective Team (NASA Space Apps Challenge 2026)",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "pandas>=2.0.0",
        "pymannkendall>=1.4.3",
        "requests>=2.28.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "matplotlib>=3.7.0",
        ]
    },
)
