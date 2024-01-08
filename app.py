from flask import Flask
from flask import request
import logging
from sortedcontainers import SortedKeyList
from typing import NamedTuple
import simplejson
import csv

# Basic data structures.
# Stock - used as a buy/sell entry
# Bid - each stock symbol has a bid entry
class Stock(NamedTuple):
    name: str
    uid: str
    price: int
    quantity: int

class Bid(NamedTuple):
    market_price: int
    buy: SortedKeyList
    sell: SortedKeyList

class Matcher:
    def __init__(self):
        self._do_init()
    def _do_init(self):
        self._bids = {}
        self._profit = 0

        self._read_tickers()

    # Bring in the NASDAQ ticker symbols
    def _read_tickers(self):
        with open('nasdaq-listings/data/nasdaq-listed-symbols.csv') as tickers:
            reader = csv.reader(tickers, delimiter=',')
            next(reader)
            for row in reader:
                self._add_ticker(row[0])

    def _clear(self):
        self._do_init()

    # small helper to add a bid to a buy or sell list
    def _add_bid(self, l, list_name, s):
        l.add(s)
        print("adding %s to %s list" % (s, list_name))

    # small helper to create a new ticker symbol entry
    def _add_ticker(self, symbol):
        if symbol not in self._bids:
            self._bids[symbol] = Bid(0,                                                 # market price
                                     SortedKeyList([], key=lambda k: k.price),  # buy list
                                     SortedKeyList([], key=lambda k: k.price))  # sell list

    # Take profit for any order where the sell price is less than the buy price.
    #
    # This is saying that the exchange will buy from the seller low and sell to
    # the buyer high, pocketing the difference.
    # legality, lawyers, and customer satisfaction TBD.
    #
    def _adjust_profit(self, buy_order, sell_order, wanted):

        # can only transact for the number of shares that exist
        shares_sold = sell_order.quantity if wanted > sell_order.quantity else wanted
        print("shares sold: %d" % shares_sold)

        self._profit += (buy_order.price - sell_order.price) * shares_sold
        print("price: %d" % (buy_order.price - sell_order.price))

    # The market price of a stock is the price that it is sold at.
    def _adjust_marketprice(self, buy_order, sell_order):
        self._bids[sell_order.name] = self._bids[sell_order.name]._replace(market_price=sell_order.price)

    # Buy a stock
    #
    # buy if there's a matching sell for a price less than the buy
    # if there's no match, queue the order for later.
    # TODO: notification for when an order that has been queued has been executed
    #
    # returns 404 if there was no match
    # returns 200 if the order went through
    def buy(self, new_order):

        # if this stock symbol doesn't exist, it's a 404 - not found
        if new_order.name not in self._bids:
            return '', 404

        sell_list = self._bids[new_order.name].sell
        buy_list =  self._bids[new_order.name].buy

        # there's no sellers, this then can't be bought
        # queue this buy order
        if not sell_list:
            self._add_bid(buy_list, "buy", new_order)
            return '', 202

        print("buying %s" % new_order.name)
        wanted = new_order.quantity   # tracks how much is wanted to buy. goes to zero as buying happens
        delq = []                     # delete queue for items that have been sold

        # sell list is ordered by price
        # find the highest priced sell order that is <= buy and work down the list to lower priced
        # sell orders.
        # example:
        #   sell order prices: 10, 20, 30
        # buy order of 25 will match the sell order of 20 and then if that isn't fully filled
        # match the 10.
        #
        for queued_order in sell_list.irange(maximum=Stock("", "", new_order.price, 0),reverse=True):
            # nothing to do, stop looking at the sell orders
            if wanted == 0:
                break

            # the amount left after this transaction with the current buy order. there are 3 case:
            # left < 0 - this queued sell order is not large enough to fill the whole buy order
            # left = 0 - order is filled
            # left > 0 - order partially filled the queued sell
            left = queued_order.quantity - wanted

            # track which buy orders get deleted. can delete while iterating
            delq.append(queued_order)
            self._adjust_profit(new_order, queued_order, wanted)
            self._adjust_marketprice(new_order, queued_order)

            # want to buy more than there is, remove order and keep looking
            if left < 0:
                wanted = wanted - queued_order.quantity
                print("bought %d of %s, want %d more" % (queued_order.quantity, new_order.name, wanted))
                # emit bought order.quantity of s.name

            # sold what was wanted
            if left == 0:
                print("bought %d of %s, fullfilled" % (new_order.quantity, new_order.name))
                wanted = wanted - queued_order.quantity
                # emit bought s.quantity of s.name

            # buy less than there is, debit the quantity on the order books by adding a
            # new order into the books with the remainder
            if left > 0:
                new_order = queued_order._replace(quantity=(queued_order.quantity - wanted))
                self._add_bid(sell_list, "sell", new_order)
                print("bought %d of %s, still have %d" % (new_order.quantity, new_order.name, new_order.quantity))
                wanted = 0
                # emit bought s.quantity of s.name

        # remove the sell orders, can't do it while iterating
        for x in delq:
            sell_list.remove(x)

        # finally, if there's still some of the buy order that is wanted, queue it for later
        if wanted != 0:
            print("Unsold, adding to sell list")
            self._add_bid(buy_list, "buy",
                      Stock(new_order.name, new_order.uid, new_order.price, wanted))
            return '', 413
        else:
            return "bought %s: %d" % (new_order.name, new_order.quantity - wanted), 200

    # Sell a stock
    #
    # sell if there's a matching buy for a price at least as high as the sell.
    # if there's no match, queue the order for later.
    # TODO: notification for when an order that has been queued has been executed
    #
    # returns 404 if there was no match
    # returns 200 if the order went through
    def sell(self, new_order):

        # if this stock symbol doesn't exist, it's a 404 - not found
        if new_order.name not in self._bids:
            return '', 404
        sell_list = self._bids[new_order.name].sell
        buy_list =  self._bids[new_order.name].buy

        print(buy_list)
        # there are no buyers, this then can't be sold
        # queue this sell order
        if not buy_list:
            self._add_bid(sell_list, "sell", new_order)
            return '', 202

        print("selling %s" % new_order.name)
        wanted = new_order.quantity   # tracks how much is wanted to sell. goes to zero as selling happens
        delq = []                     # delete queue for items that have been sold

        # buy list is ordered by price
        # find the lowest priced buy order that is >= sell and work up the list to higher priced
        # buy orders.
        # example:
        #   buy order prices: 10, 20, 30
        # sell order of 15 will match the buy order of 20 and then if that isn't fully filled
        # match the 30.
        #
        for queued_order in buy_list.irange(minimum=Stock("", "", new_order.price, 0)):
            # nothing to do, stop looking at the buy orders
            if wanted == 0:
                break

            # the amount left after this transaction with the current buy order. there are 3 case:
            # left < 0 - this queued buy order is not large enough to fill the whole sell order
            # left = 0 - order is filled
            # left > 0 - order partially filled the queued buy
            left = queued_order.quantity - wanted

            # track which buy orders get deleted. can delete while iterating
            delq.append(queued_order)
            self._adjust_profit(queued_order, new_order, wanted)
            self._adjust_marketprice(queued_order, new_order)

            # want to sell more than there is, remove order and keep looking
            if left < 0:
                wanted = wanted - queued_order.quantity
                print("sold %d of %s, want %d more" % (queued_order.quantity, new_order.name, wanted))
                # emit sold order.quantity of s.name

            # sold what was wanted
            if left == 0:
                print("sold %d of %s, fullfilled" % (new_order.quantity, new_order.name))
                wanted = wanted - queued_order.quantity
                # emit sold s.quantity of s.name

            # sold less than there is, deb
            # it the quantity on the order books by adding a
            # new order into the books with the remainder
            if left > 0:
                new_order = queued_order._replace(quantity=(queued_order.quantity - wanted))
                self._add_bid(buy_list, "buy", new_order)
                print("sold %d of %s, still have %d" % (new_order.quantity, new_order.name, new_order.quantity))
                wanted = 0
                # emit sold s.quantity of s.name

        # remove the buy orders, can't do it while iterating
        for x in delq:
            buy_list.remove(x)

        # finally, if there's still some of the sell order that is wanted, queue it for later
        if wanted != 0:
            print("Unsold, adding to sell list")
            self._add_bid(sell_list, "sell",
                        Stock(new_order.name, new_order.uid, new_order.price, wanted))
            return '', 413
        else:
            return "sold %s: %d" % (new_order.name, new_order.quantity-wanted), 200

    def quotes(self):
        q = {}

        for symbol, bids in self._bids.items():
            if bids.market_price != 0:
                q[symbol] = bids.market_price

        return q

    def profit(self):
        return self._profit

