import socket
import logging
import time

logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.DEBUG)

logger = logging.getLogger(__name__)
# Standard loopback interface address (localhost)
HOST = '127.0.0.1'
# Port to listen on (non-privileged ports are > 1023)
PORT = 65432


def handle_message(msg):
    msg = msg.decode()
    logger.info("Received from server : " + msg)
    if msg.lower() == "quit":
        return "quit"
    return "that is cool!"


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    logger.info("Waiting on new connections...")
    conn, addr = server_socket.accept()
    with conn:
        logger.info('Connected by : ' + str(addr))
        while True:
            data = conn.recv(1024)
            if not data:
                continue
            response = handle_message(data)
            conn.sendall(response.encode())
            if response == 'quit':
                logger.info("Closing the connection : " + str(addr))
                break


