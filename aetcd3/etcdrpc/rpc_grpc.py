# Generated by the Protocol Buffers compiler. DO NOT EDIT!
# source: rpc.proto
# plugin: grpclib.plugin.main
import abc
import typing

import grpclib.const
import grpclib.client
if typing.TYPE_CHECKING:
    import grpclib.server

from . import auth_pb2
from . import kv_pb2
from . import rpc_pb2


class KVBase(abc.ABC):

    @abc.abstractmethod
    async def Range(self, stream: 'grpclib.server.Stream[rpc_pb2.RangeRequest, rpc_pb2.RangeResponse]') -> None:
        pass

    @abc.abstractmethod
    async def Put(self, stream: 'grpclib.server.Stream[rpc_pb2.PutRequest, rpc_pb2.PutResponse]') -> None:
        pass

    @abc.abstractmethod
    async def DeleteRange(self, stream: 'grpclib.server.Stream[rpc_pb2.DeleteRangeRequest, rpc_pb2.DeleteRangeResponse]') -> None:
        pass

    @abc.abstractmethod
    async def Txn(self, stream: 'grpclib.server.Stream[rpc_pb2.TxnRequest, rpc_pb2.TxnResponse]') -> None:
        pass

    @abc.abstractmethod
    async def Compact(self, stream: 'grpclib.server.Stream[rpc_pb2.CompactionRequest, rpc_pb2.CompactionResponse]') -> None:
        pass

    def __mapping__(self) -> typing.Dict[str, grpclib.const.Handler]:
        return {
            '/etcdserverpb.KV/Range': grpclib.const.Handler(
                self.Range,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.RangeRequest,
                rpc_pb2.RangeResponse,
            ),
            '/etcdserverpb.KV/Put': grpclib.const.Handler(
                self.Put,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.PutRequest,
                rpc_pb2.PutResponse,
            ),
            '/etcdserverpb.KV/DeleteRange': grpclib.const.Handler(
                self.DeleteRange,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.DeleteRangeRequest,
                rpc_pb2.DeleteRangeResponse,
            ),
            '/etcdserverpb.KV/Txn': grpclib.const.Handler(
                self.Txn,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.TxnRequest,
                rpc_pb2.TxnResponse,
            ),
            '/etcdserverpb.KV/Compact': grpclib.const.Handler(
                self.Compact,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.CompactionRequest,
                rpc_pb2.CompactionResponse,
            ),
        }


class KVStub:

    def __init__(self, channel: grpclib.client.Channel) -> None:
        self.Range = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.KV/Range',
            rpc_pb2.RangeRequest,
            rpc_pb2.RangeResponse,
        )
        self.Put = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.KV/Put',
            rpc_pb2.PutRequest,
            rpc_pb2.PutResponse,
        )
        self.DeleteRange = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.KV/DeleteRange',
            rpc_pb2.DeleteRangeRequest,
            rpc_pb2.DeleteRangeResponse,
        )
        self.Txn = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.KV/Txn',
            rpc_pb2.TxnRequest,
            rpc_pb2.TxnResponse,
        )
        self.Compact = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.KV/Compact',
            rpc_pb2.CompactionRequest,
            rpc_pb2.CompactionResponse,
        )


class WatchBase(abc.ABC):

    @abc.abstractmethod
    async def Watch(self, stream: 'grpclib.server.Stream[rpc_pb2.WatchRequest, rpc_pb2.WatchResponse]') -> None:
        pass

    def __mapping__(self) -> typing.Dict[str, grpclib.const.Handler]:
        return {
            '/etcdserverpb.Watch/Watch': grpclib.const.Handler(
                self.Watch,
                grpclib.const.Cardinality.STREAM_STREAM,
                rpc_pb2.WatchRequest,
                rpc_pb2.WatchResponse,
            ),
        }


class WatchStub:

    def __init__(self, channel: grpclib.client.Channel) -> None:
        self.Watch = grpclib.client.StreamStreamMethod(
            channel,
            '/etcdserverpb.Watch/Watch',
            rpc_pb2.WatchRequest,
            rpc_pb2.WatchResponse,
        )


