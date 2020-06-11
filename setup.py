import setuptools


def _get_long_description():
    with open('README.md') as readme_file:
        return readme_file.read()


setuptools.setup(
    name='aetcd3',
    version='0.1.0a1',
    description='Python asyncio based client for the etcd API v3',
    long_description=_get_long_description(),
    long_description_content_type='text/markdown',
    author='Andrey Martyanov',
    author_email='andrey@martyanov.com',
    url='https://github.com/martyanov/aetcd3',
    packages=[
        'etcd3aio',
        'etcd3aio.etcdrpc',
    ],
    package_dir={
        'etcd3aio': 'etcd3aio',
        'etcd3aio.etcdrpc': 'etcd3aio/etcdrpc',
    },
    include_package_data=True,
    license='Apache Software License 2.0',
    zip_safe=False,
    keywords='etcd3',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
    ],
    project_urls={
        'Bug Reports': 'https://github.com/martyanov/aetcd3/issues',
        'Repository': 'https://github.com/martyanov/aetcd3',
    },
    python_requires='>=3.7,<4.0',
    install_requires=[
        'aiofiles>=0.5,<0.6',
        'grpclib>=0.3,<0.4',
        'protobuf>=3,<4',
        'tenacity>=5,<6',
    ],
    extras_require={
        'dev': [
            'PyYAML==5.3.1',
            'coverage==5.1',
            'flake8-docstrings==1.3.0',
            'flake8-import-order==0.18.1',
            'flake8==3.8.3',
            'grpcio-tools==1.29.0',
            'twine==3.1.1',
        ],
        'doc': [
            'Sphinx==3.1.0',
        ],
        'test': [
            'pifpaf==2.5.0',
            'pytest-asyncio==0.10.0',
            'pytest-cov==2.9.0',
            'pytest==5.4.3',
            'tox==3.15.2',
        ],
    },
)
