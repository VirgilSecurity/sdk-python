from setuptools import setup, find_packages

setup(
    name="virgil-sdk",
    version="5.0.1",
    packages=find_packages(),
    install_requires=[
        'virgil-crypto>3',
    ],
    package_data={"virgil_sdk": [
        "tests/*",
        "tests/data/*.json"
    ]},
    author="Virgil Security",
    author_email="support@virgilsecurity.com",
    url="https://virgilsecurity.com/",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Security :: Cryptography",
        ],
    license="BSD",
    description="""
    Virgil Security provides a set of APIs for adding security to any application. In a few simple steps you can encrypt communication, securely store data, provide passwordless login, and ensure data integrity.
    Virgil SDK allows developers to get up and running with Virgil API quickly and add full end-to-end (E2EE) security to their existing digital solutions to become HIPAA and GDPR compliant and more.
    """,
    long_description="""
    Virgil Security provides a set of APIs for adding security to any application. In a few simple steps you can encrypt communication, securely store data, provide passwordless login, and ensure data integrity.
    Virgil SDK allows developers to get up and running with Virgil API quickly and add full end-to-end (E2EE) security to their existing digital solutions to become HIPAA and GDPR compliant and more.
    """
)
