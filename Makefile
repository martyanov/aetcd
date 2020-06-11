.DEFAULT: help
.PHONY: help deps lint test testreport build upload outdated clean

help:
	@echo "Please use \`$(MAKE) <target>' where <target> is one of the following:"
	@echo "  help       - show help information"
	@echo "  lint       - inspect project source code for errors"
	@echo "  test       - run project tests"
	@echo "  testreport - run project tests and open HTML coverage report"
	@echo "  build      - build project packages"
	@echo "  upload     - upload built packages to package repository"
	@echo "  outdated   - list outdated project requirements"
	@echo "  clean      - clean up project environment and all the build artifacts"

deps:
	python3 -m pip install pip==20.1.1 setuptools==47.1.1 wheel==0.34.2
	python3 -m pip install -e .[dev,doc,test]

lint:
	python3 -m flake8 etcd3aio tests

test:
	python3 -m pytest

testreport:
	python3 -m pytest --cov-report=html
	xdg-open htmlcov/index.html

build:
	python3 setup.py sdist bdist_wheel

upload: build
	python3 -m twine upload dist/*

outdated:
	python3 -m pip list --outdated --format=columns

clean:
	rm -rf *.egg .eggs *.egg-info .pytest_cache .tox build dist htmlcov
