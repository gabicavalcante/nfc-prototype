from enum import Enum


class DoorProtocol(Enum):
    APDU = "\x00\xA4\x04\x00\x07\xF0\x39\x41\x48\x14\x81\x00\x00"
    DOOR_HELLO = "\x48\x45\x4C\x4C\x4F"  # "HELLO"
    DOOR_READY = "\x52\x45\x41\x44\x59"  # "READY"
    DOOR_WAIT = "\x57\x41\x49\x54"  # "WAIT"
    DOOR_ERROR = "\x45\x52\x52\x4F\x52"  # "ERROR"
    DOOR_DONE = "\x44\x4F\x4E\x45"  # "DONE"
    DOOR_GRANTED = "\x47\x52\x41\x4E\x54\x45\x44"  # "GRANTED"
    DOOR_READER_ERROR = "\x52\x45\x41\x44\x45\x52\x5F\x45\x52\x52\x4F\x52"  # "READER_ERROR"
    DOOR_DENY = "\x44\x45\x4E\x59"  # "DENY"
    DOOR_BYE = "\x42\x59\x45"  # "BYE"
    DOOR_NEXT = "\x4E\x45\x58\x54"  # "NEXT"
    DOOR_OK = "\x4F\x4B"  # "OK"
    DOOR_SUCCESS = "\x53\x55\x43\x43\x45\x53\x53"  # "SUCCESS"
    DOOR_RESPONSE = "\x52\x45\x53\x50\x4F\x4E\x53\x45"  # "RESPONSE"
    DOOR_RESULT = "\x52\x45\x53\x55\x4C\x54"  # "RESULT"


print(repr(DoorProtocol.APDU))