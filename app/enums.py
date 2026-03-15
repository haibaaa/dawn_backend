from enum import Enum


class Status(str, Enum):
    PENDING= "pending"
    COMPLETED= "completed"