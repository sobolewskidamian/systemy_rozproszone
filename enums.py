from enum import Enum


class ServerResponse(Enum):
    connection_established = 1
    nick_occupied = 2
    nick_invalid = 3
    exit = 4


class ClientResponse(Enum):
    exit = 1
