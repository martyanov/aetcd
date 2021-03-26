.DEFAULT: help
.PHONY: help deps lint test testreport build upload outdated genproto clean

help:
	@echo "Please use \`$(MAKE) <target>' where <target> is one of the following:"
	@echo "  help        - show help information"
	@echo "  lint        - inspect project source code for errors"
	@echo "  test        - run project tests"
	@echo "  testcluster - run project tests on etcd cluster"
	@echo "  testreport  - run project tests and open HTML coverage report"
	@echo "  build       - build project packages"
	@echo "  upload      - upload built packages to package repository"
	@echo "  outdated    - list outdated project requirements"
	@echo "  genproto    - process .proto files and generate gRPC stubs"
	@echo "  clean       - clean up project environment and all the build artifacts"

deps:
	python3 -m pip install pip==21.0.1 setuptools==54.2.0 wheel==0.36.2
	python3 -m pip install -e .[dev,doc,test]

lint:
	python3 -m flake8 aetcd3 tests

test:
	python3 -m pytest

testcluster:
	python3 -m pifpaf -e PYTHON run etcd --cluster -- python3 -m pytest

testreport:
	python3 -m pytest --cov-report=html
	xdg-open htmlcov/index.html

build:
	python3 setup.py sdist bdist_wheel

upload: build
	python3 -m twine upload dist/*

outdated:
	python3 -m pip list --outdated --format=columns

genproto:
	sed -i -e '/gogoproto/d' aetcd3/proto/rpc.proto
	sed -i -e 's/etcd\/mvcc\/mvccpb\/kv.proto/kv.proto/g' aetcd3/proto/rpc.proto
	sed -i -e 's/etcd\/auth\/authpb\/auth.proto/auth.proto/g' aetcd3/proto/rpc.proto
	sed -i -e '/google\/api\/annotations.proto/d' aetcd3/proto/rpc.proto
	sed -i -e '/option (google.api.http)/,+3d' aetcd3/proto/rpc.proto
	python -m grpc_tools.protoc -Iaetcd3/proto \
        --python_out=aetcd3/etcdrpc/ \
        --python_grpc_out=aetcd3/etcdrpc/ \
        aetcd3/proto/rpc.proto aetcd3/proto/auth.proto aetcd3/proto/kv.proto
	sed -i -e 's/import auth_pb2/from . import auth_pb2/g' aetcd3/etcdrpc/rpc_pb2.py
	sed -i -e 's/import kv_pb2/from . import kv_pb2/g' aetcd3/etcdrpc/rpc_pb2.py
	sed -i -e 's/import kv_pb2/from . import kv_pb2/g' aetcd3/etcdrpc/rpc_grpc.py
	sed -i -e 's/import auth_pb2/from . import auth_pb2/g' aetcd3/etcdrpc/rpc_grpc.py
	sed -i -e 's/import rpc_pb2/from . import rpc_pb2/g' aetcd3/etcdrpc/rpc_grpc.py

clean:
	rm -rf *.egg .eggs *.egg-info .pytest_cache .tox build dist htmlcov