class LeaseBase(abc.ABC):

    @abc.abstractmethod
    async def LeaseGrant(self, stream: 'grpclib.server.Stream[rpc_pb2.LeaseGrantRequest, rpc_pb2.LeaseGrantResponse]') -> None:
        pass

    @abc.abstractmethod
    async def LeaseRevoke(self, stream: 'grpclib.server.Stream[rpc_pb2.LeaseRevokeRequest, rpc_pb2.LeaseRevokeResponse]') -> None:
        pass

    @abc.abstractmethod
    async def LeaseKeepAlive(self, stream: 'grpclib.server.Stream[rpc_pb2.LeaseKeepAliveRequest, rpc_pb2.LeaseKeepAliveResponse]') -> None:
        pass

    @abc.abstractmethod
    async def LeaseTimeToLive(self, stream: 'grpclib.server.Stream[rpc_pb2.LeaseTimeToLiveRequest, rpc_pb2.LeaseTimeToLiveResponse]') -> None:
        pass

    @abc.abstractmethod
    async def LeaseLeases(self, stream: 'grpclib.server.Stream[rpc_pb2.LeaseLeasesRequest, rpc_pb2.LeaseLeasesResponse]') -> None:
        pass

    def __mapping__(self) -> typing.Dict[str, grpclib.const.Handler]:
        return {
            '/etcdserverpb.Lease/LeaseGrant': grpclib.const.Handler(
                self.LeaseGrant,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.LeaseGrantRequest,
                rpc_pb2.LeaseGrantResponse,
            ),
            '/etcdserverpb.Lease/LeaseRevoke': grpclib.const.Handler(
                self.LeaseRevoke,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.LeaseRevokeRequest,
                rpc_pb2.LeaseRevokeResponse,
            ),
            '/etcdserverpb.Lease/LeaseKeepAlive': grpclib.const.Handler(
                self.LeaseKeepAlive,
                grpclib.const.Cardinality.STREAM_STREAM,
                rpc_pb2.LeaseKeepAliveRequest,
                rpc_pb2.LeaseKeepAliveResponse,
            ),
            '/etcdserverpb.Lease/LeaseTimeToLive': grpclib.const.Handler(
                self.LeaseTimeToLive,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.LeaseTimeToLiveRequest,
                rpc_pb2.LeaseTimeToLiveResponse,
            ),
            '/etcdserverpb.Lease/LeaseLeases': grpclib.const.Handler(
                self.LeaseLeases,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.LeaseLeasesRequest,
                rpc_pb2.LeaseLeasesResponse,
            ),
        }


class LeaseStub:

    def __init__(self, channel: grpclib.client.Channel) -> None:
        self.LeaseGrant = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Lease/LeaseGrant',
            rpc_pb2.LeaseGrantRequest,
            rpc_pb2.LeaseGrantResponse,
        )
        self.LeaseRevoke = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Lease/LeaseRevoke',
            rpc_pb2.LeaseRevokeRequest,
            rpc_pb2.LeaseRevokeResponse,
        )
        self.LeaseKeepAlive = grpclib.client.StreamStreamMethod(
            channel,
            '/etcdserverpb.Lease/LeaseKeepAlive',
            rpc_pb2.LeaseKeepAliveRequest,
            rpc_pb2.LeaseKeepAliveResponse,
        )
        self.LeaseTimeToLive = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Lease/LeaseTimeToLive',
            rpc_pb2.LeaseTimeToLiveRequest,
            rpc_pb2.LeaseTimeToLiveResponse,
        )
        self.LeaseLeases = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Lease/LeaseLeases',
            rpc_pb2.LeaseLeasesRequest,
            rpc_pb2.LeaseLeasesResponse,
        )


