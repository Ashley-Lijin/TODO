from setuptools import setup, find_packages

setup(
    name="smart-planner",
    version="1.0.0",
    description="Claude-powered task planner with smart scheduling",
    packages=find_packages(where="Backend"),
    package_dir={"": "Backend"},
    install_requires=[
        "SQLAlchemy[asyncio]",
        "psycopg2-binary",
        "python-dotenv",
        "mcp",
        "trio",
        "fastapi",
        "uvicorn",
        "typer",
        "rich",
        "requests",
        "icalendar",
    ],
    entry_points={
        "console_scripts": [
            "todo=cli.todo:app",
        ],
    },
    python_requires=">=3.13",
)
