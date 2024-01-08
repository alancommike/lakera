#!/bin/sh

# test selling an order

# start with the order book empty
./clear_orderbook.sh | grep -q 200
[ $? -eq 0 ] || echo "failed to clear"

# buy with empty book, should get a 404 since stock doesn't exist
./buy_order.sh aaa uid 1 1 | grep -q 404
[ $? -eq 0 ] || echo "failed with empty book"


# add a sell order and a order that doesn't match that
./add_sell.sh bbb uid 1 1 | grep -q 200
[ $? -eq 0 ] || echo "failed sell add"
./buy_order.sh ccc uid 1 1 | grep -q 404
[ $? -eq 0 ] || echo "failed with selling non-match"


./clear_orderbook.sh | grep -q 200
[ $? -eq 0 ] || echo "failed to clear"

# add a sell and then buy an exact match
./add_sell.sh bbb uid 1 1 | grep -q 200
[ $? -eq 0 ] || echo "failed sell add"
./buy_order.sh bbb uid 1 1 | grep -q 200
[ $? -eq 0 ] || echo "failed with selling exact match"
./dump_orderbook.sh  | grep -q '"sell": {}'
[ $? -eq 0 ] || echo "failed removing an exact match buy from sell queue"


./clear_orderbook.sh | grep -q 200
[ $? -eq 0 ] || echo "failed to clear"

# buy when there's no seller
./add_sell.sh bbb uid 1 1 | grep -q 200
[ $? -eq 0 ] || echo "failed sell add"
./buy_order.sh bbb uid 1 1 | grep -q 200
[ $? -eq 0 ] || echo "failed with selling exact match"
./buy_order.sh bbb uid 1 1 | grep -q 202
[ $? -eq 0 ] || echo "failed  selling without a buyer"
./dump_orderbook.sh  | grep -q '"buy": {'
[ $? -eq 0 ] || echo "failed adding to buy queue when no seller"



./clear_orderbook.sh | grep -q 200
[ $? -eq 0 ] || echo "failed to clear"

# add a multiple small sells and one large buy to exactly match
./add_sell.sh bbb uid 1 10 | grep -q 200
[ $? -eq 0 ] || echo "failed sell add"
./add_sell.sh bbb uid 1 10 | grep -q 200
[ $? -eq 0 ] || echo "failed sell add"
./buy_order.sh bbb uid 1 20 | grep -q 200
[ $? -eq 0 ] || echo "failed with buying multi-exact match"
./dump_orderbook.sh  | grep -q '"sell": {}'
[ $? -eq 0 ] || echo "failed removing an multi-exact match buy from sell queue"


./clear_orderbook.sh | grep -q 200
[ $? -eq 0 ] || echo "failed to clear"

# buy less quantity than what the seller was selling
./add_sell.sh bbb uid 1 10 | grep -q 200
[ $? -eq 0 ] || echo "failed sell add"
./buy_order.sh bbb uid 1 5 | grep -q 200
[ $? -eq 0 ] || echo "failed with buying less quantity"
./dump_orderbook.sh  | grep -q '"quantity": 5'
[ $? -eq 0 ] || echo "failed updating quantity from small buy from sell queue"


./clear_orderbook.sh | grep -q 200
[ $? -eq 0 ] || echo "failed to clear"

# buy more quantity than what the seller was selling
./add_sell.sh bbb uid 1 10 | grep -q 200
[ $? -eq 0 ] || echo "failed buy add"
./buy_order.sh bbb uid 1 17 | grep -q 413
[ $? -eq 0 ] || echo "failed with buying more quantity"
./dump_orderbook.sh  | grep -q '"quantity": 7'
[ $? -eq 0 ] || echo "failed adding back to buy queue for remainder"
./dump_orderbook.sh  | grep -q '"sell": {}'
[ $? -eq 0 ] || echo "failed removing more quantity buy from sell order book"


./clear_orderbook.sh | grep -q 200
[ $? -eq 0 ] || echo "failed to clear"

# buy at lower price than what the seller was asking
./add_sell.sh bbb uid 10 10 | grep -q 200
[ $? -eq 0 ] || echo "failed sell add"
./buy_order.sh bbb uid 5 5 | grep -q 413
[ $? -eq 0 ] || echo "failed with selling at lower price"
./dump_orderbook.sh  | grep -q '"quantity": 5'
[ $? -eq 0 ] || echo "failed adding back to buy queue for remainder at lower price"
./dump_orderbook.sh  | grep -q '"quantity": 10'
[ $? -eq 0 ] || echo "failed, sell order should still be there"


./clear_orderbook.sh | grep -q 200
[ $? -eq 0 ] || echo "failed to clear"

# buy at higher price than what the seller was asking
./add_sell.sh bbb uid 10 10 | grep -q 200
[ $? -eq 0 ] || echo "failed sell add"
./buy_order.sh bbb uid 12 7 | grep -q 200
[ $? -eq 0 ] || echo "failed with selling at higher price"
./dump_orderbook.sh  | grep -q '"quantity": 3'
[ $? -eq 0 ] || echo "failed adding to sell queue for higher price"
./dump_orderbook.sh  | grep -qv 200 | jq '.buy' | grep -q 'bbb'
[ $? -eq 1 ] || echo "failed to remove buy order after a sale"


./clear_orderbook.sh | grep -q 200
[ $? -eq 0 ] || echo "failed to clear"

# buy against a non-exact match from middle of sell order queue
./add_sell.sh bbb uid 10 10 | grep -q 200
[ $? -eq 0 ] || echo "failed sell add"
./add_sell.sh bbb uid 20 10 | grep -q 200
[ $? -eq 0 ] || echo "failed sell add"
./add_sell.sh bbb uid 30 10 | grep -q 200
[ $? -eq 0 ] || echo "failed sell add"
./add_sell.sh bbb uid 40 10 | grep -q 200
[ $? -eq 0 ] || echo "failed sell add"
./buy_order.sh bbb uid 25 12 | grep -q 200
[ $? -eq 0 ] || echo "failed buying against non-exact long order queue"
./dump_orderbook.sh  | \
    grep -v 200 | jq '.[] | select(.bbb) | .bbb[] | [.price, .quantity] | @csv' | \
    grep -q "10,8"
[ $? -eq 0 ] || echo "failed in non-exact match in middle to subtract remainder"
./dump_orderbook.sh | \
    grep -v 200 | jq '.[] | select(.bbb) | .bbb[] | [.price, .quantity] | @csv' | \
    grep -qv "30"
[ $? -eq 0 ] || echo "failed to remove buy from middle of non-exact match sell"


