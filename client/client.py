import socket
import logging
import json

logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.DEBUG)

logger = logging.getLogger(__name__)

# The server's hostname or IP address
HOST = '127.0.0.1'
# The port used by the server
PORT = 65432


def display_menu():
    print("a. Press 1 to make a new transaction.")
    print("b. Press 2 to get balance")
    print("c. Press 3 to quit")


def get_response_from_server(msg_dict):
    msg_str = json.dumps(msg_dict)
    logger.debug('Sent : ' + msg_str)
    client_socket.sendall(msg_str.encode())
    data = client_socket.recv(1024).decode()
    logger.debug('Received : ' + repr(data))
    return data


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
    client_socket.connect((HOST, PORT))
    # client_socket.sendall(b'Hello, world')
    # data = client_socket.recv(1024)
    # logger.info('Received : ' + repr(data))
    while True:
        display_menu()
        print("Client prompt >> ", end="")
        user_input = input()
        if user_input == "1":
            receiver_addr = input("Enter receiver client's address  >> ")
            #TODO : add check if receiver is available in the config list or not
            amount = input("Enter the amount in $$ to be transferred to the above client  >> ")
            msg_dict = {'type': 'transfer_transaction', 'receiver': receiver_addr, 'amount': amount}
            response = get_response_from_server(msg_dict)
            if response == '0':
                print("Your transaction executed successfully")
            elif response == '1':
                print("The transaction failed due to insufficient funds!")
            elif response == '2':
                print("The transaction failed due to an error. Try again after sometime !")

        elif user_input == "2":
            msg_dict = {'type': 'balance_transaction'}
            response = get_response_from_server(msg_dict)
            logger.info("Your current balance is : $" + response)

        elif user_input == "3":
            msg_dict = {'type': 'quit'}
            response = get_response_from_server(msg_dict)
            logger.info("Bye..have a good one!")
            break

        else:
            logger.warning("Incorrect menu option. Please try again..")
            continue






