from setuptools import find_packages
from setuptools import setup

__version__ = '0.47.0'


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
            '*.yaml',
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
        "boto3>=1.15.1",
        "botocore>=1.18.1",
        "dnspython>=1.15.0",
        "neo4j>=1.7.6,<4.0.0",
        "neobolt>=1.7.0,<4.0.0",
        "policyuniverse>=1.1.0.0",
        "google-api-python-client>=1.7.8",
        "oauth2client>=4.1.3",
        "marshmallow>=3.0.0rc7",
        "okta<1.0.0",
        "pyyaml>=5.3.1",
        "requests>=2.22.0",
        "statsd",
        "packaging",
        "cryptography<3.4,>=3.2",
        "python-digitalocean>=1.16.0",
        "adal>=1.2.4",
        "azure-cli-core>=2.12.0",
        "azure-mgmt-compute>=5.0.0",
        "azure-mgmt-resource>=10.2.0",
        "azure-mgmt-cosmosdb>=6.0.0",
        "msrestazure >= 0.6.4",
        "azure-mgmt-storage>=16.0.0",
        "azure-mgmt-sql<=1.0.0",
        "azure-identity>=1.5.0",
        "kubernetes>=18.20.0",
        "pdpyras>=4.3.0",
    ],
    extras_require={
        ':python_version<"3.7"': [
            "importlib-resources",
        ],
    },
    entry_points={
        'console_scripts': [
            'cartography = cartography.cli:main',
            'cartography-detectdrift = cartography.driftdetect.cli:main',
        ],
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
