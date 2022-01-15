from typing import List
import hashlib
from block import Block


class Blockchain:
    INITIAL_CLIENT_BALANCE = 10

    def __init__(self):
        self.chain: List[Block] = []
        self.add_block(sender='dummy_sender', receiver='dummy_receiver', amount=0, previous_hash='0')

    def add_block(self, sender, receiver, amount, previous_hash):
        new_block = Block(sender, receiver, amount, previous_hash)
        self.chain.append(new_block)

    def get_balance(self, client: str):
        client_balance = Blockchain.INITIAL_CLIENT_BALANCE
        for block in self.chain:
            if block.transaction.sender == client:
                client_balance -= block.transaction.amount
            elif block.transaction.receiver == client:
                client_balance += block.transaction.amount

        return client_balance

    def execute_transaction(self, sender, receiver, amount):
        # check if sender has sufficient balance
        # add block to the chain if the above holds true
        # return 0 if block added successfully
        # else return 1 if the client has insufficient balance
        # return 2 for any other kind of error
        # if sender == receiver, return True without executing anything
        sender_balance = self.get_balance(sender)
        if sender_balance < amount:
            return 1

        self.add_block(sender, receiver, amount, self.get_previous_block_hash())
        return 0

    @staticmethod
    def hash(block):
        # encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(repr(block).encode()).hexdigest()

    def get_previous_block_hash(self):
        return Blockchain.hash(self.chain[-1])
