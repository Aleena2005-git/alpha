import hashlib
import json
from time import time


class Block:
    def __init__(self, index, timestamp, votes, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.votes = votes
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "votes": self.votes,
            "previous_hash": self.previous_hash
        }, sort_keys=True).encode()

        return hashlib.sha256(block_string).hexdigest()


class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.pending_votes = []

    def create_genesis_block(self):
        return Block(0, time(), [], "0")

    def get_latest_block(self):
        return self.chain[-1]

    def add_vote(self, vote):
        self.pending_votes.append(vote)

    def mine_block(self):
        if not self.pending_votes:
            return False

        new_block = Block(
            index=len(self.chain),
            timestamp=time(),
            votes=self.pending_votes,
            previous_hash=self.get_latest_block().hash
        )

        self.chain.append(new_block)
        self.pending_votes = []
        return True

    def has_voted(self, wallet, election, post):
        for block in self.chain:
            for vote in block.votes:
                if (
                    vote["wallet"] == wallet and
                    vote["election"] == election and
                    vote["post"] == post
                ):
                    return True
        return False

    def get_results(self, election, post):
        results = {}

        for block in self.chain:
            for vote in block.votes:
                if vote["election"] == election and vote["post"] == post:
                    candidate = vote["candidate"]
                    results[candidate] = results.get(candidate, 0) + 1

        return results