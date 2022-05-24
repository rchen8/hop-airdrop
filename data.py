from collections import defaultdict
import json
import redis
import requests
import sys

r = redis.Redis(host='localhost', port=6379)

def reset():
  letters = '0123456789abcdef'
  for char in letters:
    r.set('txns_' + char, '[]')

def get_eligible_addresses():
  with open('blacklist_hop.txt') as file:
    blacklist = set([x.strip() for x in file.readlines()])

  url = 'https://raw.githubusercontent.com/hop-protocol/hop-airdrop/master/src/data/eligibleAddresses.txt'
  addresses = requests.get(url).text.split('\n')[0:-1]
  for addr in addresses:
    if addr in blacklist:
      addresses.remove(addr)
  return set(addresses)

addresses = get_eligible_addresses()

def get_senders(address):
  api_key = 'lol im not gonna commit this to github'
  url = 'https://api.covalenthq.com/v1/10/address/%s/transactions_v2/?quote-currency=USD&format=JSON&block-signed-at-asc=false&no-logs=true&page-size=1000000&page-number=&key=%s' % (address, api_key)
  txns = requests.get(url).json()['data']['items']
  return set([txn['from_address'] for txn in txns if txn['from_address'] != address]) & addresses

def get_data():
  char = sys.argv[1]
  last_address = json.loads(r.get('txns_' + char))[-1][0]

  for address in sorted(list(addresses)):
    if address[2] != char:
      continue
    if address <= last_address:
      continue
    senders = get_senders(address)
    print(address, senders)
    if len(senders) > 0:
      txns = json.loads(r.get('txns_' + char))
      for sender in senders:
        txns.append([address, sender])
      r.set('txns_' + char, json.dumps(txns))

def merge_data():
  letters = '0123456789abcdef'
  txns = []
  for char in letters:
    x = json.loads(r.get('txns_' + char))
    for row in x:
      txns.append([row[1], row[0]])
  r.set('txns', json.dumps(txns))

def restore_data():
  txns = []
  with open('txns.txt') as file:
    for row in file:
      row = row.replace('\n','').split(',')
      print(row)
      txns.append(row)
  r.set('txns', json.dumps(txns))

def export_to_csv():
  txns = json.loads(r.get('txns'))
  for row in txns:
    print('%s,%s' % (row[0], row[1]))

def update_addresses():
  txns = json.loads(r.get('txns'))
  new_txns = []
  for row in txns:
    if row[0] not in addresses and row[1] not in addresses:
      print(row)
    else:
      new_txns.append(row)
  r.set('txns', json.dumps(new_txns))

def blacklist_addresses():
  blacklist = []
  with open('blacklist.txt') as file:
    for row in file:
      blacklist.append(row.replace('\n', ''))

  txns = json.loads(r.get('txns'))
  new_txns = []
  for row in txns:
    if row[0] in blacklist or row[1] in blacklist:
      print(row)
      pass
    else:
      new_txns.append(row)
  r.set('txns', json.dumps(new_txns))
