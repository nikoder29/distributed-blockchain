import socket
import logging
import time
import json
import selectors
import types

from blockchain_utils import Blockchain
from constants import *

logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.DEBUG)

logger = logging.getLogger(__name__)


class BlockchainMaster:
    def __init__(self):
        self.blockchain = Blockchain()
        self.lsock = None
        self.start_server()

    def __del__(self):
        logger.debug("closing the server socket..")
        self.lsock.close()

    def handle_message(self, msg, client_addr):
        # TODO: add sanity check for json
        msg_dict = json.loads(msg.decode())
        if msg_dict["type"] == "quit":
            return "quit"
        elif msg_dict["type"] == "balance_transaction":
            return self.handle_balance_transaction(client_addr)
        elif msg_dict["type"] == "transfer_transaction":
            return self.handle_transfer_transaction(msg_dict, client_addr)
        logger.warning("that is cool but we don't understand this lingo yet!")
        return -1

    def handle_transfer_transaction(self, msg_dict, client_addr):
        # return 1 if transaction executed successfully, else return 0
        #TODO: fix the format for client_addr
        sender = client_addr
        receiver = msg_dict['receiver']  # extract receiver from msg
        #TODO: sanity check if amount is a valid floating point number!
        amount = float(msg_dict['amount'])  # extract amount from msg
        result = self.blockchain.execute_transaction(sender, receiver, amount)
        return result
        # if result:
        #     return "transaction_executed"
        # return "transaction_failed"

    def handle_balance_transaction(self, client_addr):
        return self.blockchain.get_balance(client_addr)

    def accept_wrapper(self, sock, selector):
        conn, addr = sock.accept()  # Should be ready to read
        print('accepted connection from', addr)
        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        selector.register(conn, events, data=data)

    def service_connection(self, key, mask, selector):
        sock = key.fileobj
        data = key.data
        client_host, client_port = sock.getpeername()
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(1024)  # Should be ready to read
            if recv_data:
                # data.outb += recv_data
                client_addr = client_host + ":" + str(client_port)
                logger.info(f"Message received from client {client_addr} : " + str(recv_data))
                response = self.handle_message(recv_data, client_addr)
                time.sleep(2)
                sock.sendall(str(response).encode())
                logger.info(f"Message sent to client {client_addr} : " + str(response))
            else:
                print('closing connection to : ', data.addr)
                selector.unregister(sock)
                sock.close()
        # if mask & selectors.EVENT_WRITE:
        #     if data.outb:
        #         print('echoing', repr(data.outb), 'to', data.addr)
        #         sent = sock.send(data.outb)  # Should be ready to write
        #         data.outb = data.outb[sent:]

    def start_server(self):
        selector = selectors.DefaultSelector()
        self.lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.lsock.bind((SERVER_HOST, SERVER_PORT))
        self.lsock.listen()
        logger.info("Waiting on new connections...")
        self.lsock.setblocking(False)
        selector.register(self.lsock, selectors.EVENT_READ, data=None)

        while True:
            events = selector.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    self.accept_wrapper(key.fileobj, selector)
                else:
                    self.service_connection(key, mask, selector)

    # def start_server(self):
    #     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    #         server_socket.bind((SERVER_HOST, SERVER_PORT))
    #         server_socket.listen()
    #         logger.info("Waiting on new connections...")
    #         conn, addr = server_socket.accept()
    #         with conn:
    #             logger.info('Connected by : ' + str(addr))
    #             while True:
    #                 data = conn.recv(1024)
    #                 if not data:
    #                     continue
    #                 response = self.handle_message(data, str(addr))
    #                 #TODO: server should also send a json wrapped msg to client.
    #                 conn.sendall(str(response).encode())
    #                 if response == 'quit':
    #                     logger.info("Closing the connection : " + str(addr))
    #                     break


if __name__ == '__main__':
    BlockchainMaster()
