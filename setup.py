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
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    project_urls={
        'Bug Reports': 'https://github.com/martyanov/aetcd3/issues',
        'Repository': 'https://github.com/martyanov/aetcd3',
    },
    python_requires='>=3.8,<4.0',
    setup_requires=[
        'setuptools_scm==6.0.1',
    ],
    install_requires=[
        'aiofiles>=0.6',
        'grpclib>=0.4.1,<0.5',
        'protobuf>=3,<4',
        'tenacity>=6,<7',
    ],
    extras_require={
        'dev': [
            'flake8-commas==2.0.0',
            'flake8-docstrings==1.6.0',
            'flake8-import-order==0.18.1',
            'flake8==3.9.0',
            'grpcio-tools==1.36.1',
            'pep8-naming==0.11.1',
            'twine==3.4.1',
        ],
        'doc': [
            'sphinx==3.1.0',
            'sphinx_rtd_theme==0.5.0',
        ],
        'test': [
            'pifpaf==3.1.5',
            'pytest-asyncio==0.14.0',
            'pytest-cov==2.11.1',
            'pytest==6.2.2',
            'tox==3.15.2',
        ],
    },
)
