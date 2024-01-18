import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# PyPi upload Command
# rm -r dist ; python setup.py sdist ; python -m twine upload dist/*

setuptools.setup(
    name="TikTokLive",
    packages=setuptools.find_packages(),
    version="5.0.8",
    license="MIT",
    description="TikTok Live Connection Client",
    author="Isaac Kogan",
    author_email="info@isaackogan.com",
    url="https://github.com/isaackogan/TikTokLive",
    long_description=long_description,
    long_description_content_type="text/markdown",
    download_url="https://github.com/isaackogan/TikTokLive/releases/tag/v5.0.8",
    keywords=["tiktok", "tiktok live", "python3", "api", "unofficial"],
    install_requires=[
        "httpx>=0.23.0",  # Make requests
        "protobuf3-to-dict>=0.1.5",  # Convert Protobuf to Dict
        "protobuf>=3.19.4",  # Decode Protobuf Messages
        "pyee>=9.0.4",  # Event Emitter
        "ffmpy>=0.3.0",  # Download streams
        "mashumaro>=3.5",  # JSON Deserialization
        "websockets>=10.4",  # Connecting to websocket server
        "websockets_proxy>=0.1.0",  # This module will enable you to use websockets package with proxies
        "async-timeout>=4.0.3"  # Fix: python_socks/async_/asyncio/_proxy.py import package
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ]
)
