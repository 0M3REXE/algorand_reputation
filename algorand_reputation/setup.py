from pathlib import Path
from setuptools import setup, find_packages

README = (Path(__file__).parent.parent / "README.md").read_text(encoding="utf-8")

setup(
    name="algorand_reputation",
    version="0.1.1",
    packages=find_packages(include=["algorand_reputation", "algorand_reputation.*"]),
    install_requires=["algosdk>=2.6.0"],
    extras_require={
        "dev": ["pytest", "ruff", "mypy"],
    },
    description="Heuristic reputation scoring utilities for Algorand accounts.",
    long_description=README,
    long_description_content_type="text/markdown",
    author="Omer Abdullah",
    author_email="omerhyd8080@gmail.com",
    url="https://github.com/0M3REXE/algorand_reputation",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
)
