from setuptools import setup, find_packages # type: ignore

def read_requirements():
    with open('requirements.txt') as req:
        return [line.strip() for line in req.readlines() if line.strip() and not line.startswith('#')]

setup(
    name="yaml2dataclass",
    version="0.1.0",
    packages=find_packages(),
    install_requires=read_requirements(),
    author="BennoCrafter",
    description="Convert YAML to dataclass",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/bennocrafter/yaml2dataclass",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    entry_points={
        'console_scripts': [
            'yaml2dataclass=yaml2dataclass.cli:main',
        ],
    }
)
