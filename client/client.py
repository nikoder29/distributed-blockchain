import socket
import logging
import json
import sys
import pathlib
import os


from constants import *

logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.DEBUG)

logger = logging.getLogger(__name__)


class Client:

    def __init__(self, host, port, client_dict):
        logger.info("Host : " + host)
        logger.info("Port :" + str(port))
        self.client_dict = client_dict
        self.start_client(host, port)
        # self.host = host
        # self.port = port

    @staticmethod
    def display_menu():
        print("a. Press 1 to make a new transaction.")
        print("b. Press 2 to get balance")
        print("c. Press 3 to quit")

    def get_response_from_server(self, msg_dict, client_socket):
        msg_str = json.dumps(msg_dict)
        logger.debug('Sent : ' + msg_str)
        client_socket.sendall(msg_str.encode())
        data = client_socket.recv(1024).decode()
        logger.debug('Received : ' + repr(data))
        return data

    def start_client(self, client_host, client_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:

            client_socket.bind((client_host, client_port))
            client_socket.connect((SERVER_HOST, SERVER_PORT))

            while True:
                self.display_menu()
                user_input = input("Client prompt >> ")
                if user_input == "1":
                    self.handle_transfer_transaction(client_socket)

                elif user_input == "2":
                    msg_dict = {'type': 'balance_transaction'}
                    response = self.get_response_from_server(msg_dict, client_socket)
                    logger.info("Your current balance is : $" + response)

                elif user_input == "3":
                    msg_dict = {'type': 'quit'}
                    self.get_response_from_server(msg_dict, client_socket)
                    logger.info("Bye..have a good one!")
                    break

                else:
                    logger.warning("Incorrect menu option. Please try again..")
                    continue

    def handle_transfer_transaction(self, client_socket):
        receiver_id = input("Enter receiver client id  >> ")
        # TODO : add check if receiver is available in the config list or not
        if receiver_id not in self.client_dict:
            logger.error("Client id does not exist. Please try again with a valid client id..")
            return
        receiver_addr = self.client_dict[receiver_id]['host'] + ":" + str(self.client_dict[receiver_id]['port'])
        amount = input("Enter the amount in $$ to be transferred to the above client  >> ")
        msg_dict = {'type': 'transfer_transaction', 'receiver': receiver_addr, 'amount': amount}
        response = self.get_response_from_server(msg_dict, client_socket)
        if response == '0':
            print("Your transaction executed successfully")
        elif response == '1':
            print("The transaction failed due to insufficient funds!")
        elif response == '2':
            print("The transaction failed due to an error. Try again after sometime !")


if __name__ == '__main__':

    client_id = sys.argv[1]
    with open(os.path.join(pathlib.Path(__file__).parent.resolve(),'config.json'), 'r') as config_file:
        config_dict = json.load(config_file)
        client_dict = config_dict["clients"]
        if client_id not in client_dict:
            logger.error("Invalid client id. Please check...")
        else:
            logger.info("Initiating client..")
            Client(client_dict[client_id]["host"], client_dict[client_id]["port"], client_dict)



