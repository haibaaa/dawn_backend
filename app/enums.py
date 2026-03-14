from enum import Enum


class Status(str, Enum):
    pending= "pending"
    completed= "completed"