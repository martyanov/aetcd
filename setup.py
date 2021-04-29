import setuptools


def _get_long_description():
    with open('README.rst') as readme_file:
        return readme_file.read()


setuptools.setup(
    name='aetcd3',
    use_scm_version=True,
    description='Python asyncio-based client for etcd',
    long_description=_get_long_description(),
    long_description_content_type='text/x-rst',
    author='Andrey Martyanov',
    author_email='andrey@martyanov.com',
    url='https://github.com/martyanov/aetcd3',
    packages=[
        'aetcd3',
        'aetcd3.rpc',
    ],
    package_dir={
        'aetcd3': 'aetcd3',
        'aetcd3.rpc': 'aetcd3/rpc',
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
        'Documentation': 'https://aetcd3.readthedocs.io',
        'Code': 'https://github.com/martyanov/aetcd3',
        'Issues': 'https://github.com/martyanov/aetcd3/issues',
    },
    python_requires='>=3.8,<4.0',
    setup_requires=[
        'setuptools_scm==6.0.1',
    ],
    install_requires=[
        'aiofiles>=0.5,<0.7',
        'grpclib>=0.4.1,<0.5',
        'protobuf>=3,<4',
        'tenacity>=6,<7',
    ],
    extras_require={
        'dev': [
            'flake8-commas==2.0.0',
            'flake8-docstrings==1.6.0',
            'flake8-isort==4.0.0',
            'flake8-quotes==3.2.0',
            'flake8==3.9.1',
            'grpcio-tools==1.37.0',
            'pep8-naming==0.11.1',
            'twine==3.4.1',
        ],
        'doc': [
            'sphinx==3.5.4',
            'sphinx_rtd_theme==0.5.2',
        ],
        'test': [
            'pifpaf==3.1.5',
            'pytest-asyncio==0.15.1',
            'pytest-cov==2.11.1',
            'pytest==6.2.3',
        ],
    },
)
