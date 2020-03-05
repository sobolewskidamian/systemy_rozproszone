import socket
import argparse
import threading
import sys
from enums import ServerResponse, ClientResponse
from ascii_art import ascii_art

DISCONNECTED = False


def print_message(message, nick):
    arr = message.split("::")
    print("\n(%s) %s\n%s> " % (arr[0], arr[1], nick), end='')


def listen_tcp(socket_tcp, nick):
    global DISCONNECTED
    try:
        while not DISCONNECTED:
            data = socket_tcp.recv(1024).decode('utf-8')
            if data == '':
                continue
            if data == ServerResponse.exit.name:
                raise Exception()
            print_message(data, nick)
    except:
        DISCONNECTED = True


def print_usage():
    print("Type 'message' to send 'message' to all chat users by TCP\n"
          "Type 'U message' to send 'message' to server by UDP and then to all users by TCP\n"
          "Type 'U ascii_art' to send ascii art to all users'\n")


def talk(socket_tcp, socket_udp, host, port, nick):
    global DISCONNECTED
    try:
        while not DISCONNECTED:
            msg = input("%s> " % nick)
            if msg in ['q', 'quit', 'exit']:
                msg = ClientResponse.exit.name

            if msg in ['h', 'help']:
                print_usage()
            elif msg.startswith("U "):
                if msg[2::] == 'ascii_art':
                    msg = 'U ' + ascii_art
                socket_udp.sendto(bytes("%s::%s" % (nick, msg[2::]), 'utf-8'), (host, port))
            # elif msg.startswith("M "):
            # socket_udp.sendto(bytes("%s::%s" % (nick, msg[2::]), 'utf-8'), (multicast_group, port))
            else:
                socket_tcp.sendall(msg.encode('utf-8'))
                if msg == ClientResponse.exit.name:
                    raise Exception()
    except:
        DISCONNECTED = True


def exit_server(socket_tcp):
    socket_tcp.sendall(ClientResponse.exit.name.encode('utf-8'))
    print("Disconnected from the server")


def set_nick(socket_tcp):
    try:
        while True:
            nick = input("Your nick: ")
            if nick == '':
                continue
            socket_tcp.sendall(nick.encode('utf-8'))
            message = socket_tcp.recv(1024).decode()
            if message == ServerResponse.connection_established.name:
                return nick
            elif message == ServerResponse.nick_occupied.name:
                print("Nick is occupied. Try other one")
            elif message == ServerResponse.nick_invalid.name:
                print("Nick is occupied. Try other one")
            else:
                print("Something wrong with server. Try again")
    except:
        sys.exit(0)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default=socket.gethostname())
    parser.add_argument('--port', type=int, default=9999)

    args = parser.parse_args()
    host = args.host
    port = args.port
    print("%s:%s" % (host, port))
    return host, port


def main():
    host, port = parse_args()

    socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        socket_tcp.connect((host, port))
    except:
        print("Failed connection to %s:%s" % (host, port))
        sys.exit(1)
    nick = set_nick(socket_tcp)

    try:
        t_listen_tcp = threading.Thread(target=listen_tcp, args=(socket_tcp, nick))
        t_talk = threading.Thread(target=talk, args=(socket_tcp, socket_udp, host, port, nick))

        t_listen_tcp.setDaemon(True)
        t_talk.setDaemon(True)

        t_listen_tcp.start()
        t_talk.start()

        t_talk.join()
    except:
        pass

    exit_server(socket_tcp)
    socket_tcp.close()
    socket_udp.close()


if __name__ == "__main__":
    main()
