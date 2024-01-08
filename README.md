# Lakera Stock exchange interview task
This implements the simple stock exchange for the Lakera interview task.

## Requirements
The assumption is there's a working python3, all other dependencies can be installed via the requirements.txt.

To run the test and debug scripts, _jq_ and _curl_ are required. 

Note: tested only on M2 Mac

## Environment Setup
To setup the environment for running the server and clients:
1. python3 -m venv .venv
2. . .venv/bin/activate
3. pip install -r requirements.txt

### Running the code in the setup environment
Start the server and then run the other tools against it. The server logs to the console.

- server:
  - python -m flask run 
  
- tests, or other apps
  - run the *.sh or *.py files directly, i.e. ./test_buy.sh

- API endpoints
  - Use curl to GET/POST to the endpoints on localhost:5000
  - curl --silent 
        -H "Content-Type: application/json" 
        -X GET 127.0.0.1:5000/profit 
- agent
  - client.py

## Basic design
There's a simple single threaded Flask server that manages the exchange. 
When the server starts it loads up a list of stock symbols from the NASDAQ exchange. 
These are from https://github.com/datasets/nasdaq-listings/tree/master and included in this repo.

The server keeps track of all the stock symbols in a single dict. 
Each entry (the _Bid_ NamedTuple) contains the symbol's market price, a buy list and a sell list.

The _buy_ and _sell_ listed are stored as a _SortedKeyList_, which makes for
[efficiently](https://grantjenks.com/docs/sortedcontainers/performance-scale.html) 
finding matching prices. 
When a buy or sell comes in, it is matched against the appropriate list. 
If there's no match, it's considered a limit order and stored as a _Stock_
NamedTuple which includes the quantity and price. 
The _Stock_ tuple carries with it a uid, which isn't currently used, though was added with the
thought of identifying agents that are buying/selling. 

As per the instructions, the exchange pockets the arbitrage between seller and buyer.
If a buy order comes in higher than a pending sell order, the sell is executed at its limit
and sold to the buyer at the higher price. Legality and customer satisfaction 
of this is TBD. 

## APIs
As this is a small and quick exercise, the testing, error checking, logging, and general robustness are limited. 
Rather than a formal test harness, scripts and debug endpoints are used to drive basic testing. There is
no proper logging, all logging is simply a python print().

### Debugging APIs
There are debug endpoints to drive basic testing
- POST /add_sell
  - Directly enter a limit sell order and create the ticker if it doesn't exist
  - { "stock": string, "uid": string, "price": int, "quantity": int}
  - see add_sell.sh
    - ./add_sell.sh GOOG uid 10 10
- POST /add_buy
  - Directly enter a limit buy order and create the ticker if it doesn't exist
  - { "stock": string, "uid": string, "price": int, "quantity": int}
  - see add_buy.sh
    - ./add_buy.sh GOOG uid 10 10
- POST /clearbook
  - Remove all the entries from the buy and sell lists
  - see clear_orderbook.sh
    - ./clear_orderbook.sh
- GET /orderbook
  - Return a JSON of the stock tickers that have buy and sell orders pending
  - See dump_orderbook.sh or watch_bids.sh
    - ./dump_orderbook.sh

### Production APIs
The two primary endpoints are /buy and /sell. 
For simplicity and time management, the returned JSON doesn't have the exact order execution.
In a production system, each order would be emitted to a message bus and matched with
the sell orders. 

- POST /buy
  - Post a buy, if there's a match with a sell it'll execute right then. If there's no match, it'll be queued for later.
  - { "stock": string, "uid": string, "price": int, "quantity": int}
  - see buy_order.sh
    - ./buy_order.sh GOOG "uid" 10 10
  - returns:
    - 200: buy was fulfilled
    - 202: there's no sell bids. bid was queued
    - 404: stock symbol doesn't exist
    - 413: buy was partial, remainder was queued
- POST /sell
  - Post a sell, if there's a match with a buy it'll execute right then. If there's no match, it'll be queued for later.
  - { "stock": string, "uid": string, "price": int, "quantity": int}
  - see sell_order.sh
    - ./sell_order.sh GOOG "uid" 10 10
  - returns:
    - 200: sell was fulfilled
    - 202: there's no buy bids. bid was queued
    - 404: stock symbol doesn't exist
    - 413: sell was partial, remainder was queued
- GET /quotes
  - return a JSON of the stock tickers that have executed and hence have a market price
  - see watch_quotes.sh
    - ./watch_quotes.sh
- GET /profit
  - return the profit that the exchange has made so far

### Testing and running
Minimal tests are run from the _test_add.sh_, test_buy.sh_, and _test_sell.sh_ scripts.

The general workflow to exercise the system is:
1. Start the server in one window
2. Start the watch_bids.sh in another window
3. Optionally start the watch_quotes.sh
4. Manually exercise the system via add_buy.sh, add_sell.sh, buy_order.sh, and sell_order.sh
   5. Watch the results from the watch windows and the logging from the server





