import requests
import json

server = 'http://127.0.0.1:5000'
response = requests.get(server)
print(response.json())

buy ={
    "stock" : "alan",
    "quantity" : 1,
    "price" : 10
}

sell ={
    "stock" : "pam",
    "quantity" : 1,
    "price" : 10
}

response = requests.post("http://127.0.0.1:5000/buy", json=buy)
print(response.status_code)
if response.text:
    print(response.text)

response = requests.post("http://127.0.0.1:5000/sell", json=sell)
print(response.status_code)
