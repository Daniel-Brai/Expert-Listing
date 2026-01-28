from typing import TypeAlias
from uuid import UUID

from ulid import ULID

ID: TypeAlias = int | str | UUID | ULID
