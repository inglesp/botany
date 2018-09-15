import os
import re

from setuptools import find_packages, setup


def read(*parts):
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, *parts)) as f:
        return f.read()


VERSION = re.search(
    '^__version__ = "(.*)"$',
    read("src", "botany_connectfour", "__init__.py"),
    re.MULTILINE,
).group(1)

if __name__ == "__main__":
    setup(
        name="botany-connectfour",
        version=VERSION,
        description="Botany connectfour",
        packages=find_packages(where="src"),
        package_dir={"": "src"},
        install_requires=["attrs"],
        url="http://github.com/inglesp/botany",
        author="Peter Inglesby",
        author_email="peter.inglesby@gmail.com",
        license="License :: OSI Approved :: MIT License",
    )
