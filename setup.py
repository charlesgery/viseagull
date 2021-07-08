import setuptools

with open('LICENSE') as f:
    license = f.read()

setuptools.setup(
    name="viseagull",
    version="0.0.1",
    author="Charles Gery",
    author_email="charles.gery@gmail.com",
    description="A ludic visualization tool to explore your codebase",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.7",
    license=license,
    entry_points={
        'console_scripts': [
            'viseagull = viseagull.viseagull:main'
        ]
    }
)