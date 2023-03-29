""" Setup
"""
from os import path

from setuptools import setup

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

__version__ = "0.0.1"

setup(
    name="chimerapy_orchestrator",
    version=__version__,
    description="Reusable Nodes and Orchestration Scheme for ChimeraPy with JSON configuration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/oele-isis-vanderbilt/ChimeraPyOrchestrator",
    author="Umesh Timalsina",
    author_email="umesh.timalsina@vanderbilt.edu",
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GPL-3.0",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Distributed Computing",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="distributed computing multimodal data analytics",
    packages=["chimerapy_orchestrator"],
    include_package_data=True,
    install_requires=["chimerapy", "pydantic"],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "cp-orchestrator = chimerapy_orchestrator.cli.__main__:run"
        ]
    },
)
