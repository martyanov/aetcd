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
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    project_urls={
        'Documentation': 'https://aetcd.readthedocs.io',
        'Code': 'https://github.com/martyanov/aetcd',
        'Issues': 'https://github.com/martyanov/aetcd/issues',
    },
    python_requires='>=3.8,<4.0',
    setup_requires=[
        'setuptools_scm==6.3.2',
    ],
    install_requires=[
        'grpcio>1.51,<2',
        'protobuf>4,<5',
    ],
    extras_require={
        'dev': [
            'flake8-commas==2.1.0',
            'flake8-docstrings==1.7.0',
            'flake8-isort==6.0.0',
            'flake8-quotes==3.3.2',
            'flake8==6.0.0',
            'grpcio-tools==1.51.1',
            'pep8-naming==0.13.3',
            'twine==4.0.2',
        ],
        'doc': [
            'sphinx==6.1.3',
            'sphinx_rtd_theme==1.2.0',
        ],
        'test': [
            'pytest-asyncio==0.20.3',
            'pytest-cov==4.0.0',
            'pytest-mock==3.10.0',
            'pytest==7.2.1',
        ],
    },
)
