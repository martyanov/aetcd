import setuptools


def _get_long_description():
    with open('README.rst') as readme_file:
        return readme_file.read()


setuptools.setup(
    name='aetcd',
    use_scm_version=True,
    description='Python asyncio-based client for etcd',
    long_description=_get_long_description(),
    long_description_content_type='text/x-rst',
    author='Andrey Martyanov',
    author_email='andrey@martyanov.com',
    url='https://github.com/martyanov/aetcd',
    packages=[
        'aetcd',
        'aetcd.rpc',
    ],
    package_dir={
        'aetcd': 'aetcd',
        'aetcd.rpc': 'aetcd/rpc',
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
        'Documentation': 'https://aetcd.readthedocs.io',
        'Code': 'https://github.com/martyanov/aetcd',
        'Issues': 'https://github.com/martyanov/aetcd/issues',
    },
    python_requires='>=3.8,<4.0',
    setup_requires=[
        'setuptools_scm==6.0.1',
    ],
    install_requires=[
        'aiofiles>=0.5,<0.9',
        'grpclib>=0.4.1,<0.5',
        'protobuf>=3,<4',
        'tenacity>=6,<9',
    ],
    extras_require={
        'dev': [
            'flake8-commas==2.1.0',
            'flake8-docstrings==1.6.0',
            'flake8-isort==4.1.1',
            'flake8-quotes==3.3.1',
            'flake8==4.0.1',
            'grpcio-tools==1.43.0',
            'pep8-naming==0.12.1',
            'twine==3.7.1',
        ],
        'doc': [
            'sphinx==4.3.2',
            'sphinx_rtd_theme==1.0.0',
        ],
        'test': [
            'pifpaf==3.1.5',
            'pytest-asyncio==0.16.0',
            'pytest-cov==3.0.0',
            'pytest==6.2.5',
        ],
    },
)
