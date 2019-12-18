from setuptools import setup, find_packages

__version__ = '0.2.4'

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
    package_data={'': ['LICENSE', 'README.md']},
    package_dir={'locust_influx': 'locust_influx'},
    include_package_data=True,
    python_requires='>=3.6',
    install_requires=[
        'locustio>=0.12.2',
        'influxdb>=5.2.2',
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Plugins",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    project_urls={
        'Documentation': 'https://locust_influx.github.io',
        'Source': 'https://github.com/lucrib/locust_influx',
    },
)
