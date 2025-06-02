from setuptools import setup, find_packages

setup(
    name="projektseminar_docker",
    version="1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        # Ihre Abhängigkeiten hier
        'flask',
        'pandas',
    ],
)