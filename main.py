import socket
import select
from datetime import datetime
from PyDictionary import PyDictionary
from Functions import *
from Encryptions import Hash


MAX_MSG_LENGTH = 1024
SERVER_PORT = 5555
SERVER_IP = "127.0.0.1"
print("Setting up server...")
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((SERVER_IP, SERVER_PORT))
server_socket.listen()
DATA2 = "Server Message: "
print("Listening for clients...")
client_sockets = []
messages_To_Send = []
PARTS_OF_SPEECH = ("Noun", "Verb", "Adjective")
room_dict = {"": []}
h = Hash(1)


def get_meaning(messege):  # gets a message and returns the meaning of it
    definition = h.decrypt(messege)
    dictionary = PyDictionary(definition)
    meaning_unsorted = dictionary.getMeanings()[definition]
    meaning_sorted = f"meaning of the word {definition}:\n"
    if meaning_unsorted is None:
        return False
    for i in range(len(PARTS_OF_SPEECH)):
        if PARTS_OF_SPEECH[i] in meaning_unsorted:
            meaning_sorted += f"{PARTS_OF_SPEECH[i]}: {meaning_unsorted[PARTS_OF_SPEECH[i]][0]}\n\n"
    return h.encrypt(meaning_sorted)


while True:
    rlist, wlist, xlist = select.select([server_socket] + client_sockets, client_sockets, [])
    for current_socket in rlist:  # goes over list of sockets it can read from
        if current_socket is server_socket:
            connection, client_address = current_socket.accept()
            room_dict[""].append(connection)
            print("New client joined!", client_address)
            client_sockets.append(connection)
        else:
            try:
                data = current_socket.recv(MAX_MSG_LENGTH).decode()
                if data == "STOP":  # if data is STOP then disconnect the client socket
                    print("Connection closed", datetime.now().strftime("%H:%M"), client_address[0])
                    client_sockets.remove(current_socket)
                    current_socket.close()
                else:
                    messages_To_Send.append((current_socket, find_key_in_dict_of_lists(room_dict, current_socket), data))  # appends socket of sender and message into list of messages
                    print(datetime.now().strftime("%H:%M"), h.decrypt(data), client_address[0])

            except ConnectionResetError as E:
                print("Connection closed", datetime.now().strftime("%H:%M"), client_address[0])
                client_sockets.remove(current_socket)
                current_socket.close()
    for message in messages_To_Send:
        current_socket, code, data = message
        if data[0] == "*":  # if client requests to join or open a private chat room
            data = data[1::]
            room_dict[code].remove(current_socket)
            if data not in room_dict.keys():
                room_dict[data] = [current_socket]
            else:
                room_dict[data].append(current_socket)
            data = "*"
        if data[0] == "@":
            data = data[2::]
            if current_socket in wlist:
                if get_meaning(data) is False:
                    current_socket.send("Definition Not Found".encode("UTF-8"))
                else:
                    current_socket.send(get_meaning(data).encode("UTF-8"))
        else:
            if data != "*":
                for sock in room_dict[code]:
                    if sock in wlist and sock != current_socket:
                        sock.send(data.encode("UTF-8"))

        messages_To_Send.remove(message)

# Todo add restricted number of people in room
