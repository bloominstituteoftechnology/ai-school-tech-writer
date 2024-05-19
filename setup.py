from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='technical-writer',
    version='0.0.0-alpha',
    packages=find_packages(),
    install_requires=requirements,
)
