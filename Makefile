.DEFAULT: help
.PHONY: bootstrap build clean help genproto lint outdated test testcluster testreport upload

VENV=.venv
PYTHON_BIN?=python3
PYTHON=$(VENV)/bin/$(PYTHON_BIN)

help:
	@echo "Please use \`$(MAKE) <target>' where <target> is one of the following:"
	@echo "  help        - show help information"
	@echo "  bootstrap  - setup packaging dependencies and initialize venv"
	@echo "  build       - build project packages"
	@echo "  genproto    - process .proto files and generate gRPC stubs"
	@echo "  lint        - inspect project source code for errors"
	@echo "  outdated    - list outdated project requirements"
	@echo "  test        - run project tests"
	@echo "  testcluster - run project tests on etcd cluster"
	@echo "  testreport  - run project tests and open HTML coverage report"
	@echo "  upload      - upload built packages to package repository"
	@echo "  clean       - clean up project environment and all the build artifacts"

bootstrap: $(VENV)/bin/activate
$(VENV)/bin/activate:
	$(PYTHON_BIN) -m venv $(VENV)
	$(PYTHON) -m pip install pip==23.0 setuptools==67.3.2 wheel==0.38.4
	$(PYTHON) -m pip install -e .[dev,doc,test]
	$(PYTHON) -m pip install 'pifpaf @ git+https://github.com/jd/pifpaf.git@80cc13bd7e4b0cb286d15659c9fe7958e8600cd9#egg=aetcd'

build: bootstrap
	$(PYTHON) setup.py sdist bdist_wheel

genproto: bootstrap
	$(PYTHON) -m grpc_tools.protoc -Iproto \
		--python_out=aetcd/rpc/ \
		--grpc_python_out=aetcd/rpc/ \
		proto/rpc.proto proto/auth.proto proto/kv.proto
	sed -i -e 's/import auth_pb2/from . import auth_pb2/g' aetcd/rpc/rpc_pb2.py
	sed -i -e 's/import kv_pb2/from . import kv_pb2/g' aetcd/rpc/rpc_pb2.py
	sed -i -e 's/import rpc_pb2/from . import rpc_pb2/g' aetcd/rpc/rpc_pb2_grpc.py

lint: bootstrap
	$(PYTHON) -m flake8 aetcd tests

test: bootstrap
	$(PYTHON) -m pytest

testcluster: bootstrap
	$(PYTHON) -m pifpaf -e TEST --debug run etcd --cluster -- $(PYTHON) -m pytest --with-cluster --cov-report=xml

testreport: bootstrap
	$(PYTHON) -m pytest --cov-report=html
	xdg-open htmlcov/index.html

upload: build
	$(PYTHON) -m twine upload dist/*

outdated: bootstrap
	$(PYTHON) -m pip list --outdated --format=columns

clean:
	rm -rf *.egg-info *.egg .eggs .pytest_cache build coverage.xml dist htmlcov $(VENV)
