import threading
import json
from socket import *
import os

# Initial Global parameters
HOST = 'localhost'
PORT = 7778
username = ""
CONN_PORT = None
chat_messages = "Welcome To Chat Service\n"
current_input = "Enter your Desired username: \r"
chatting = True


def console_write():
    """ Detects chat log changes and neatly prints to console

        This works by assigning 2 global variables. If there
        is a change in either variable then it reprints
    :return: nothing, will stop when program stops
    """
    while chatting:  # Global shutdown variable. helps to exit thread
        print(chat_messages)
        print(current_input)
        chat = chat_messages
        inp = current_input
        while chat == chat_messages and inp == current_input:
            pass        # If there is a change to consoles input, Clear console & reprint
        os.system('cls')  # NOTE: THIS LINE ONLY WORKS IN WINDOWS
    print("exiting")
    return


def send_private_message(user_directions, user, message, server_sock):
    """ Send a private message to [user] with [message]

        take a username and send a message to that uses as a json
        json will contain, user_directions, user, and message
    :param user_directions: p (private message)
    :param user: username to send to
    :param message: messgae to send to other user
    :param server_sock: socket to send message through
    :return: None
    """
    global chat_messages
    #  Print message because it will not be sent back
    chat_messages = chat_messages + "PRIVATE: To " + user + ": " + message + "\n"
    msg = json.dumps((user_directions, user, message))   # include user in json
    msg = msg.encode("utf-8")

    length_bytes = len(msg).to_bytes(4, 'big')
    msg = length_bytes + msg

    server_sock.sendall(msg)
    return


def send_message(opt, message, server_sock):
    """ Send message as json with prepended option.

        messages will be formated with opt(options),
        followed by message as a json tuple.
    :param opt: b, p, e (broadcast, private, exit)
    :param message: String message
    :param server_sock: Socket to send to
    :return: None
    """
    msg = json.dumps((opt, message))  # Convert to json and encode
    msg = msg.encode("utf-8")

    length_bytes = len(msg).to_bytes(4, 'big')
    msg = length_bytes + msg  # Take length of message and append to front.

    server_sock.sendall(msg)
    return


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


def start(client_sock, ):
    """ Send INIT data to server to begin chatting.

        Sends username to server and server creates profile.
        Should recieve (Status_message, Chat_Server_Port)
        if done correctly. Otherwise (Status_message, Error_message)
        when it is done correctly it sets up to infinitely receive
        messages until the user quits.

    :socket sock: INIT server socket
    """
    global CONN_PORT, username, chat_messages, current_input

    while True:
        client_sock.connect((HOST, PORT))

        while True:
            # Initial Chat room setup

            opt = "START:"
            username = input()
            current_input = "Enter your desired username: "
            send_message(opt, username, client_sock)
            # Sends Username to server with Start: at begining

            length = client_sock.recv(4)
            length = int.from_bytes(length, "big")
            message = recv_all(length, client_sock)
            # Receive response

            message = message.decode("utf-8")
            message = json.loads(message)
            # And decode it

            # Did we have an ERROR or was it a success?
            if message[1] == "ERROR":
                chat_messages = chat_messages + "Error: USERNAME TAKEN [" + username + "] \n"
            else:
                CONN_PORT = message[1]
                chat_messages = chat_messages + "Connecting\n"
                client_sock.shutdown(SHUT_WR)

                while chatting:                # Starts only receiving through this thread
                    length = client_sock.recv(4)
                    length = int.from_bytes(length, "big")
                    message = recv_all(length, client_sock)

                    if 0 == len(message):  # Trying to figure out how to close a socket from a shutdown call from server
                        client_sock.close()
                        return

                    message = message.decode("utf-8")
                    message = json.loads(message)
                    chat_messages = chat_messages + message[0] + message[1] + "\n"
                client_sock.close()
                return


def write(send_sock, ):

    """Sends chat messages to Chat Server.

        Function should wait for CONN_PORT to not be None.
        Once start thread finishes it should be equal to
        the correct port. then will send Connection message

    """
    global username, current_input, chatting

    while CONN_PORT is None:
        pass

    send_sock.connect((HOST, CONN_PORT))
    send_message("setup", username, send_sock)  # Initial set up message to sync username

    while True:   # Main chat loop
        current_input = "Broadcast message, private message or, exit chat:\nType message, press \"p\", or \"e\"\r"
        user_directions = input()

        if user_directions == "p":  # Private message
            current_input = "Which user would you like to message: "
            user = input()
            current_input = "Type your message: "
            message = input()
            send_private_message(user_directions, user, message, send_sock)

        elif user_directions == "e":  # Exit message
            send_message(user_directions, "left", send_sock)
            send_sock.close()
            chatting = False   # Global shutdown variable. Will help shutdown threads
            return

        else:
            send_message("b", user_directions, send_sock)


if __name__ == '__main__':
    sock = socket()
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

    write_sock = socket()
    write_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    console_thread = threading.Thread(target=console_write).start()             # start console thread
    start_thread = threading.Thread(target=start, args=(sock,)).start()         # Start receiving thread
    write_thread = threading.Thread(target=write, args=(write_sock,)).start()   # Start writing thread

