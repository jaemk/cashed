from setuptools import setup, find_packages

setup(
    name="cashed",
    version="0.1",
    description="Simple caching using decorators",
    author="James Kominick",
    author_email="james.kominick@gmail.com",
    url="https://github.com/jaemk/cashed",
    packages=find_packages(exclude=["examples"]),
)
