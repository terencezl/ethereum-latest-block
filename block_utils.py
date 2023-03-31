import eventlet
from web3 import Web3
from datetime import datetime
import requests
from loguru import logger


class BlockUtils:
    def __init__(self, uri_eth_node, uri_eth2usd, pool_n_workers):
        self.uri_eth_node = uri_eth_node
        self.uri_eth2usd = uri_eth2usd
        self.w3 = Web3(Web3.HTTPProvider(self.uri_eth_node))
        # TODO: investigate w3 internal retrying and add retries if necessary for robustness
        self.pool = eventlet.GreenPool(pool_n_workers)

    def get_price_at_ts(self, ts):
        """Get ETH-USD price at timestamp.

        NOTE: this price is in float, not Decimal.
        If this is a problem, need to get exact price at timestamp.
        """
        # TODO: add retries if necessary for robustness
        r = requests.get(f"{self.uri_eth2usd}&ts={ts}")
        return r.json()["ETH"]["USD"]

    def check_latest_block(self):
        """Check latest block number."""
        latest_block = self.w3.eth.get_block("latest")
        return latest_block["number"]

    def get_latest_block(self, block_number="latest"):
        """Get latest block info with all transactions.

        Args:
            block_number (str, optional): Block number. Defaults to "latest".
        Returns:
            dict: Latest block info in format of:
            {
                "ts": "2021-05-01 00:00:00",
                "bn": 12345678,
                "price": 1234.56,
                "txs": [
                    {
                        "addr_from": "0x1234567890abcdef1234567890abcdef12345678",
                        "addr_to": "0x1234567890abcdef1234567890abcdef12345678",
                        "amt_eth": "1234.567890123456789",
                        "amt_usd": "1234567.890123456789"
                    },
                    ...
                ]
            }
        """
        latest_block = self.w3.eth.get_block(block_number)

        payload = {}
        ts = latest_block["timestamp"]
        ts_iso = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        bn = latest_block["number"]
        price_at_ts = self.get_price_at_ts(ts)
        payload["ts"] = ts_iso
        payload["bn"] = bn
        payload["price"] = price_at_ts
        logger.debug(f"Timestamp: {ts_iso} Block Number: {bn} Price: {price_at_ts}")

        payload["txs"] = []
        for tx in self.pool.imap(self.w3.eth.get_transaction, latest_block["transactions"]):
            # sometimes "to" field could be None
            # need to investigate but handle broadly here for now
            amt_eth = self.w3.from_wei(tx["value"], "ether")
            amt_usd = float(amt_eth) * price_at_ts

            payload["txs"].append(
                {
                    "addr_from": tx.get("from", " " * 42),
                    "addr_to": tx.get("to", " " * 42),
                    "amt_eth": f"{amt_eth:20f}",
                    "amt_usd": f"{amt_usd:20f}",
                }
            )

        return payload
