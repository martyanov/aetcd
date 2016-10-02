============
python-etcd3
============


.. image:: https://img.shields.io/pypi/v/etcd3.svg
        :target: https://pypi.python.org/pypi/etcd3

.. image:: https://img.shields.io/travis/kragniz/python-etcd3.svg
        :target: https://travis-ci.org/kragniz/python-etcd3

.. image:: https://readthedocs.org/projects/python-etcd3/badge/?version=latest
        :target: https://python-etcd3.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/kragniz/python-etcd3/shield.svg
     :target: https://pyup.io/repos/github/kragniz/python-etcd3/
     :alt: Updates


Python client for the etcd3 API

* Free software: Apache Software License 2.0
* Documentation: https://python-etcd3.readthedocs.io.

This project is developed using Readme Driven Development, the most hip
development methodology.

Fictitious example of api usage:

.. code-block:: python

    import etcd3

    etcd = etcd3.client()
    # or
    etcd = etcd3.client(username='root',
                        password='hunter2',
                        host='127.0.0.1',
                        port=1234)

    etcd.get('foo')
    etcd.set('bar', 'doot')
    etcd.delete('bar')

    # locks
    lock = etcd.lock('thing')
    # do something
    lock.release()

    with etcd.lock('doot-machine') as lock:
        # do something

    # watching
    for event in etcd.watch('some-key'):
        print(event)

    # admin stuff
    member_id = etcd.add_member('newMember', peer_urls=['https://127.0.0.1:12345'])
    etcd.update_member(member_id, peer_urls=['https://127.0.0.1:12345'])
    etcd.remove_member(member_id)
    for member in etcd.members:
        print(member.id, member.name, member.peer_addresses)
        member.remove()


Generating protobuf stuff
-------------------------

I ran::

    $ protoc --python_out=. -I/home/kragniz/git/protobuf -I/home/kragniz/git/googleapis -I. -I.. /home/kragniz/git/protobuf/gogoproto/gogo.proto ./etcdserver/etcdserverpb/rpc.proto

from inside the etcd repo and it did stuff. Not sure if it did the correct
stuff, but it output some python.