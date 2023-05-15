#!/usr/bin/env python3
import argparse
import json
import sys
import os
import csv
from time import sleep
from importUtils import *

import requests
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.util.retry import Retry


retries = Retry(total=3, backoff_factor=1, status_forcelist=[400, 500, 502, 503, 504])
http = requests.Session()
http.mount("https://", HTTPAdapter(max_retries=retries))


def import_prices(mappingFile, productCsvFile, csvFile, apiUrl, tenant, accessToken):
    mapping = read_json(mappingFile)
    csv_to_json(csvFile, "tmp/prices.json")
    database = read_json("tmp/prices.json")
    csv_to_json(productCsvFile, "tmp/products.json")
    productDatabase = read_json("tmp/products.json")
    for site in mapping['prices']['sites']:
      create_prices(mapping, database, productDatabase, site, apiUrl, tenant, accessToken)


def create_prices(mapping, database, productDatabase, site, apiUrl, tenant, accessToken):
    for item in database:
      sku = item[mapping['prices']['productIdentifier']['csvKey']]
      productId = construct_product_id(productDatabase, mapping, sku)
      if productId == None:
        print(f"Skipping price creation for {sku} because the identifier does not exist in product database")
      else:
        payload = prepare_payload(item, mapping, site, productId)
        persist_price(apiUrl, tenant, accessToken, payload)

def construct_product_id(productDatabase, mapping, productId):
  csvColumnId = mapping['products']['identifier']['csvKey']
  csvColumnParentId = mapping['products']['parentIdentifier']['csvKey']
  csvColumnProductType = mapping['products']['productType']['csvKey']

  for item in productDatabase:
    if item[csvColumnId] == productId:
      if item[csvColumnProductType] == "VARIANT":
          return item[csvColumnParentId] + "--" + productId
      else:
          return productId
  return None


def prepare_payload(item, mapping, site, productId):
  currency = site['currency']
  siteCode = site['siteCode']
  country = site['location']
  prices = list()
  for tier in site['tiers']:
    priceValue = item[tier['csvKey']]
    prices.append({"priceValue" : priceValue})
  payload = {
           "itemId": {
             "itemType": "PRODUCT",
             "id": productId
           },
           "currency": currency,
           "location": {
             "countryCode": country
           },
           "restrictions": {
             "siteCodes": [
               siteCode
             ]
           },
           "tierValues": prices
         }
  return payload

def persist_price(apiUrl, tenant, accessToken, payload):
    r = http.post(f'{apiUrl}/price/{tenant}/prices',
      #json = json.dumps(payload), NBER Change that
      json = payload,
      headers = {'Authorization' : f'Bearer {accessToken}', 'X-Version' : 'v2'})
    response = r.json()
    print(response)
    if r.status_code not in (200, 201, 204):
        print(f"Error: {r.status_code} - {r.text}")
        r.raise_for_status()
    return response