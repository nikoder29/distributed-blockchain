import socket
import logging

logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.DEBUG)

logger = logging.getLogger(__name__)

# The server's hostname or IP address
HOST = '127.0.0.1'
# The port used by the server
PORT = 65432

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
    client_socket.connect((HOST, PORT))
    client_socket.sendall(b'Hello, world')
    data = client_socket.recv(1024)
    logger.info('Received : ' + repr(data))
    while True:
        user_input = input("client prompt >> ")
        client_socket.sendall(str.encode(user_input))
        data = client_socket.recv(1024).decode()
        logger.info('Received : ' + repr(data))
        if data == 'quit':
            logger.info("Bye..have a good one!")
            break




