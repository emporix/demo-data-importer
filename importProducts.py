#!/usr/bin/env python3
import argparse
import json
import sys
import os
import csv
import mimetypes
from time import sleep
import time
from importUtils import *
from importReferences import *
from pprint import pprint
import requests
from concurrent.futures import ThreadPoolExecutor
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.util.retry import Retry


retries = Retry(total=3, backoff_factor=1, status_forcelist=[400, 500, 502, 503, 504])
http = requests.Session()
http.mount("https://", HTTPAdapter(max_retries=retries))


def import_products(mappingFile, csvFile, apiUrl, tenant, accessToken):
    mapping = read_json(mappingFile)
    csv_to_json(csvFile, "tmp/products.json")
    database = read_json("tmp/products.json")
    batchSize = 500
    numberOfThreads = 10
    if 'config' in mapping['products']:
      if 'batchSize' in mapping['products']['config']:
        batchSize = mapping['products']['config']['batchSize']
      if 'numberOfThreads' in mapping['products']['config']:
        numberOfThreads = mapping['products']['config']['numberOfThreads']
    batches = prepare_batches(database, batchSize)
    batchRequests = []
    for batch in batches:
      batchRequest = []
      for item in batch:
        payload = prepare_product_payload(apiUrl, tenant, accessToken, mapping, item)
        batchRequest.append(payload)
      wrapper = {"payload" : batchRequest, "tenant" : tenant, "accessToken" : accessToken, "apiUrl" : apiUrl}
      batchRequests.append(wrapper)
    with ThreadPoolExecutor(max_workers=numberOfThreads) as pool:
      list(pool.map(save_batch_product, batchRequests))
    imageBatchRequests = []
    for item in database:
      wrapper = {"apiUrl" : apiUrl, "tenant" : tenant, "accessToken" : accessToken, "mapping" : mapping, "item" : item}
      imageBatchRequests.append(wrapper)
    with ThreadPoolExecutor(max_workers=numberOfThreads) as pool:
      list(pool.map(upload_images_in_bulk, imageBatchRequests))

def save_batch_product(wrapper):
  save_products(wrapper['apiUrl'], wrapper['tenant'], wrapper['accessToken'], wrapper['payload'])

def prepare_batches(list, size):
  for i in range(0, len(list), size):
    yield list[i:i+size]

def prepare_product_payload(apiUrl, tenant, token, mappingConfig, itemLine):
    payload = {}
    payload['published'] = True
    payload['metadata'] = {
      "overridden" : ['name', 'description'],
      "mixins" : {
        "productCustomAttributes" : "https://res.cloudinary.com/saas-ag/raw/upload/schemata/productCustomAttributesMixIn.v29.json"
      }
    }

    attributes = mappingConfig['products']['attributes']
    productType = itemLine['Product type']
    for attribute in attributes:
      if attribute["csvKey"] in itemLine:
        attributeValue = itemLine[attribute["csvKey"]]
        attribute_value_injector(apiUrl, tenant, token, productType, payload, attribute, mappingConfig, attributeValue, itemLine)
    adjust_payload(payload)
    return payload

def attribute_value_injector(apiUrl, tenant, token, productType, payload, attribute, mapping, value, item):
    if value != "":
      if attribute['emporixKey'].startswith("mixins"):
        payload['metadata']['overridden'].append(attribute['emporixKey'])
      if productType == "BUNDLE" and 'bundle' in attribute and attribute['bundle']:
          inject_bundle_attribute(productType, payload, attribute, value)
      elif 'variantAttribute' in attribute and attribute['variantAttribute'] == True:
        if productType == "PARENT_VARIANT":
          inject_variant_attribute_for_variant_parent(productType, payload, attribute, value)
        else:
          inject_variant_attribute_for_variant(productType, payload, attribute, value)
      else:
         inject_standard_attribute(apiUrl, tenant, token, productType, payload, attribute, mapping, value, item)


def inject_standard_attribute(apiUrl, tenant, token, productType, payload, attribute, mapping, value, item):
    keys = attribute['emporixKey'].split(".")
    nestedObject = payload
    for key in keys:
      if key == keys[-1]:
        if 'type' in attribute and attribute['type'] == "REFERENCE":
          nestedObject[key] = import_reference(apiUrl, tenant, token, attribute, mapping, value, item)
        elif 'type' in attribute and attribute['type'] == "NUMBER":
          nestedObject[key] = int(value)
        elif 'type' in attribute and attribute['type'] == "DECIMAL":
          nestedObject[key] = float(value)
        elif 'type' in attribute and attribute['type'] == "BOOLEAN":
          nestedObject[key] = value == "TRUE"
        elif 'type' in attribute and attribute['type'] == "ARRAY":
          nestedObject[key] = json.loads(value.replace("'", '"'))
        else:
          nestedObject[key] = value
      else:
        if key not in nestedObject:
          nestedObject[key] = {}
      nestedObject = nestedObject[key]


