#!/bin/sh
curl --write-out "%{http_code}\n" \
      --silent \
      --write-out "%{http_code}\n" \
      -H "Content-Type: application/json" \
      -X POST 127.0.0.1:5000/clearbook
