from setuptools import setup
import codecs
import os
import re

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with codecs.open(os.path.join(here, *parts), "r") as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name="JSONSchema2PoPo2",
    version=find_version("jsonschema2popo", "__init__.py"),
    description="Converts a JSON Schema to a Plain Old Python Object class",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Build Tools",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
    url="https://github.com/mikedombo/JSONSchema2PoPo2",
    author="Michael Dombrowski",
    author_email="michael@mikedombrowski.com",
    keywords="python json-schema code-generator",
    license="MIT License",
    python_requires=">=3.4",
    install_requires=["Jinja2>=2.11.3", "networkx==2.4"],
    extras_require={"Format JS": ["jsbeautifier"], "Format Python": ["black"]},
    packages=["jsonschema2popo"],
    package_data={"jsonschema2popo": ["*/*"]},
    include_package_data=True,
    entry_points={
        "console_scripts": ["jsonschema2popo2=jsonschema2popo.jsonschema2popo:main"]
    },
)
