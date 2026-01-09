from setuptools import find_packages, setup

setup(
    name="backroom-agent",
    version="0.1.0",
    description="Backrooms Agent Game System",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "langgraph>=0.2.0",
        "langchain-core>=0.3.0",
        "langchain-openai>=0.3.0",
        "langsmith>=0.1.0",
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "fastapi>=0.115.0",
        "uvicorn>=0.30.0",
        "pydantic>=2.0.0",
        "graphviz>=0.20.1",
    ],
    entry_points={
        "console_scripts": [
            "backroom-agent=backroom_agent.__main__:main",
            "backroom-generate-graph=backroom_agent.utils.map_generator:generate_level_graph",
        ],
    },
)
