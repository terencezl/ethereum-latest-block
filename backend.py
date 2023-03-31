import gevent
from gevent import monkey
monkey.patch_all()
import time
from web3 import Web3
from datetime import datetime
import requests
from rich import print
from concurrent import futures
# from decimal import Decimal

uri_eth_node = "https://eth-mainnet.alchemyapi.io/v2/GNauZOAEhjOc34zQQqQuXorOlmC6wJ6W"
w3 = Web3(Web3.HTTPProvider(uri_eth_node))
latest_block = w3.eth.get_block('latest')

ts = latest_block["timestamp"]
ts_iso = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

uri_eth2usd_ts = f"https://min-api.cryptocompare.com/data/pricehistorical?fsym=ETH&tsyms=USD&ts={ts}"
r = requests.get(uri_eth2usd_ts)
price_at_ts = r.json()["ETH"]["USD"]
# note this price is in float, not Decimal
# if this is a problem, need to get exact price at timestamp
print(f"Timestamp: {ts_iso} Block Number: {latest_block['number']} Price: {price_at_ts}")

def get_transaction(tx_hash):
    tx = w3.eth.get_transaction(tx_hash)
    return tx

# thread_pool = futures.ThreadPoolExecutor(max_workers=512)

# t = time.perf_counter()
# futures = []
# for t_hex in latest_block["transactions"]:
#     futures.append(thread_pool.submit(get_transaction, t_hex))

# for future in futures:
#     tx = future.result()
#     val_eth = w3.from_wei(tx.get('value', None), 'ether')
#     val_usd = float(val_eth) * price_at_ts
#     print(f"From: {tx.get('from', None)} To: {tx.get('to', None)} Value: {val_eth:20f} ETH Value: {val_usd:20f} USD")

# print(f"Time: {time.perf_counter() - t:0.4f} seconds")
# print("-" * 80)

# green threads
pool = gevent.pool.Pool(512)

t = time.perf_counter()
transactions = pool.map(get_transaction, latest_block["transactions"])

for tx in transactions:
    val_eth = w3.from_wei(tx.get('value', None), 'ether')
    val_usd = float(val_eth) * price_at_ts
    print(f"From: {tx.get('from', None)} To: {tx.get('to', None)} Value: {val_eth:20f} ETH Value: {val_usd:20f} USD")
print(f"Time: {time.perf_counter() - t:0.4f} seconds")