class ClusterBase(abc.ABC):

    @abc.abstractmethod
    async def MemberAdd(self, stream: 'grpclib.server.Stream[rpc_pb2.MemberAddRequest, rpc_pb2.MemberAddResponse]') -> None:
        pass

    @abc.abstractmethod
    async def MemberRemove(self, stream: 'grpclib.server.Stream[rpc_pb2.MemberRemoveRequest, rpc_pb2.MemberRemoveResponse]') -> None:
        pass

    @abc.abstractmethod
    async def MemberUpdate(self, stream: 'grpclib.server.Stream[rpc_pb2.MemberUpdateRequest, rpc_pb2.MemberUpdateResponse]') -> None:
        pass

    @abc.abstractmethod
    async def MemberList(self, stream: 'grpclib.server.Stream[rpc_pb2.MemberListRequest, rpc_pb2.MemberListResponse]') -> None:
        pass

    @abc.abstractmethod
    async def MemberPromote(self, stream: 'grpclib.server.Stream[rpc_pb2.MemberPromoteRequest, rpc_pb2.MemberPromoteResponse]') -> None:
        pass

    def __mapping__(self) -> typing.Dict[str, grpclib.const.Handler]:
        return {
            '/etcdserverpb.Cluster/MemberAdd': grpclib.const.Handler(
                self.MemberAdd,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.MemberAddRequest,
                rpc_pb2.MemberAddResponse,
            ),
            '/etcdserverpb.Cluster/MemberRemove': grpclib.const.Handler(
                self.MemberRemove,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.MemberRemoveRequest,
                rpc_pb2.MemberRemoveResponse,
            ),
            '/etcdserverpb.Cluster/MemberUpdate': grpclib.const.Handler(
                self.MemberUpdate,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.MemberUpdateRequest,
                rpc_pb2.MemberUpdateResponse,
            ),
            '/etcdserverpb.Cluster/MemberList': grpclib.const.Handler(
                self.MemberList,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.MemberListRequest,
                rpc_pb2.MemberListResponse,
            ),
            '/etcdserverpb.Cluster/MemberPromote': grpclib.const.Handler(
                self.MemberPromote,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.MemberPromoteRequest,
                rpc_pb2.MemberPromoteResponse,
            ),
        }


class ClusterStub:

    def __init__(self, channel: grpclib.client.Channel) -> None:
        self.MemberAdd = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Cluster/MemberAdd',
            rpc_pb2.MemberAddRequest,
            rpc_pb2.MemberAddResponse,
        )
        self.MemberRemove = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Cluster/MemberRemove',
            rpc_pb2.MemberRemoveRequest,
            rpc_pb2.MemberRemoveResponse,
        )
        self.MemberUpdate = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Cluster/MemberUpdate',
            rpc_pb2.MemberUpdateRequest,
            rpc_pb2.MemberUpdateResponse,
        )
        self.MemberList = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Cluster/MemberList',
            rpc_pb2.MemberListRequest,
            rpc_pb2.MemberListResponse,
        )
        self.MemberPromote = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Cluster/MemberPromote',
            rpc_pb2.MemberPromoteRequest,
            rpc_pb2.MemberPromoteResponse,
        )


class MaintenanceBase(abc.ABC):

    @abc.abstractmethod
    async def Alarm(self, stream: 'grpclib.server.Stream[rpc_pb2.AlarmRequest, rpc_pb2.AlarmResponse]') -> None:
        pass

    @abc.abstractmethod
    async def Status(self, stream: 'grpclib.server.Stream[rpc_pb2.StatusRequest, rpc_pb2.StatusResponse]') -> None:
        pass

    @abc.abstractmethod
    async def Defragment(self, stream: 'grpclib.server.Stream[rpc_pb2.DefragmentRequest, rpc_pb2.DefragmentResponse]') -> None:
        pass

    @abc.abstractmethod
    async def Hash(self, stream: 'grpclib.server.Stream[rpc_pb2.HashRequest, rpc_pb2.HashResponse]') -> None:
        pass

    @abc.abstractmethod
    async def HashKV(self, stream: 'grpclib.server.Stream[rpc_pb2.HashKVRequest, rpc_pb2.HashKVResponse]') -> None:
        pass

    @abc.abstractmethod
    async def Snapshot(self, stream: 'grpclib.server.Stream[rpc_pb2.SnapshotRequest, rpc_pb2.SnapshotResponse]') -> None:
        pass

    @abc.abstractmethod
    async def MoveLeader(self, stream: 'grpclib.server.Stream[rpc_pb2.MoveLeaderRequest, rpc_pb2.MoveLeaderResponse]') -> None:
        pass

    def __mapping__(self) -> typing.Dict[str, grpclib.const.Handler]:
        return {
            '/etcdserverpb.Maintenance/Alarm': grpclib.const.Handler(
                self.Alarm,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.AlarmRequest,
                rpc_pb2.AlarmResponse,
            ),
            '/etcdserverpb.Maintenance/Status': grpclib.const.Handler(
                self.Status,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.StatusRequest,
                rpc_pb2.StatusResponse,
            ),
            '/etcdserverpb.Maintenance/Defragment': grpclib.const.Handler(
                self.Defragment,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.DefragmentRequest,
                rpc_pb2.DefragmentResponse,
            ),
            '/etcdserverpb.Maintenance/Hash': grpclib.const.Handler(
                self.Hash,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.HashRequest,
                rpc_pb2.HashResponse,
            ),
            '/etcdserverpb.Maintenance/HashKV': grpclib.const.Handler(
                self.HashKV,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.HashKVRequest,
                rpc_pb2.HashKVResponse,
            ),
            '/etcdserverpb.Maintenance/Snapshot': grpclib.const.Handler(
                self.Snapshot,
                grpclib.const.Cardinality.UNARY_STREAM,
                rpc_pb2.SnapshotRequest,
                rpc_pb2.SnapshotResponse,
            ),
            '/etcdserverpb.Maintenance/MoveLeader': grpclib.const.Handler(
                self.MoveLeader,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.MoveLeaderRequest,
                rpc_pb2.MoveLeaderResponse,
            ),
        }


