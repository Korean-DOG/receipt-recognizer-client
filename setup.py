from setuptools import setup, find_packages

with open("receipt_recognizer/version.py", "r", encoding="utf-8") as f:
    for line in f:
        if line.startswith("__version__"):
            __version__ = line.split("=")[1].strip().strip('"').strip("'")
            break
    else:
        __version__ = "0.1.0"

setup(
    name="receipt-recognizer-client",
    version=__version__,
    author="Korean-DOG",
    author_email="phghost@mail.ru",
    url="https://github.com/Korean-DOG/receipt-recognizer-client",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.11",
    install_requires=[
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "receipt-recognizer=receipt_recognizer.cli:main",
        ],
    },
)
