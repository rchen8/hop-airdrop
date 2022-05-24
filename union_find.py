from collections import defaultdict
from pyvis.network import Network
import json
import redis
import requests
import time

r = redis.Redis(host='localhost', port=6379)

set_ = defaultdict(str)

def union(i, j):
  set_[find(i)] = find(j)

def find(i):
  if set_[i] == i:
    return i
  set_[i] = find(set_[i])
  return set_[i]

def union_find():
  txns = json.loads(r.get('txns'))

  for row in txns:
    set_[row[0]] = row[0]
    set_[row[1]] = row[1]
  print(len(set_), len(set(set_.values())))

  for row in txns:
    union(set_[row[0]], set_[row[1]])

  for addr in set_.keys():
    find(addr)
  print(len(set_), len(set(set_.values())))

  freq = defaultdict(int)
  for addr in set_:
    freq[set_[addr]] += 1

  freq = {k: v for k, v in sorted(freq.items(), key=lambda item: -item[1])}
  for row in freq:
    if freq[row] < 10:
      break
    print(row, freq[row])

def get_cycle(addr):
  addrs = []
  for row in set_:
    if set_[row] == addr:
      addrs.append(row)
  # print(addrs)
  return addrs

def get_edges_from_cycle(cycle):
  txns = json.loads(r.get('txns'))
  edges = []
  for row in txns:
    if row[0] in cycle or row[1] in cycle:
      # print(row)
      edges.append(row)
  return edges

def delete_nodes(cycle, edges, nodes):
  new_cycle = cycle.copy()
  new_edges = edges.copy()
  for node in nodes:
    if node in cycle:
      new_cycle.remove(node)
    for edge in edges:
      if edge[0] == node or edge[1] == node:
        new_edges.remove(edge)
  return new_cycle, new_edges

def graph(cycle, edges):
  net = Network('950px', '1900px', directed=True)
  net.add_nodes(cycle)
  for row in edges:
    net.add_edge(row[0], row[1])
  net.show('hop.html')

def search_big_cycle(edges):
  adj_list = defaultdict(list)
  for edge in edges:
    adj_list[edge[0]].append(edge[1])
    adj_list[edge[1]].append(edge[0])

  count = {}
  for row in adj_list:
    count[row] = len(adj_list[row])
  count = {k: v for k, v in sorted(count.items(), key=lambda item: item[1])}
  print(count)

details = defaultdict(list)
activity = defaultdict(list)

def get_chain(name):
  if name == 'Gnosis':
    return 5
  if name == 'Polygon':
    return 4
  if name == 'Arbitrum':
    return 2
  if name == 'Optimism':
    return 3
  return 1

def get_hop_activity(address):
  url = 'https://explorer-api.hop.exchange/v1/transfers?perPage=25&startDate=2020-07-01&account=' + address
  data = requests.get(url).json()['data']
  dates = set([x['timestampIso'][0:10] for x in data])
  print(address, dates)
  for x in data:
    details[x['timestampIso'][0:10]].append([address[0:5], x['sourceChainName'], x['destinationChainName'], x['amountDisplay'], x['token']])
    
    if address not in activity:
      activity[address] = [0,0,0,0,0,0,0]
    activity[address][0] += 1
    activity[address][get_chain(x['sourceChainName'])] += 1
    activity[address][get_chain(x['destinationChainName'])] += 1
    activity[address][6] += x['amountUsd']
  return dates

def find_sybil_activity(cycle):
  freq = defaultdict(int)
  for node in sorted(cycle):
    for date in get_hop_activity(node):
      freq[date] += 1
  
  for key in sorted(details.keys()):
    print(key, details[key])
  for key in {k: v for k, v in sorted(activity.items(), key=lambda item: -item[1][6])}:
    print('| %s | %s | %s | %s | %s | %s | %s | %s |' % (key, activity[key][0], activity[key][1], activity[key][2], activity[key][3], activity[key][4], activity[key][5], round(activity[key][6])))

  freq = ({k: v for k, v in sorted(freq.items(), key=lambda item: -item[1])})
  for row in freq:
    if freq[row] == 1:
      break
    print('| %s | %s |' % (row, freq[row]))


union_find()
cycle = get_cycle('0xd491447348c474af15c40839d3e0056a80fec352')
edges = get_edges_from_cycle(cycle)

find_sybil_activity(cycle)
graph(cycle, edges)
# search_big_cycle(edges)