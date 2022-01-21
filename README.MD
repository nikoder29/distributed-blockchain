distributed blockchain client server model

How to run : 
Open two terminals, one for server, another for client.

To run the server :
python server/blockchain_master.py

To run the client:
python client/client.py 1
python client/client.py 2
python client/client.py 3

The client will show up the menu. Choose the appropriate option and add the details when asked, and wait for the response.


How to handle client discovery: 
1. The server broadcasts the list of active clients to all the connected clients, every time some client adds or leaves the server.
2. Or, we can maintain a config file, with the list of all the clients, such that every client can get the address of all other clients from this file, the only caveat being, if a client goes down, the network will hang!



Open Questions : 
1. How to handle blockchain server UI - done
2. What to do about #6 in the problem statement
3. Shall we send REQUEST / REPLY / RELEASE to self client as well.

References:
1. https://realpython.com/python-sockets/ 