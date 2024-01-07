#!/bin/sh

curl -H "Content-Type: application/json" \
   --silent \
   --write-out "%{http_code}\n" \
   -X POST 127.0.0.1:5000/buy  \
   -d '{"stock": "'$1'", "uid": "'$2'", "price": '$3',"quantity": '$4'}'

