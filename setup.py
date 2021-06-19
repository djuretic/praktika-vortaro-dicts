from setuptools import setup, find_packages

setup(
    name="eo_dicts",
    version="0.1",
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    install_requires=[
        "Click",
    ],
    entry_points="""
        [console_scripts]
        process_revo=eo_dicts.process_revo:main
    """,
)
