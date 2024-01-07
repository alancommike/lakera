import csv

from flask import Flask
from flask import request
from sortedcontainers import SortedKeyList
from collections import namedtuple
import simplejson

Stock = namedtuple('Stock', ['name', 'uid', 'price', 'quantity'])

class Matcher:
    def __init__(self):
        self._do_init()
    def _do_init(self):
        self.buy_list = {}
        self.sell_list = {}
        self.market_price = {}
        self.profit = 0
        self._read_tickers()

    def _read_tickers(self):
        with open('nasdaq-listings/data/nasdaq-listed-symbols.csv') as tickers:
            reader = csv.reader(tickers, delimiter=',')
            next(reader)
            for row in reader:
                self.buy_list[row[0]] = SortedKeyList([], key=lambda k: k.price)
                self.sell_list[row[0]] = SortedKeyList([], key=lambda k: k.price)
    def _clear(self):
        self._do_init()
    def _add(self, l, list_name, s):
       if s.name in l:
            l[s.name].add(s)
            print ("adding %s to %s list" % (s, list_name))
       else:
            l[s.name] = SortedKeyList([], key=lambda k: k.price)
            l[s.name].add(s)
            print("creating %s list with %s" % (list_name, s))

    # Buy a stock
    #
    # buy if there's a matching sell for a price less than the buy
    # if there's no match, queue the order for later.
    # TODO: notification for when an order that has been queued has been executed
    #
    # returns 404 if there was no match
    # returns 200 if the order went through
    def buy(self, new_order):
        # if there's no stock of this type in the buy list, queue this sell order
        if new_order.name not in self.sell_list:
            self._add(self.buy_list, "sell", new_order)
            return [], 404

        print("buying %s" % new_order.name)
        wanted = new_order.quantity   # tracks how much is wanted to buy. goes to zero as buying happens
        delq = []                     # delete queue for items that have been sold

        print("profit: %s" % self.profit)
        # sell list is ordered by price, so start iterating at the start of the sell queue
        for pending_order in self.sell_list[new_order.name].irange(maximum=Stock("", "", new_order.price, 0),reverse=True):
            # nothing to do, stop looking at the sell orders
            if wanted == 0:
                break

            # the amount left after this transaction with the current buy order. there are 3 case:
            # left < 0 - this queued sell order is not large enough to fill the whole buy order
            # left = 0 - order is filled
            # left > 0 - order partially filled the queued sell
            left = pending_order.quantity - wanted

            # track which buy orders get deleted. can delete while iterating
            delq.append(pending_order)

            # want to buy more than there is, remove order and keep looking
            if left < 0:
                self.profit += (new_order.price - pending_order.price) * pending_order.quantity
                wanted = wanted - pending_order.quantity
                print("bought %d of %s, want %d more" % (pending_order.quantity, new_order.name, wanted))
                # emit bought order.quantity of s.name

            # sold what was wanted
            if left == 0:
                self.profit += (new_order.price - pending_order.price) * pending_order.quantity
                print("bought %d of %s, fullfilled" % (new_order.quantity, new_order.name))
                wanted = wanted - pending_order.quantity
                # emit bought s.quantity of s.name

            # buy less than there is, debit the quantity on the order books by adding a
            # new order into the books with the remainder
            if left > 0:
                self.profit += (new_order.price - pending_order.price) * new_order.quantity

                new_order = pending_order._replace(quantity=(pending_order.quantity - wanted))
                self._add(self.sell_list, "sell", new_order)
                print("bought %d of %s, still have %d" % (new_order.quantity, new_order.name, new_order.quantity))
                wanted = 0
                # emit bought s.quantity of s.name


        print("profit: %s" % self.profit)

        # remove the sell orders, can't do it while iterating
        for x in delq:
            self.sell_list[new_order.name].remove(x)

        # finally, if there's still some of the buy order that is wanted, queue it for later
        if wanted != 0:
            print("Unsold, adding to sell list")
            self._add(self.buy_list, "buy",
                      Stock(new_order.name, new_order.uid, new_order.price, wanted))
            return [], 404
        else:
            return {"sold": new_order.quantity - wanted}, 200

    # Sell a stock
    #
    # sell if there's a matching buy for a price at least as high as the sell.
    # if there's no match, queue the order for later.
    # TODO: notification for when an order that has been queued has been executed
    #
    # returns 404 if there was no match
    # returns 200 if the order went through
    def sell(self, new_order):
        # if there's no stock of this type in the buy list, queue this sell order
        if new_order.name not in self.buy_list:
            self._add(self.sell_list, "sell", new_order)
            return [], 404

        print("selling %s" % new_order.name)
        wanted = new_order.quantity   # tracks how much is wanted to sell. goes to zero as selling happens
        delq = []                     # delete queue for items that have been sold

        # buy list is ordered by price, so start iterating at buy price >= sell price
        for pending_order in self.buy_list[new_order.name].irange(minimum=Stock("", "", new_order.price, 0)):
            # nothing to do, stop looking at the buy orders
            if wanted == 0:
                break

            # the amount left after this transaction with the current buy order. there are 3 case:
            # left < 0 - this queued buy order is not large enough to fill the whole sell order
            # left = 0 - order is filled
            # left > 0 - order partially filled the queued buy
            left = pending_order.quantity - wanted

            # track which buy orders get deleted. can delete while iterating
            delq.append(pending_order)

            # want to sell more than there is, remove order and keep looking
            if left < 0:
                wanted = wanted - pending_order.quantity
                print("sold %d of %s, want %d more" % (pending_order.quantity, new_order.name, wanted))
                # emit sold order.quantity of s.name

            # sold what was wanted
            if left == 0:
                print("sold %d of %s, fullfilled" % (new_order.quantity, new_order.name))
                wanted = wanted - pending_order.quantity
                # emit sold s.quantity of s.name

            # sold less than there is, deb
            # it the quantity on the order books by adding a
            # new order into the books with the remainder
            if left > 0:
                new_order = pending_order._replace(quantity=(pending_order.quantity - wanted))
                self._add(self.buy_list, "buy", new_order)
                print("sold %d of %s, still have %d" % (new_order.quantity, new_order.name, new_order.quantity))
                wanted = 0
                # emit sold s.quantity of s.name

        # remove the buy orders, can't do it while iterating
        for x in delq:
            self.buy_list[new_order.name].remove(x)

        # finally, if there's still some of the sell order that is wanted, queue it for later
        if wanted != 0:
            print("Unsold, adding to sell list")
            self._add(self.sell_list, "sell",
                      Stock(new_order.name, new_order.uid, new_order.price, wanted))
            return [], 404
        else:
            return {"sold": new_order.quantity-wanted}, 200

    def quotes(self):
        q = {}

        # lowest price in the sell order book is the price of the stock
        for stock, orders in self.sell_list.items():
            if len(orders):
                q[stock] = orders[0].price
        return q

app = Flask(__name__)
matcher = Matcher()
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
    for key, value in matcher.sell_list.items():
        order_book['sell'][key] = [v for v in value]

    for key, value in matcher.buy_list.items():
        order_book['buy'][key] = [v for v in value]

    return simplejson.dumps(order_book), 200

@app.route('/clearbook', methods=['POST'])
def clearbook():
    matcher._clear()
    return dict({"status": "cleared"})
def debug_add_helper(l, list_name, req):
    matcher._add(l, list_name, _req2stock(req))
    print(l)
    for b in l.keys():
        print("keys {}".format(b))
        print(l[b])
@app.route('/add_buy', methods=['POST'])
def add_buy():
    debug_add_helper(matcher.buy_list, "buy", request.get_json())

    return dict({"bought": "true"})

@app.route('/add_sell', methods=['POST'])
def add_sell():
    debug_add_helper(matcher.sell_list, "sell", request.get_json())

    return dict({"sold": "true"})
if __name__ == '__main__':
    app.run()
