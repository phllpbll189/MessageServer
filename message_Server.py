import json
import threading
from socket import *


HOST = 'localhost'
PORT = 7778
CONN_PORT = 7777
CLIENTS = []


def name_taken(name):
    """ Returns True if name is already in CLIENTS

    :param name: prefered name sent from client
    :return: Bool, True if name is already in CLIENTS
    """
    for i in CLIENTS:
        if name == i[0]:
            return True
    return False


def send_intro_message(message, result, client_sock):
    """Sends message to connected client

    :param message: message options for message
    :param result: message to be sent to client
    :param client_sock: socket to send message too
    :return: None
    """
    msg = json.dumps((message, result))
    msg = msg.encode("utf-8")
    length_bytes = len(msg).to_bytes(4, 'big')
    msg = length_bytes + msg
    client_sock.sendall(msg)


def recv_all(length, recv_sock):
    """ Take a socket and the amount of data to be received and return it.

    :param length: The amount of data we are receiving
    :param recv_sock: The socket where we are receiving
    :return: Data that has been received
    """
    data = b''
    while len(data) < length:
        more = recv_sock.recv(length - len(data))
        if not more:
            raise EOFError('was expecting %d bytes but only received'
                           '%d bytes before the socket closed' % (length, len(data)))
        data += more
    return data


def init(new_sock):
    """ Take client's socket and name put in in a tuple,
        send back the port to the chat room

    :type new_sock: new socket connecting to server
    """
    while True:
        client_sock, addr = new_sock.accept()
        accepted = True
        while accepted:
            try:
                length = client_sock.recv(4)
                length = int.from_bytes(length, "big")
                json_data = recv_all(length, client_sock)
                dec_data = json_data.decode("utf-8")
                data = json.loads(dec_data)

                if data[0] == "START:" and len(data) > 1:
                    if not name_taken(data[1]):
                        CLIENTS.append((data[1], client_sock))
                        send_intro_message("accepted", CONN_PORT, client_sock)
                        accepted = False

                    else:
                        send_intro_message("Name Taken", "ERROR", client_sock)
                        print("ERROR: cannot replicate names")

                else:
                    send_intro_message("Wrong command use START: [your-name]", "ERROR", client_sock)
                    print("ERROR: wrong incoming command")
            except ConnectionResetError:
                pass


def chat(client_sock):
    """Recieves data from client_sock and sends to correct sockets

        Main Chat loop, will keep receiving messages until it recieves the exit message.
        Then it will notify other users the user has left, close the sockets, and return.

    :param client_sock: socket that sends messages this thread
    :return: None
    """
    username = ""
    private_sock = None
    while True:
        try:
            length = client_sock.recv(4)
            length = int.from_bytes(length, "big")

            message = recv_all(length, client_sock)
            message = message.decode("utf-8")
            message = json.loads(message)

            if message[0] == "setup":       # Initial setup for a socket
                for i in CLIENTS:           # finds the send socket tied to this recieve socket
                    if i[0] == message[1]:
                        private_sock = i[1]
                        username = message[1]       # And sets local username for later use
                        print(username + " has connected")
                        for u in CLIENTS:
                            send_intro_message(message[1], " :Has Connected", u[1])   # Connection message

            elif message[0] == "b":         # Sends the received message to everyone connected
                prepend = "BROADCAST: from " + username + ": "
                for i in CLIENTS:
                    send_intro_message(prepend, message[1], i[1])

            elif message[0] == "p":         # Sends the received message only to specified client
                prepend = "PRIVATE: from " + username + ": "
                user_found = False
                for i in CLIENTS:
                    if i[0] == message[1]:
                        send_intro_message(prepend, message[2], i[1])
                        user_found = True
                if not user_found:
                    send_intro_message(message[1], ": Not a Valid username", private_sock)

            elif message[0] == "e":         # If exit then tell other clients and exit/close sockets
                for i in CLIENTS:
                    if username == i[0]:
                        send_intro_message(username, " has left chat", i[1])
                        i[1].close()
                        client_sock.close()
                        client_to_remove = i
                    else:
                        send_intro_message(username, " has left chat", i[1])
                CLIENTS.remove(client_to_remove)
                print(username + " has left")
                return

        except ConnectionResetError:
            for i in CLIENTS:
                if username == i[0]:
                    i[1].close()
                    CLIENTS.remove(i)
                else:
                    print(username + " has left")
                    send_intro_message(username, " has left chat", i[1])
            client_sock.close()
            return


def read(read_sock):
    """Start new thread for every accepted client

    :param read_sock: new client's socket
    :return: None. infinitely accepts new clients
    """

    while True:
        client_sock, addr = read_sock.accept()
        threading.Thread(target=chat, args=(client_sock,)).start()


if __name__ == '__main__':
    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(20)         # Start up new sockets. One to initialize client connections

    conn = socket(AF_INET, SOCK_STREAM)
    conn.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    conn.bind((HOST, CONN_PORT))
    conn.listen(20)         # And another for connecting the sending client socket to its own thread.

    threading.Thread(target=read, args=(conn,)).start()
    threading.Thread(target=init, args=(sock,)).start()
