from setuptools import setup, find_packages

from __version__ import __version__

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='locust_influx',
    version=__version__,
    url='https://github.com/lucrib/locust_influx',
    license='Apache-2.0',
    author='Lucas Ribeiro',
    author_email='lucasribeiro1990@gmail.com',
    description='Report locust metrics to influxdb.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    python_requires='>=3.6',
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Plugins",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
    ],
)
