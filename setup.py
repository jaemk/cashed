from setuptools import setup, find_packages

setup(
    name="cashed",
    version="0.1.2",
    description="Simple caching using decorators",
    author="James Kominick",
    author_email="james.kominick@gmail.com",
    license="MIT",
    url="https://github.com/jaemk/cashed",
    packages=find_packages(exclude=["examples"]),
)
