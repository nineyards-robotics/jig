from setuptools import find_packages, setup

package_name = "jig_cli"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["tests"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    python_requires=">=3.10",
    install_requires=["pyyaml"],
    zip_safe=True,
    entry_points={
        "console_scripts": [
            "jig = jig_cli.cli:main",
        ],
    },
)