# Globals
app = Flask(__name__)
matcher = Matcher()

# turn off logging of the Flask requests and routing
logging.getLogger('werkzeug').setLevel(logging.CRITICAL)

@app.route('/')
def alive():
    return {'status': 'alive'}

def _req2stock(req):
    return Stock(req['stock'], req['uid'], req['price'], req['quantity'])

@app.route('/buy', methods=['POST'])
def buy():
    req = request.get_json()
    fullfillment, status = matcher.buy(_req2stock(req))

    return fullfillment, status
@app.route('/sell', methods=['POST'])
def sell():
    req = request.get_json()
    fullfillment, status = matcher.sell(_req2stock(req))

    return fullfillment, status

@app.route('/quotes', methods=['GET'])
def quotes():
    return simplejson.dumps(matcher.quotes()), 200

@app.route('/profit', methods=['GET'])
def profit():
    return simplejson.dumps(matcher.profit()), 200
#
# debugging and testing endpoints
#
# add a buy or sell order - /add_buy, /add_sell
# dump the order book - /orderbook
# clear the order book - /clearbook
#
@app.route('/orderbook', methods=['GET'])
def orderbook():
    order_book = {}
    order_book['sell'] = {}
    order_book['buy'] = {}
    for symbol, bids in matcher._bids.items():
        if bids.sell:
            order_book['sell'][symbol] = [v for v in bids.sell]

    for symbol, bids in matcher._bids.items():
        if bids.buy:
            order_book['buy'][symbol] = [v for v in bids.buy]

    return simplejson.dumps(order_book), 200

@app.route('/clearbook', methods=['POST'])
def clearbook():
    matcher._clear()
    return dict({"status": "cleared"})

@app.route('/add_buy', methods=['POST'])
def add_buy():
    s = _req2stock(request.get_json())
    matcher._add_ticker(s.name)
    matcher._add_bid(matcher._bids[s.name].buy, "buy", s)

    return dict({"bought": "true"})

@app.route('/add_sell', methods=['POST'])
def add_sell():
    s = _req2stock(request.get_json())
    matcher._add_ticker(s.name)
    matcher._add_bid(matcher._bids[s.name].sell, "sell", s)

    return dict({"sold": "true"})

if __name__ == '__main__':
    app.run()
