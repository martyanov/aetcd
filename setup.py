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
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
    ],
    project_urls={
        'Documentation': 'https://aetcd.readthedocs.io',
        'Code': 'https://github.com/martyanov/aetcd',
        'Issues': 'https://github.com/martyanov/aetcd/issues',
    },
    python_requires='>=3.10,<4.0',
    setup_requires=[
        'setuptools_scm==10.0.5',
    ],
    install_requires=[
        'grpcio>1.66.0,<2',
        'protobuf>4,<7',
    ],
    extras_require={
        'dev': [
            'flake8-commas==4.0.0',
            'flake8-docstrings==1.7.0',
            'flake8-isort==7.0.0',
            'flake8-quotes==3.4.0',
            'flake8==7.3.0',
            'grpcio-tools==1.66.2',
            'pep8-naming==0.15.1',
            'twine==6.2.0',
        ],
        'doc': [
            'sphinx==8.1.3',
            'sphinx_rtd_theme==3.1.0',
        ],
        'test': [
            'pytest-asyncio==1.3.0',
            'pytest-cov==7.1.0',
            'pytest-mock==3.15.1',
            'pytest==9.0.3',
        ],
    },
)
