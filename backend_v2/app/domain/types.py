from typing import Any, TypeAlias


JSONPrimitive: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONPrimitive | dict[str, "JSONValue"] | list["JSONValue"]
MetadataMap: TypeAlias = dict[str, Any]
