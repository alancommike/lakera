#!/bin/sh
curl --write-out "%{http_code}\n" \
      --silent \
      -H "Content-Type: application/json" \
      -X GET 127.0.0.1:5000/quotes | jq .

/bin/echo -n "Profit: "
curl --silent \
      -H "Content-Type: application/json" \
      -X GET 127.0.0.1:5000/profit 
