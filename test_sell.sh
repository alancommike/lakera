#!/bin/sh

# test selling an order

# start with the order book empty
./clear_orderbook.sh | grep -q 200
[ $? -eq 0 ] || echo "failed to clear"

# sell with empty book, should get a 404
./sell_order.sh aaa uid 1 1 | grep -q 404
[ $? -eq 0 ] || echo "failed with empty book"


# add a buy order and sell an order that doesn't match that ticker symbol
./add_buy.sh bbb uid 1 1 | grep -q 200
[ $? -eq 0 ] || echo "failed buy add"
./sell_order.sh ccc uid 1 1 | grep -q 404
[ $? -eq 0 ] || echo "failed with selling non-match"

./clear_orderbook.sh | grep -q 200
[ $? -eq 0 ] || echo "failed to clear"

# add a buy and then sell an exact match
./add_buy.sh bbb uid 1 1 | grep -q 200
[ $? -eq 0 ] || echo "failed buy add"
./sell_order.sh bbb uid 1 1 | grep -q 200
[ $? -eq 0 ] || echo "failed with selling exact match"
./dump_orderbook.sh  | grep -q '"bbb": \[\]'
[ $? -eq 0 ] || echo "failed removing an exact match sell from buy queue"


./clear_orderbook.sh | grep -q 200
[ $? -eq 0 ] || echo "failed to clear"

# add a multiple small buys and one large sell to exactly match
./add_buy.sh bbb uid 1 10 | grep -q 200
[ $? -eq 0 ] || echo "failed buy add"
./add_buy.sh bbb uid 1 10 | grep -q 200
[ $? -eq 0 ] || echo "failed buy add"
./sell_order.sh bbb uid 1 20 | grep -q 200
[ $? -eq 0 ] || echo "failed with selling multi-exact match"
./dump_orderbook.sh  | grep -q '"bbb": \[\]'
[ $? -eq 0 ] || echo "failed removing an multi-exact match sell from buy queue"


./clear_orderbook.sh | grep -q 200
[ $? -eq 0 ] || echo "failed to clear"

# sell less quantity than what the buyer wanted
./add_buy.sh bbb uid 1 10 | grep -q 200
[ $? -eq 0 ] || echo "failed buy add"
./sell_order.sh bbb uid 1 5 | grep -q 200
[ $? -eq 0 ] || echo "failed with selling less quantity"
./dump_orderbook.sh  | grep -q '"quantity": 5'
[ $? -eq 0 ] || echo "failed updating quantity from small sell from buy queue"


./clear_orderbook.sh | grep -q 200
[ $? -eq 0 ] || echo "failed to clear"

# sell more quantity than what the buyer wanted
./add_buy.sh bbb uid 1 10 | grep -q 200
[ $? -eq 0 ] || echo "failed buy add"
./sell_order.sh bbb uid 1 17 | grep -q 404
[ $? -eq 0 ] || echo "failed with selling more quantity"
./dump_orderbook.sh  | grep -q '"quantity": 7'
[ $? -eq 0 ] || echo "failed adding back to sell queue for remainder"
./dump_orderbook.sh  | grep -q '"bbb": \[\]'
[ $? -eq 0 ] || echo "failed removing more quantity sell from buy order book"


./clear_orderbook.sh | grep -q 200
[ $? -eq 0 ] || echo "failed to clear"

# sell at lower price than what the buyer was asking
./add_buy.sh bbb uid 10 10 | grep -q 200
[ $? -eq 0 ] || echo "failed buy add"
./sell_order.sh bbb uid 5 5 | grep -q 200
[ $? -eq 0 ] || echo "failed with selling at lower price"
./dump_orderbook.sh  | grep -q '"quantity": 5'
[ $? -eq 0 ] || echo "failed adding back to sell queue for remainder at lower price"
./dump_orderbook.sh  | grep -qv 200 | jq '.sell' | grep -q 'bbb'
[ $? -eq 1 ] || echo "failed, added a sell order when selling at lower price than buyer"


./clear_orderbook.sh | grep -q 200
[ $? -eq 0 ] || echo "failed to clear"

# sell at higher price than what the buyer was asking
./add_buy.sh bbb uid 10 10 | grep -q 200
[ $? -eq 0 ] || echo "failed buy add"
./sell_order.sh bbb uid 12 7 | grep -q 404
[ $? -eq 0 ] || echo "failed with selling at higher price"
./dump_orderbook.sh  | grep -q '"quantity": 7'
[ $? -eq 0 ] || echo "failed adding to sell queue for higher price"
./dump_orderbook.sh  | grep -q '"quantity": 10'
[ $? -eq 0 ] || echo "failed, removed buy when no match was made"


./clear_orderbook.sh | grep -q 200
[ $? -eq 0 ] || echo "failed to clear"

# sell against a non-exact match from middle of buy order queue
./add_buy.sh bbb uid 10 10 | grep -q 200
[ $? -eq 0 ] || echo "failed buy add"
./add_buy.sh bbb uid 20 10 | grep -q 200
[ $? -eq 0 ] || echo "failed buy add"
./add_buy.sh bbb uid 30 10 | grep -q 200
[ $? -eq 0 ] || echo "failed buy add"
./add_buy.sh bbb uid 40 10 | grep -q 200
[ $? -eq 0 ] || echo "failed buy add"
./sell_order.sh bbb uid 25 12 | grep -q 200
[ $? -eq 0 ] || echo "failed selling against non-exact long order queue"
./dump_orderbook.sh  | \
    grep -v 200 | jq '.[] | select(.bbb) | .bbb[] | [.price, .quantity] | @csv' | \
    grep -q "40,8"
[ $? -eq 0 ] || echo "failed in non-exact match in middle to subtract remainder"
./dump_orderbook.sh | \
    grep -v 200 | jq '.[] | select(.bbb) | .bbb[] | [.price, .quantity] | @csv' | \
    grep -qv "30"
[ $? -eq 0 ] || echo "failed to remove buy from middle of non-exact match sell"
