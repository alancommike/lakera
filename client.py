#!/usr/bin/env python
import requests
import json
import random
import sys
import csv
import time


server = 'http://127.0.0.1:5000'
response = requests.get(server)
print(response.json())

json_request = """{'stock': '%s', 'uid': 'uid', 'price': %d, 'quantity': %d}"""
session_headers = {'Connection': 'close', 'Content-Type': 'application/json' }

symbols = []
with open('nasdaq-listings/data/nasdaq-listed-symbols.csv') as tickers:
    reader = csv.reader(tickers, delimiter=',')
    next(reader)
    for row in reader:
        symbols.append(row[0])

num_stocks = len(symbols)
num_stocks = 10

def do_request(url, req, session):
    return session.post(url, json=req, headers=session_headers)

session = requests.session()

while True:
    stock_pick = symbols[int(num_stocks * random.random())]
    cointoss = random.random()
    buy = True if cointoss < .5 else False
    quantity = int(random.random() * 100)
    price = int(random.random() * 100)

    req = {}
    req['stock'] = stock_pick
    req['uid'] = 'uid'
    req['price'] = price
    req['quantity'] = quantity

    if buy:
        response = do_request("http://127.0.0.1:5000/buy", req, session)
    else:
        response = do_request("http://127.0.0.1:5000/sell", req, session)

    if response.text:
      print(response.text)

    response.close()
    time.sleep(.1)
