.DEFAULT: help
.PHONY: help bootstrap lint test testreport build upload outdated genproto clean

VENV=.venv
PYTHON_BIN?=python3
PYTHON=$(VENV)/bin/$(PYTHON_BIN)

help:
	@echo "Please use \`$(MAKE) <target>' where <target> is one of the following:"
	@echo "  help        - show help information"
	@echo "  bootstrap  - setup packaging dependencies and initialize venv"
	@echo "  lint        - inspect project source code for errors"
	@echo "  test        - run project tests"
	@echo "  testcluster - run project tests on etcd cluster"
	@echo "  testreport  - run project tests and open HTML coverage report"
	@echo "  build       - build project packages"
	@echo "  upload      - upload built packages to package repository"
	@echo "  outdated    - list outdated project requirements"
	@echo "  genproto    - process .proto files and generate gRPC stubs"
	@echo "  clean       - clean up project environment and all the build artifacts"

bootstrap: $(VENV)/bin/activate
$(VENV)/bin/activate:
	$(PYTHON_BIN) -m venv $(VENV)
	$(PYTHON) -m pip install pip==21.1 setuptools==56.0.0 wheel==0.36.2
	$(PYTHON) -m pip install -e .[dev,doc,test]

lint: bootstrap
	$(PYTHON) -m flake8 aetcd3 tests

test: bootstrap
	$(PYTHON) -m pytest

testcluster: bootstrap
	$(PYTHON) -m pifpaf -e PYTHON run etcd --cluster -- $(PYTHON) -m pytest

testreport: bootstrap
	$(PYTHON) -m pytest --cov-report=html
	xdg-open htmlcov/index.html

build: bootstrap
	$(PYTHON) setup.py sdist bdist_wheel

upload: build
	$(PYTHON) -m twine upload dist/*

outdated: bootstrap
	$(PYTHON) -m pip list --outdated --format=columns

genproto: bootstrap
	$(PYTHON) -m grpc_tools.protoc -Iproto \
		--plugin=protoc-gen-python_grpc=$(VENV)/bin/protoc-gen-python_grpc \
		--plugin=protoc-gen-grpclib_python=$(VENV)/bin/protoc-gen-grpclib_python \
		--python_out=aetcd3/rpc/ \
		--python_grpc_out=aetcd3/rpc/ \
		proto/rpc.proto proto/auth.proto proto/kv.proto
	sed -i -e 's/import auth_pb2/from . import auth_pb2/g' aetcd3/rpc/rpc_pb2.py
	sed -i -e 's/import kv_pb2/from . import kv_pb2/g' aetcd3/rpc/rpc_pb2.py
	sed -i -e 's/import kv_pb2/from . import kv_pb2/g' aetcd3/rpc/rpc_grpc.py
	sed -i -e 's/import auth_pb2/from . import auth_pb2/g' aetcd3/rpc/rpc_grpc.py
	sed -i -e 's/import rpc_pb2/from . import rpc_pb2/g' aetcd3/rpc/rpc_grpc.py

clean:
	rm -rf *.egg .eggs *.egg-info .pytest_cache .venv build coverage.xml dist htmlcov
