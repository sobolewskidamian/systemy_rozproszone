import sys
import socket
import argparse
import threading
from enums import ServerResponse, ClientResponse

clients = {}


def register_new_client(client, connection):
    ip = connection[0]
    port = connection[1]
    while True:
        nick = client.recv(64).decode('utf-8')
        if nick == '':
            try:
                client.send(ServerResponse.nick_invalid.name.encode('utf-8'))
            except:
                break
        elif nick in clients:
            client.send(ServerResponse.nick_occupied.name.encode('utf-8'))
        else:
            client.send(ServerResponse.connection_established.name.encode('utf-8'))
            clients[nick] = [client, ip, port]
            print("%s connected from %s:%s" % (nick, ip, port))
            return nick


def client_tcp(client, connection):
    nick = register_new_client(client, connection)
    if nick is not None:
        send_broadcast(nick, "I joined the chat")

        try:
            while True:
                msg = client.recv(1024)
                msg = msg.decode('utf-8')
                print("    TCP - %s - %s" % (nick, msg))
                if msg.startswith(ClientResponse.exit.name):
                    del clients[nick]
                    break
                send_broadcast(nick, msg)
        except:
            del clients[nick]
        print("%s left the chat" % (nick,))
        send_broadcast(nick, "I left the chat")
    client.close()


def client_udp(socket_udp):
    while True:
        msg, address = socket_udp.recvfrom(8192)
        msg = str(msg, 'utf-8')
        msg = msg.split("::")
        nick = msg[0]
        msg = "::".join(msg[1::])
        print("    UDP - %s - %s" % (nick, msg))
        send_broadcast(nick, msg)


def send_broadcast(source_nick, message):
    reply = "%s::%s" % (source_nick, message)
    for target_client in clients.keys():
        if target_client != source_nick:
            clients[target_client][0].sendall(reply.encode('utf-8'))


def kill_all_clients():
    for client in clients.keys():
        try:
            clients[client][0].sendall(ServerResponse.exit.name.encode('utf-8'))
        except:
            pass


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
    socket_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        socket_tcp.bind((host, port))
        socket_tcp.listen(5)
        socket_udp.bind((host, port))
    except:
        print("Failed bind %s:%s" % (host, port))
        sys.exit(1)

    try:
        while True:
            client, conn = socket_tcp.accept()

            t_tcp = threading.Thread(target=client_tcp, args=(client, conn))
            t_udp = threading.Thread(target=client_udp, args=(socket_udp,))

            t_tcp.setDaemon(True)
            t_udp.setDaemon(True)

            t_tcp.start()
            t_udp.start()
    except:
        print("Shutting down the server")

    kill_all_clients()
    socket_tcp.close()
    socket_udp.close()


if __name__ == "__main__":
    main()