class MaintenanceStub:

    def __init__(self, channel: grpclib.client.Channel) -> None:
        self.Alarm = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Maintenance/Alarm',
            rpc_pb2.AlarmRequest,
            rpc_pb2.AlarmResponse,
        )
        self.Status = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Maintenance/Status',
            rpc_pb2.StatusRequest,
            rpc_pb2.StatusResponse,
        )
        self.Defragment = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Maintenance/Defragment',
            rpc_pb2.DefragmentRequest,
            rpc_pb2.DefragmentResponse,
        )
        self.Hash = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Maintenance/Hash',
            rpc_pb2.HashRequest,
            rpc_pb2.HashResponse,
        )
        self.HashKV = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Maintenance/HashKV',
            rpc_pb2.HashKVRequest,
            rpc_pb2.HashKVResponse,
        )
        self.Snapshot = grpclib.client.UnaryStreamMethod(
            channel,
            '/etcdserverpb.Maintenance/Snapshot',
            rpc_pb2.SnapshotRequest,
            rpc_pb2.SnapshotResponse,
        )
        self.MoveLeader = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Maintenance/MoveLeader',
            rpc_pb2.MoveLeaderRequest,
            rpc_pb2.MoveLeaderResponse,
        )


class AuthBase(abc.ABC):

    @abc.abstractmethod
    async def AuthEnable(self, stream: 'grpclib.server.Stream[rpc_pb2.AuthEnableRequest, rpc_pb2.AuthEnableResponse]') -> None:
        pass

    @abc.abstractmethod
    async def AuthDisable(self, stream: 'grpclib.server.Stream[rpc_pb2.AuthDisableRequest, rpc_pb2.AuthDisableResponse]') -> None:
        pass

    @abc.abstractmethod
    async def Authenticate(self, stream: 'grpclib.server.Stream[rpc_pb2.AuthenticateRequest, rpc_pb2.AuthenticateResponse]') -> None:
        pass

    @abc.abstractmethod
    async def UserAdd(self, stream: 'grpclib.server.Stream[rpc_pb2.AuthUserAddRequest, rpc_pb2.AuthUserAddResponse]') -> None:
        pass

    @abc.abstractmethod
    async def UserGet(self, stream: 'grpclib.server.Stream[rpc_pb2.AuthUserGetRequest, rpc_pb2.AuthUserGetResponse]') -> None:
        pass

    @abc.abstractmethod
    async def UserList(self, stream: 'grpclib.server.Stream[rpc_pb2.AuthUserListRequest, rpc_pb2.AuthUserListResponse]') -> None:
        pass

    @abc.abstractmethod
    async def UserDelete(self, stream: 'grpclib.server.Stream[rpc_pb2.AuthUserDeleteRequest, rpc_pb2.AuthUserDeleteResponse]') -> None:
        pass

    @abc.abstractmethod
    async def UserChangePassword(self, stream: 'grpclib.server.Stream[rpc_pb2.AuthUserChangePasswordRequest, rpc_pb2.AuthUserChangePasswordResponse]') -> None:
        pass

    @abc.abstractmethod
    async def UserGrantRole(self, stream: 'grpclib.server.Stream[rpc_pb2.AuthUserGrantRoleRequest, rpc_pb2.AuthUserGrantRoleResponse]') -> None:
        pass

    @abc.abstractmethod
    async def UserRevokeRole(self, stream: 'grpclib.server.Stream[rpc_pb2.AuthUserRevokeRoleRequest, rpc_pb2.AuthUserRevokeRoleResponse]') -> None:
        pass

    @abc.abstractmethod
    async def RoleAdd(self, stream: 'grpclib.server.Stream[rpc_pb2.AuthRoleAddRequest, rpc_pb2.AuthRoleAddResponse]') -> None:
        pass

    @abc.abstractmethod
    async def RoleGet(self, stream: 'grpclib.server.Stream[rpc_pb2.AuthRoleGetRequest, rpc_pb2.AuthRoleGetResponse]') -> None:
        pass

    @abc.abstractmethod
    async def RoleList(self, stream: 'grpclib.server.Stream[rpc_pb2.AuthRoleListRequest, rpc_pb2.AuthRoleListResponse]') -> None:
        pass

    @abc.abstractmethod
    async def RoleDelete(self, stream: 'grpclib.server.Stream[rpc_pb2.AuthRoleDeleteRequest, rpc_pb2.AuthRoleDeleteResponse]') -> None:
        pass

    @abc.abstractmethod
    async def RoleGrantPermission(self, stream: 'grpclib.server.Stream[rpc_pb2.AuthRoleGrantPermissionRequest, rpc_pb2.AuthRoleGrantPermissionResponse]') -> None:
        pass

    @abc.abstractmethod
    async def RoleRevokePermission(self, stream: 'grpclib.server.Stream[rpc_pb2.AuthRoleRevokePermissionRequest, rpc_pb2.AuthRoleRevokePermissionResponse]') -> None:
        pass

    def __mapping__(self) -> typing.Dict[str, grpclib.const.Handler]:
        return {
            '/etcdserverpb.Auth/AuthEnable': grpclib.const.Handler(
                self.AuthEnable,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.AuthEnableRequest,
                rpc_pb2.AuthEnableResponse,
            ),
            '/etcdserverpb.Auth/AuthDisable': grpclib.const.Handler(
                self.AuthDisable,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.AuthDisableRequest,
                rpc_pb2.AuthDisableResponse,
            ),
            '/etcdserverpb.Auth/Authenticate': grpclib.const.Handler(
                self.Authenticate,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.AuthenticateRequest,
                rpc_pb2.AuthenticateResponse,
            ),
            '/etcdserverpb.Auth/UserAdd': grpclib.const.Handler(
                self.UserAdd,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.AuthUserAddRequest,
                rpc_pb2.AuthUserAddResponse,
            ),
            '/etcdserverpb.Auth/UserGet': grpclib.const.Handler(
                self.UserGet,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.AuthUserGetRequest,
                rpc_pb2.AuthUserGetResponse,
            ),
            '/etcdserverpb.Auth/UserList': grpclib.const.Handler(
                self.UserList,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.AuthUserListRequest,
                rpc_pb2.AuthUserListResponse,
            ),
            '/etcdserverpb.Auth/UserDelete': grpclib.const.Handler(
                self.UserDelete,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.AuthUserDeleteRequest,
                rpc_pb2.AuthUserDeleteResponse,
            ),
            '/etcdserverpb.Auth/UserChangePassword': grpclib.const.Handler(
                self.UserChangePassword,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.AuthUserChangePasswordRequest,
                rpc_pb2.AuthUserChangePasswordResponse,
            ),
            '/etcdserverpb.Auth/UserGrantRole': grpclib.const.Handler(
                self.UserGrantRole,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.AuthUserGrantRoleRequest,
                rpc_pb2.AuthUserGrantRoleResponse,
            ),
            '/etcdserverpb.Auth/UserRevokeRole': grpclib.const.Handler(
                self.UserRevokeRole,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.AuthUserRevokeRoleRequest,
                rpc_pb2.AuthUserRevokeRoleResponse,
            ),
            '/etcdserverpb.Auth/RoleAdd': grpclib.const.Handler(
                self.RoleAdd,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.AuthRoleAddRequest,
                rpc_pb2.AuthRoleAddResponse,
            ),
            '/etcdserverpb.Auth/RoleGet': grpclib.const.Handler(
                self.RoleGet,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.AuthRoleGetRequest,
                rpc_pb2.AuthRoleGetResponse,
            ),
            '/etcdserverpb.Auth/RoleList': grpclib.const.Handler(
                self.RoleList,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.AuthRoleListRequest,
                rpc_pb2.AuthRoleListResponse,
            ),
            '/etcdserverpb.Auth/RoleDelete': grpclib.const.Handler(
                self.RoleDelete,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.AuthRoleDeleteRequest,
                rpc_pb2.AuthRoleDeleteResponse,
            ),
            '/etcdserverpb.Auth/RoleGrantPermission': grpclib.const.Handler(
                self.RoleGrantPermission,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.AuthRoleGrantPermissionRequest,
                rpc_pb2.AuthRoleGrantPermissionResponse,
            ),
            '/etcdserverpb.Auth/RoleRevokePermission': grpclib.const.Handler(
                self.RoleRevokePermission,
                grpclib.const.Cardinality.UNARY_UNARY,
                rpc_pb2.AuthRoleRevokePermissionRequest,
                rpc_pb2.AuthRoleRevokePermissionResponse,
            ),
        }


