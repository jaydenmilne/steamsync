from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="steamsync",
    version="0.2.5",
    author="Jayden Milne",
    author_email="jaydenmilne@users.noreply.github.com",
    description="Tool to automatically add games from the Epic Games Launcher to Steam",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jaydenmilne/steamsync",
    #packages=["*"],
    package_dir={"": "src"},
    classifiers=[
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Topic :: Games/Entertainment",
    ],
    install_requires=["vdf>=3,<4"],
    scripts=["src/steamsync.py"],
    python_requires=">=3.7",
)
