from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GroupSnapshot(_message.Message):
    __slots__ = ("id", "name", "description", "fetched_at_unix", "members")
    class Member(_message.Message):
        __slots__ = ("crsid", "name")
        CRSID_FIELD_NUMBER: _ClassVar[int]
        NAME_FIELD_NUMBER: _ClassVar[int]
        crsid: str
        name: str
        def __init__(self, crsid: _Optional[str] = ..., name: _Optional[str] = ...) -> None: ...
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    FETCHED_AT_UNIX_FIELD_NUMBER: _ClassVar[int]
    MEMBERS_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    description: str
    fetched_at_unix: int
    members: _containers.RepeatedCompositeFieldContainer[GroupSnapshot.Member]
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., fetched_at_unix: _Optional[int] = ..., members: _Optional[_Iterable[_Union[GroupSnapshot.Member, _Mapping]]] = ...) -> None: ...
