#!/bin/sh

# test manually adding a buy and sell order

# start with the order book empty
./clear_orderbook.sh | grep -q 200
[ $? -eq 0 ] || echo "failed to clear"


# add a buy order and a sell order
./add_buy.sh aaa uid 1 1 | grep -q 200
[ $? -eq 0 ] || echo "failed buy add"

./add_sell.sh bbb uid 1 1 | grep -q 200
[ $? -eq 0 ] || echo "failed sell add"


# make sure the orders are there
./dump_orderbook.sh  | grep -q 200
[ $? -eq 0 ] || echo "failed get order book"

aaa=$(./dump_orderbook.sh  | grep 'aaa' | wc -l)
[ ${aaa} -eq 2 ] || echo "didn't successfully add buy order"

bbb=$(./dump_orderbook.sh  | grep 'bbb' | wc -l)
[ ${bbb} -eq 2 ] || echo "didn't successfully add sell order"


# add a second buy order and make sure there's two
./add_buy.sh aaa uid 1 1 | grep -q 200
[ $? -eq 0 ] || echo "failed 2nd buy add"

aaa=$(./dump_orderbook.sh  | grep 'aaa' | wc -l)
[ ${aaa} -eq 3 ] || echo "didn't successfully add buy order"