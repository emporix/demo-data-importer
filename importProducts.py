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
    for item in database:
       payload = prepare_product_payload(apiUrl, tenant, accessToken, mapping, item)
       id = save_product(apiUrl, tenant, accessToken, payload)['id']
       upload_images(apiUrl, tenant, accessToken, id, mapping, item)

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


def save_product(apiUrl, tenant, token, payload):
    print("Saving product {}".format(payload['code']))
    r = http.post(f'{apiUrl}/product/{tenant}/products',
      json = payload,
      headers = {'Authorization' : f'Bearer {token}', 'tenant' : tenant})
    time.sleep(0.6) # Need more time to validate the Mixins with a long list of Mixins
    if r.status_code == 400:
      print("\n\nThe following error occurred:")
      print(r.json())
      print("\n\nfor the following request:")
      print(json.dumps(payload))
    time.sleep(0.6) # Need more time to validate the Mixins with a long list of Mixins
    response = r.json()
    time.sleep(0.6) # Need more time to validate the Mixins with a long list of Mixins
    if r.status_code not in (200, 201, 204):
        print(f"Error: {r.status_code} - {r.text}")
        r.raise_for_status()
    if payload['productType'] == "PARENT_VARIANT":
      remove_autogenerated_variants(apiUrl, tenant, token, response['id'])
    return response


def remove_autogenerated_variants(apiUrl, tenant, token, parentId):
    sleep(5)
    r = http.get(f'{apiUrl}/product/{tenant}/products?q=parentVariantId:{parentId}&pageSize=1000',
      headers = {'Authorization' : f'Bearer {token}', 'tenant' : tenant})
    if r.status_code not in (200, 201, 204):
        print(f"Error: {r.status_code} - {r.text}")
        r.raise_for_status()
    variants = r.json()
    for v in variants:
      variantId = v['id']
      deleteResponse = http.delete(f'{apiUrl}/product/{tenant}/products/{variantId}', headers = {'Authorization' : f'Bearer {token}'})
      deleteResponse.raise_for_status()


def upload_images(apiUrl, tenant, accessToken, id, mapping, item):
    for imageColumn in mapping['images']['columns']:
      try:
        upload_image(apiUrl, tenant, accessToken, id, mapping, item, imageColumn)
      except FileNotFoundError:
        print("File does not exist")


def upload_image(apiUrl, tenant, accessToken, id, mapping, item, imageColumn):
    if item[imageColumn] != "":
      imagePath = mapping['images']['directoryPath'] + "/" + item[imageColumn]
      print("Uploading image: " + imagePath)
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
      response1 = r1.json()
      r1.raise_for_status()