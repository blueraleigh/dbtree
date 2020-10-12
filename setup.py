from setuptools import setup

setup(
    name="dbtree",
    version="1.0",
    packages=["dbtree"],
    include_package_data=True,
    install_requires=["click"],
    entry_points="""
        [console_scripts]
        dbtree=dbtree.cli:cli
    """,
)