class AuthStub:

    def __init__(self, channel: grpclib.client.Channel) -> None:
        self.AuthEnable = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Auth/AuthEnable',
            rpc_pb2.AuthEnableRequest,
            rpc_pb2.AuthEnableResponse,
        )
        self.AuthDisable = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Auth/AuthDisable',
            rpc_pb2.AuthDisableRequest,
            rpc_pb2.AuthDisableResponse,
        )
        self.Authenticate = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Auth/Authenticate',
            rpc_pb2.AuthenticateRequest,
            rpc_pb2.AuthenticateResponse,
        )
        self.UserAdd = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Auth/UserAdd',
            rpc_pb2.AuthUserAddRequest,
            rpc_pb2.AuthUserAddResponse,
        )
        self.UserGet = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Auth/UserGet',
            rpc_pb2.AuthUserGetRequest,
            rpc_pb2.AuthUserGetResponse,
        )
        self.UserList = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Auth/UserList',
            rpc_pb2.AuthUserListRequest,
            rpc_pb2.AuthUserListResponse,
        )
        self.UserDelete = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Auth/UserDelete',
            rpc_pb2.AuthUserDeleteRequest,
            rpc_pb2.AuthUserDeleteResponse,
        )
        self.UserChangePassword = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Auth/UserChangePassword',
            rpc_pb2.AuthUserChangePasswordRequest,
            rpc_pb2.AuthUserChangePasswordResponse,
        )
        self.UserGrantRole = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Auth/UserGrantRole',
            rpc_pb2.AuthUserGrantRoleRequest,
            rpc_pb2.AuthUserGrantRoleResponse,
        )
        self.UserRevokeRole = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Auth/UserRevokeRole',
            rpc_pb2.AuthUserRevokeRoleRequest,
            rpc_pb2.AuthUserRevokeRoleResponse,
        )
        self.RoleAdd = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Auth/RoleAdd',
            rpc_pb2.AuthRoleAddRequest,
            rpc_pb2.AuthRoleAddResponse,
        )
        self.RoleGet = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Auth/RoleGet',
            rpc_pb2.AuthRoleGetRequest,
            rpc_pb2.AuthRoleGetResponse,
        )
        self.RoleList = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Auth/RoleList',
            rpc_pb2.AuthRoleListRequest,
            rpc_pb2.AuthRoleListResponse,
        )
        self.RoleDelete = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Auth/RoleDelete',
            rpc_pb2.AuthRoleDeleteRequest,
            rpc_pb2.AuthRoleDeleteResponse,
        )
        self.RoleGrantPermission = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Auth/RoleGrantPermission',
            rpc_pb2.AuthRoleGrantPermissionRequest,
            rpc_pb2.AuthRoleGrantPermissionResponse,
        )
        self.RoleRevokePermission = grpclib.client.UnaryUnaryMethod(
            channel,
            '/etcdserverpb.Auth/RoleRevokePermission',
            rpc_pb2.AuthRoleRevokePermissionRequest,
            rpc_pb2.AuthRoleRevokePermissionResponse,
        )
