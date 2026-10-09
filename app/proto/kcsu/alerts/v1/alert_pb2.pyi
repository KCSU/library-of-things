from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Alert(_message.Message):
    __slots__ = ("source", "dedup_key", "occurred_at_unix", "summary", "detail", "extra")
    class ExtraEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    DEDUP_KEY_FIELD_NUMBER: _ClassVar[int]
    OCCURRED_AT_UNIX_FIELD_NUMBER: _ClassVar[int]
    SUMMARY_FIELD_NUMBER: _ClassVar[int]
    DETAIL_FIELD_NUMBER: _ClassVar[int]
    EXTRA_FIELD_NUMBER: _ClassVar[int]
    source: str
    dedup_key: str
    occurred_at_unix: int
    summary: str
    detail: str
    extra: _containers.ScalarMap[str, str]
    def __init__(self, source: _Optional[str] = ..., dedup_key: _Optional[str] = ..., occurred_at_unix: _Optional[int] = ..., summary: _Optional[str] = ..., detail: _Optional[str] = ..., extra: _Optional[_Mapping[str, str]] = ...) -> None: ...
