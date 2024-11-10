from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="doctalk",
    version="0.1.0",
    author="Wenfeng Liu",
    author_email="wenfeng.liu@gmail.com",
    description="An offline document-to-speech converter using Edge TTS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kurlez/doctalk",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
        "edge-tts>=6.1.7",
        "markdown>=3.4.1",
        "beautifulsoup4>=4.12.0",
        "mutagen>=1.46.0",
        "ebooklib>=0.18.0",
        "html2text>=2020.1.16",
    ],
    entry_points={
        "console_scripts": [
            "doctalk=doctalk.doctalk:main",
        ],
    },
)