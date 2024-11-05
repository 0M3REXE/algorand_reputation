from setuptools import setup, find_packages

setup(
    name='algorand_reputation',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'algosdk',
    ],
    description='A package to evaluate Algorand account reputation scores.',
    author='Omer Abdullah',
    author_email='omerhyd8080@gmail.com',
    url='https://github.com/yourusername/algorand_reputation',  # Update with your repo
)
