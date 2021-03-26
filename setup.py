import setuptools


def _get_long_description():
    with open('README.rst') as readme_file:
        return readme_file.read()


setuptools.setup(
    name='aetcd3',
    use_scm_version=True,
    description='Python asyncio based client for the etcd API v3',
    long_description=_get_long_description(),
    long_description_content_type='text/x-rst',
    author='Andrey Martyanov',
    author_email='andrey@martyanov.com',
    url='https://github.com/martyanov/aetcd3',
    packages=[
        'aetcd3',
        'aetcd3.etcdrpc',
    ],
    package_dir={
        'aetcd3': 'aetcd3',
        'aetcd3.etcdrpc': 'aetcd3/etcdrpc',
    },
    include_package_data=True,
    license='Apache Software License 2.0',
    zip_safe=False,
    keywords='etcd3',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    project_urls={
        'Bug Reports': 'https://github.com/martyanov/aetcd3/issues',
        'Repository': 'https://github.com/martyanov/aetcd3',
    },
    python_requires='>=3.7,<4.0',
    setup_requires=[
        'setuptools_scm==4.1.2',
    ],
    install_requires=[
        'aiofiles>=0.5,<0.6',
        'grpclib>=0.4.1,<0.5',
        'protobuf>=3,<4',
        'tenacity>=6,<7',
    ],
    extras_require={
        'dev': [
            'flake8-commas==2.0.0',
            'flake8-docstrings==1.5.0',
            'flake8-import-order==0.18.1',
            'flake8==3.8.3',
            'grpcio-tools==1.29.0',
            'pep8-naming==0.10.0',
            'twine==3.1.1',
        ],
        'doc': [
            'sphinx==3.1.0',
            'sphinx_rtd_theme==0.5.0',
        ],
        'test': [
            'pifpaf==2.5.0',
            'pytest-asyncio==0.12.0',
            'pytest-cov==2.9.0',
            'pytest==5.4.3',
            'tox==3.15.2',
        ],
    },
)
