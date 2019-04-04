from setuptools import setup, find_packages

__version__ = '0.2.3rc3'


setup(
    name='cartography',
    version=__version__,
    description='Explore assets and their relationships across your technical infrastructure.',
    url='https://www.github.com/lyft/cartography',
    maintainer='Lyft',
    maintainer_email='security@lyft.com',
    license='apache2',
    packages=find_packages(exclude=['tests*']),
    package_data={
        'cartography.data': [
            '*.cypher',
        ],
        'cartography.data.jobs.analysis': [
            '*.json',
        ],
        'cartography.data.jobs.cleanup': [
            '*.json',
        ],
    },
    dependency_links=[],
    install_requires=[
        "boto3>=1.7.0",
        "botocore>=1.12.0",
        "dnspython>=1.15.0",
        "neo4j-driver>=1.7.0",
        "neobolt>=1.7.0",
        "policyuniverse>=1.1.0.0",
        "python-dateutil>=2.7.0",
    ],
    extras_require={
        ':python_version<"3.7"': [
            "importlib-resources",
        ],
    },
    entry_points={
        'console_scripts': [
            'cartography = cartography.cli:main',
        ]
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Topic :: Security',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
