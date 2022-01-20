import selectors
import socket
import logging
import json
import sys
import pathlib
import os
import time
import threading
import types
from queue import Queue

from queue import PriorityQueue
from constants import *
from lamport_mutex_utils import *

logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.DEBUG)

logger = logging.getLogger(__name__)


class Client:

    def __init__(self, client_id, client_dict):
        self.peer_clients_queue = Queue()
        self.processor_queue = Queue()
        self.client_dict = client_dict

        self.timestamp = Timestamp(1, os.getpid())
        self.request_queue = PriorityQueue()

        # Testing the priority queue

        #self.request_queue.put(Timestamp(10, 1234))
        #self.request_queue.put(Timestamp(1, 4321))
        #self.request_queue.put(Timestamp(3, 3758))
        #self.request_queue.put(Timestamp(3, 2345))
        #self.request_queue.put(Timestamp(6, 9577))

        #while self.request_queue:
        #    logger.info(repr(self.request_queue.get()))

        self.event = threading.Event()
        self.client_id = client_id
        self.client_dict = client_dict
        # client_thread = threading.Thread(target=self.start_peer_clients, args=(client_dict, client_id, self.peer_clients_queue))
        # client_thread.daemon = True
        self.peer_client_dict = {}
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_thread = threading.Thread(target=self.start_server, args=(client_dict, client_id, self.event, self.peer_client_dict, self.server_socket))
        server_thread.daemon = True
        server_thread.start()
        time.sleep(15)
        self.populate_peer_client_dict()
        self.start_master_client()
        # self.start_client(host, port)

        # self.host = host
        # self.port = port

    def __del__(self):
        for _, conn in self.peer_client_dict.items():
            conn.close()
        self.server_socket.close()

    @staticmethod
    def display_menu():
        print("a. Press 1 to make a new transaction.")
        print("b. Press 2 to get balance")
        print("c. Press 3 to quit")

    def get_response_from_server(self, msg_dict, client_socket):
        # The clock was already updates before calling this function
        msg_str = json.dumps(msg_dict)
        
        logger.debug('Message sent to blockchain master : ' + msg_str)
        time.sleep(2)
        client_socket.sendall(msg_str.encode())
        data = client_socket.recv(1024).decode()
        logger.debug('Message received from blockchain master : ' + repr(data))
        
        # update my clock after receiving a message from the server
        self.update_current_clock("Receive from server", 0) 
        
        return data

    def accept_wrapper(self, sock, selector):
        conn, addr = sock.accept()  # Should be ready to read
        print('accepted connection from', addr)
        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        selector.register(conn, events, data=data)

        # print(selector.get_map())

    def service_connection(self, key, mask, selector, peer_client_dict, client_id):
        sock = key.fileobj
        data = key.data
        client_host, client_port = sock.getpeername()
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(1024)  # Should be ready to read
            if recv_data:
                peer_client_addr = client_host + ":" + str(client_port)
                logger.info(f"Message received from client {peer_client_addr} : " + str(recv_data))
                res = self.handle_message_from_peer(recv_data, client_id, peer_client_dict)
                time.sleep(2)
                return res
                # sock.sendall(str(response).encode())
                # logger.info(f"Message sent to client {client_addr} : " + str(response))
            else:
                print('closing connection to : ', data.addr)
                selector.unregister(sock)
                sock.close()
        return 0

    def update_current_clock(self, event, new_clock):
        logger.info(f" \n++ Lamport clock before updating (event = {event}): " + str(self.timestamp.lamport_clock))
        old_clock = self.timestamp.lamport_clock
        self.timestamp.lamport_clock = max(old_clock, new_clock) + 1
        logger.info(f" \n++ Lamport clock after updating (event = {event}): " + str(self.timestamp.lamport_clock))

        

    def start_server(self, client_dict, client_id, event, peer_client_dict, server_socket):
        server_host = client_dict[client_id]["server_host"]
        server_port = client_dict[client_id]["server_port"]

        selector = selectors.DefaultSelector()
        # self.lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                server_socket.bind((server_host, server_port))
                break
            except Exception as ex:
                logger.error(ex)
                time.sleep(5)

        server_socket.listen()
        logger.info("Server is up and running!")
        logger.info("Waiting on new connections...")
        server_socket.setblocking(False)
        selector.register(server_socket, selectors.EVENT_READ, data=None)
        peer_reply_count = 0
        total_number_of_clients = len(client_dict) - 1
        while True:
            events = selector.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    self.accept_wrapper(key.fileobj, selector)
                else:
                    peer_reply_count += self.service_connection(key, mask, selector, peer_client_dict, client_id)
                    if peer_reply_count == total_number_of_clients:
                        if self.request_queue.queue[0].pid == self.timestamp.pid:
                            # this set event will be read by the main client, before sending a request to the blockchain server
                            event.set()
                            peer_reply_count = 0

    def wait_for_consensus_from_peers(self):
        # update my clock before broadcasting the REQUEST to peers
        self.update_current_clock("Send REQUEST", 0) 

        # Add the client's timestamp into its local queue
        self.request_queue.put(self.timestamp)
        logger.info(f"Request Queue at client {self.client_id} : " + str(sorted(self.request_queue.queue)))

        request_dict = {"type": "REQUEST", 'timestamp': self.timestamp.get_dict(), "client_id": self.client_id}

        for client_id, conn in self.peer_client_dict.items():
            # TODO: ADD SLEEP TIMER
            conn.sendall(json.dumps(request_dict).encode())
            logger.info(f"Message sent to client {client_id} : " + str(request_dict))
        
        
        
        # waiting for consensus ( REPLY ) from all the peers, to be set by the server
        self.event.wait()

    def send_release_to_peers(self):
        # update my clock before sending the RELEASE
        self.update_current_clock("Send RELEASE", 0) 

        release_dict = {"type": "RELEASE", 'timestamp': self.timestamp.get_dict(), "client_id": self.client_id}
        for client_id, conn in self.peer_client_dict.items():
            # TODO: ADD SLEEP TIMER
            conn.sendall(json.dumps(release_dict).encode())
            logger.info(f"Message sent to client {client_id} : " + str(release_dict))
        # waiting for consensus ( REPLY ) from all the peers, to be set by the server

        # Remove the queue entry corresponding to my request. 
        self.update_request_queue(self.timestamp.pid)     

        self.event.clear()

    def update_request_queue(self, pid_to_remove):
        # Can't remove element by index in PriorityQueue, 
        # so creating a new one without the entry to be deleted.

        new_queue = PriorityQueue()
        #import pdb
        while not self.request_queue.empty():
            # pop the first element
            entry = self.request_queue.get()
            #pdb.set_trace()
            if entry.pid != pid_to_remove:
                new_queue.put(entry)
            
        self.request_queue = new_queue

        logger.info(f"Request queue at client {self.client_id} : " + str(sorted(self.request_queue.queue)))
    

    def start_master_client(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # sock.setblocking(False)
            # client_socket.bind((client_dict[client_id]["client_host"], client_dict[client_id]["client_port"]))
            client_socket.connect((BLOCKCHAIN_SERVER_HOST, BLOCKCHAIN_SERVER_PORT))
            logger.info("Now connected to the blockchain server!")
            self.handle_balance_transaction(client_socket)

            while True:
                self.display_menu()
                user_input = input("Client prompt >> ")
                if user_input == "1":
                    self.wait_for_consensus_from_peers()
                    self.handle_balance_transaction(client_socket)
                    self.handle_transfer_transaction(client_socket)
                    self.handle_balance_transaction(client_socket)
                    self.send_release_to_peers()

                elif user_input == "2":

                    self.wait_for_consensus_from_peers()
                    self.handle_balance_transaction(client_socket)
                    self.send_release_to_peers()

                elif user_input == "3":
                    self.handle_quit(client_socket)
                    break

                else:
                    logger.warning("Incorrect menu option. Please try again..")
                    continue

    def handle_balance_transaction(self, client_socket):
        
        # update my clock before sending a message to the server.
        self.update_current_clock("Send to server", 0) # This will increment the current clock by 1
       
        msg_dict = {'type': 'balance_transaction', 'timestamp': self.timestamp.get_dict(), \
                    'client_id': self.client_id}
        response = self.get_response_from_server(msg_dict, client_socket)
        logger.info("Your current balance is : $" + response)

    def handle_transfer_transaction(self, client_socket):
        receiver_id = input("Enter receiver client id  >> ")
        # add check if receiver is available in the config list or not
        if receiver_id not in self.client_dict:
            logger.error("Client id does not exist. Please try again with a valid client id..")
            return
        # receiver_addr = self.client_dict[receiver_id]['host'] + ":" + str(self.client_dict[receiver_id]['port'])
        amount = input("Enter the amount in $$ to be transferred to the above client  >> ")

        # assuming that all clients will do the right thing, and not impersonate self as any other client
        # we can enforce this by not sending the sender client address, and having the blockchain figure that out from the connection object
        
        # update my clock before sending a message to the server.
        self.update_current_clock("Send to server", 0) # This will increment the current clock by 1

        msg_dict = {'type': 'transfer_transaction', 'timestamp': self.timestamp.get_dict(), \
                    'sender': self.client_id, 'receiver': receiver_id, 'amount': amount}

        response = self.get_response_from_server(msg_dict, client_socket)
        
        if response == '0':
            print("SUCCESS")
            # print("Your transaction executed successfully")
        elif response == '1':
            print("INCORRECT")
            # print("The transaction failed due to insufficient funds!")
        elif response == '2':
            print("INCORRECT")
            # print("The transaction failed due to an error. Try again after sometime !")

    def populate_peer_client_dict(self):
        # connect to the server of all other clients
        for other_client_id, client_details in self.client_dict.items():
            if other_client_id == self.client_id:
                continue

            # client_thread = threading.Thread(target=self.handle_peer_connection,
            #                                  args=(client_details["server_host"], client_details["server_port"]))
            server_addr = (client_details["server_host"], client_details["server_port"])
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # sock.setblocking(True)
            logger.info("Trying to connect to peer : " + other_client_id)
            while True:
                exit_code = sock.connect_ex(server_addr)
                print(exit_code)
                time.sleep(2)
                if exit_code == 0 or exit_code == 56:
                    break
            logger.info("Now connected to peer : " + other_client_id)
            self.peer_client_dict[other_client_id] = sock


    def handle_message_from_peer(self, msg, client_id, peer_client_dict):
        msg_dict = json.loads(msg.decode())
        peer_client_id = msg_dict["client_id"]

        # Extract the peer's Timestamp
        peer_clock = msg_dict['timestamp']['lamport_clock']
        peer_pid = msg_dict['timestamp']['pid']
        peer_timestamp = Timestamp(peer_clock, peer_pid)
        
        if msg_dict["type"] == "REQUEST":
            logger.info(f"REQUEST from client {peer_client_id} received at client {self.client_id}. ")
            
            # insert the requester's timestamp into the local request queue. 
            self.request_queue.put(peer_timestamp)
            
            logger.info(f"Request queue at client {self.client_id} : " + str(sorted(self.request_queue.queue)))
            
            # update my clock after receiving the REQUEST
            self.update_current_clock("Receive REQUEST", peer_clock) 
            
            # send reply to the server of the appropriate peer
            conn = peer_client_dict[peer_client_id]

            # update my clock before sending the REPLY
            self.update_current_clock("Send REPLY", 0) 

            response_dict = {'type': 'REPLY', 'timestamp': self.timestamp.get_dict(), 'client_id': client_id}
            # TODO: ADD SLEEP TIMER
            conn.sendall(json.dumps(response_dict).encode())
            logger.info(f"Message sent to client {peer_client_id} : " + str(response_dict))
            
            return 0
        elif msg_dict["type"] == "REPLY":
            # update my clock after receiving the REPLY
            self.update_current_clock("Receive REPLY", peer_clock) 
            return 1
        elif msg_dict["type"] == "RELEASE":
            # Remove the queue entry corresponding to the sender of the RELEASE. 
            self.update_request_queue(peer_pid)

            # update my clock after receiving the RELEASE
            self.update_current_clock("Receive RELEASE", peer_clock)

            return 0

    def handle_quit(self, client_socket):
        # update my clock before sending a message to the server.
        self.update_current_clock("Send to server", 0)
        
        msg_dict = {'type': 'quit', \
                    'timestamp': self.timestamp.get_dict()}
        
        self.get_response_from_server(msg_dict, client_socket)
        logger.info("Bye..have a good one!")

if __name__ == '__main__':
    argv_client_id = sys.argv[1]
    with open(os.path.join(pathlib.Path(__file__).parent.resolve(),'config.json'), 'r') as config_file:
        config_dict = json.load(config_file)
        client_dict = config_dict["clients"]
        if argv_client_id not in client_dict:
            logger.error("Invalid client id. Please check...")
        else:
            logger.info("Initiating client..")
            Client(argv_client_id, client_dict)
