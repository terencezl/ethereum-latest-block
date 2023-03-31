import eventlet
eventlet.monkey_patch()
import argparse
from web3 import Web3
from datetime import datetime
import requests
from loguru import logger

URI_ETH_NODE = "https://eth-mainnet.alchemyapi.io/v2/GNauZOAEhjOc34zQQqQuXorOlmC6wJ6W"
URI_ETH2USD = "https://min-api.cryptocompare.com/data/pricehistorical?fsym=ETH&tsyms=USD"

w3 = Web3(Web3.HTTPProvider(URI_ETH_NODE))
pool = eventlet.GreenPool(512)


def get_price_at_ts(ts):
    # note this price is in float, not Decimal
    # if this is a problem, need to get exact price at timestamp
    r = requests.get(f"{URI_ETH2USD}&ts={ts}")
    return r.json()["ETH"]["USD"]


def check_latest_block():
    latest_block = w3.eth.get_block('latest')
    return latest_block["number"]


def get_latest_block(block_number="latest"):
    latest_block = w3.eth.get_block(block_number)

    payload = {}
    ts = latest_block["timestamp"]
    ts_iso = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    bn = latest_block["number"]
    price_at_ts = get_price_at_ts(ts)
    payload["ts"] = ts_iso
    payload["bn"] = bn
    payload["price"] = price_at_ts
    logger.debug(f"Timestamp: {ts_iso} Block Number: {bn} Price: {price_at_ts}")

    payload["txs"] = []
    # nul_to_addr = None
    for tx in pool.imap(w3.eth.get_transaction, latest_block["transactions"]):
        # sometimes "to" field could be None
        # need to investigate but handle broardly here for now
        amt_eth = w3.from_wei(tx["value"], 'ether')
        amt_usd = float(amt_eth) * price_at_ts

        payload["txs"].append({
            "addr_from": tx.get('from', " " * 42),
            "addr_to": tx.get('to', " " * 42),
            "amt_eth": f"{amt_eth:20f}",
            "amt_usd": f"{amt_usd:20f}"
        })
        # logger.info(f"From: {tx.get('from', ' ' * 42)} To: {tx.get('to', ' ' * 42)} Value: {amt_eth:20f} ETH Value: {amt_usd:20f} USD")
        # if tx.get('to', None) is None:
        #     nul_to_addr = tx.get('to', " " * 42)

    # if nul_to_addr:
    #     logger.warning("Found null address in latest block. Investigate!")

    return payload


if __name__ == "__main__":
    # for i in range(16944200, 16944244):
    #     logger.info(f"Getting block {i}...")
    #     get_latest_block(i)
    pass
