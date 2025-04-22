#!/usr/bin/env python3
import argparse
import json
import sys
import os
import csv
import traceback
import logging
from time import sleep
from importUtils import *

import requests
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.util.retry import Retry


retries = Retry(total=3, backoff_factor=1, status_forcelist=[400, 500, 502, 503, 504])
http = requests.Session()
http.mount("https://", HTTPAdapter(max_retries=retries))


def import_availabilities(mappingFile, productCsvFile, availabilitiesCsvFile, apiUrl, tenant, accessToken):
    mapping = read_json(mappingFile)
    csv_to_json(availabilitiesCsvFile, "tmp/availabilities.json")
    database = read_json("tmp/availabilities.json")
    csv_to_json(productCsvFile, "tmp/products.json")
    productDatabase = read_json("tmp/products.json")
    for site in mapping['availabilities']['sites']:
      create_availabilities(mapping, database, productDatabase, site, apiUrl, tenant, accessToken)


def create_availabilities(mapping, database, productDatabase, site, apiUrl, tenant, accessToken):
    for item in database:
      try:
        sku = item[mapping['availabilities']['productIdentifier']['csvKey']]
        productId = construct_product_id(productDatabase, mapping, sku)
        if productId == None:
          print(f"Skipping price creation for {sku} because the identifier does not exist in product database")
        else:
          payload = prepare_payload(item, mapping, site, productId)
          persist_availability(apiUrl, tenant, accessToken, payload, productId, site['siteCode'])
      except Exception as e:
        print(f"Issue while creating an availability")
        logging.error(traceback.format_exc())


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
  siteCode = site['siteCode']
  try:
    stockLevel = int(item[site['csvKey']])
  except ValueError:
    stockLevel = 0

  payload = {
          "site" : siteCode,
          "stockLevel" : stockLevel,
          "available" : stockLevel > 0,
          "productId" : productId,
          "distributionChannel" : "ASSORTMENT"
         }
  print(json.dumps(payload))
  return payload

def persist_availability(apiUrl, tenant, accessToken, payload, productId,site):
    r = http.post(f'{apiUrl}/availability/{tenant}/availability/{productId}/{site}',
      json = payload,
      headers = {'Authorization' : f'Bearer {accessToken}'})
    response = r.json()
    print(response)
    if r.status_code not in (200, 201, 204):
        print(f"Error: {r.status_code} - {r.text}")
        r.raise_for_status()
    return response