class Block:
    class Transaction:
        def __init__(self, sender, receiver, amount):
            self.sender = sender
            self.receiver = receiver
            self.amount = amount

        def __repr__(self):
            return ":".join([self.sender, self.receiver, str(self.amount)])

    def __init__(self, sender, receiver, amount, previous_hash):
        self.transaction = Block.Transaction(sender, receiver, amount)
        self.previous_hash = previous_hash

    def __repr__(self):
        return ":".join(["transaction", repr(self.transaction), "previous_hash", self.previous_hash])