def inject_variant_attribute_for_variant_parent(productType, payload, attribute, values):
    if 'variantAttributes' not in payload:
      payload['variantAttributes'] = {}
    payload['variantAttributes'][attribute['emporixKey']] = []
    separator = ","
    if 'valueSeparator' in attribute:
      separator = attribute['valueSeparator']
    splitValues = values.split(separator)
    for value in splitValues:
      typedValue = value
      if 'type' in attribute and attribute['type'] == "NUMBER":
        typedValue = int(value)
      payload['variantAttributes'][attribute['emporixKey']].append({'key' : typedValue})


def inject_variant_attribute_for_variant(productType, payload, attribute, value):
    try:
      mixins = payload['mixins']
    except Exception as e:
      print("\n\nThe following error occurred:")
      print(str(e) + ". The Brand name maybe missing in the CSV for the product")
      print("\n\nfor the following request:")
      print(json.dumps(payload))
      sys.exit(1)  # Terminate the script

    if 'productVariantAttributes' not in mixins:
      mixins['productVariantAttributes'] = {}
    typedValue = value
    if 'type' in attribute and attribute['type'] == "NUMBER":
      typedValue = int(value)
    mixins['productVariantAttributes'][attribute['emporixKey']] = typedValue

def inject_bundle_attribute(productType, payload, attribute, value):
    payload['bundledProducts'] = []
    print("value before split")
    print(value)
    productsAndQuantities = value.split(",")
    for productAndQuantity in productsAndQuantities:
      v = productAndQuantity.split(":")
      payload['bundledProducts'].append({
        "productId" : v[0],
        "amount" : v[1]
      })


def adjust_payload(payload):
    if payload['productType'] == "VARIANT":
      id = payload['id']
      payload['id'] = payload['parentVariantId'] + "--" + id

def save_products(apiUrl, tenant, token, payload):
    print("Saving batch product...")
    r = http.post(f'{apiUrl}/product/{tenant}/products/bulk?skipVariantGeneration=true',
      json = payload,
      headers = {'Authorization' : f'Bearer {token}', 'tenant' : tenant})
    if r.status_code == 400:
      print("\n\nThe following error occurred:")
      print(r.json())
      print("\n\nfor the following request:")
      print(json.dumps(payload))
    if r.status_code == 207:
      response = r.json()
      for item in response:
        print(item)
    if r.status_code not in (200, 201, 204, 207,409):
        print(f"Error: {r.status_code} - {r.text}")
        r.raise_for_status()
    return response

def upload_images_in_bulk(wrapper):
  upload_images(wrapper['apiUrl'], wrapper['tenant'], wrapper['accessToken'], wrapper['mapping'], wrapper['item'])

def upload_images(apiUrl, tenant, accessToken, mapping, item):
    id = item[mapping['products']['identifier']['csvKey']]
    for imageColumn in mapping['images']['columns']:
      try:
        upload_image(apiUrl, tenant, accessToken, id, mapping, item, imageColumn)
      except FileNotFoundError:
        print("File does not exist")


def upload_image(apiUrl, tenant, accessToken, id, mapping, item, imageColumn):
    if item[imageColumn] != "":
      imagePath = mapping['images']['directoryPath'] + "/" + item[imageColumn]
      print("Uploading image: " + imagePath + " for item: " + id)
      payload = {
          "type": "BLOB",
          "details": {
              "filename": item[imageColumn],
              "mimeType": mimetypes.guess_type(imagePath)[0]
          },
          "access": "PUBLIC",
          "refIds": [
              {
                    "type": "PRODUCT",
                    "id": id
              }
          ]
      }
      multipart_form_data = (
          ('file', (item[imageColumn], open(imagePath, 'rb'))),
          ('body', (None, json.dumps(payload)))
      )
      headers = {'Authorization' : f'Bearer {accessToken}'}
      r1 = http.post(f'{apiUrl}/media/{tenant}/assets', headers=headers, data={}, files=multipart_form_data)
      r1.raise_for_status()