#!/usr/bin/env python3

from importUtils import *

import requests
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.util.retry import Retry

retries = Retry(total=3, backoff_factor=1, status_forcelist=[400, 500, 502, 503, 504])
http = requests.Session()
http.mount("https://", HTTPAdapter(max_retries=retries))

brand_cache = {}

def import_reference(apiUrl, tenant, accessToken, attributeConfig, mapping, value, item):
  if attributeConfig['referenceType'] == "BRAND":
    return brand_reference(apiUrl, tenant, accessToken, attributeConfig, value)
  if attributeConfig['referenceType'] == "PRODUCT_TEMPLATE":
    return product_template_reference(apiUrl, tenant, accessToken, attributeConfig, mapping, value, item)

  else:
    return None

def brand_reference(apiUrl, tenant, accessToken, attributeConfig, brandName):
  if brandName in brand_cache:
    return brand_cache[brandName]

  r = http.get(f'{apiUrl}/brand/brands?q=name:{brandName}',
        headers = {'Authorization' : f'Bearer {accessToken}'})
  response = r.json()
  if response:
    brand_cache[brandName] = response[0]["id"]
    return response[0]["id"]
  else:
    if 'createIfMissing' in attributeConfig and attributeConfig['createIfMissing']:
      print(f"The brand {brandName} is missing. Will create the brand ...")
      payload = {
        "name" : brandName,
        "description": brandName
      }
      r2 = http.post(f'{apiUrl}/brand/brands',
              json = payload,
              headers = {'Authorization' : f'Bearer {accessToken}'})
      response2 = r2.json()
      brand_cache[brandName] = response2['id']
      return response2['id']
    else:
      print(f"Brand '{brandName}' does not exist and auto creation is not enabled")
      return None


def product_template_reference(apiUrl, tenant, accessToken, attributeConfig, mapping, templateName, item):
  r = http.get(f'{apiUrl}/product/{tenant}/product-templates?q=name:"{templateName}"',
        headers = {'Authorization' : f'Bearer {accessToken}'})
  response = r.json()
  if response:
    templateResponse = {
      "id" : response[0]["id"],
      "version" : response[0]['metadata']['version']
    }
    return templateResponse
  else:
    if 'createIfMissing' in attributeConfig and attributeConfig['createIfMissing']:
      payload = product_template_payload(mapping, templateName, item)
      r2 = http.post(f'{apiUrl}/product/{tenant}/product-templates',
        json = payload,
        headers = {'Authorization' : f'Bearer {accessToken}', 'Content-Language' : '*'})
      print(r2.json())
      return {
        "id" : r2.json()['id'],
        "version" : 1
      }
    else:
      print(f"Product template '{templateName}' does not exist and auto creation is not enabled")
      return None

def product_template_payload(mapping, templateName, item):
  payload = {
    "name" : { "en" : templateName},
    "attributes" : []
  }
  for attribute in mapping['products']['attributes']:
    if 'variantAttribute' in attribute and attribute['variantAttribute']:
      if item[attribute['csvKey']] != "":
        attributeType = "TEXT"
        if 'type' in attribute:
          if attribute['type'] == "NUMBER" or attribute['type'] == "DECIMAL":
            attributeType = "NUMBER"
          if attribute['type'] == "BOOLEAN":
            attributeType = "BOOLEAN"
        payloadAttribute = {
          "key" : attribute['emporixKey'],
          "name" : {"en" : attribute['emporixKey']},
          "type" : attributeType,
          "values" : [],
          "metadata" : {
            "variantAttribute" : True
          }
        }
        valueSeparator = ","
        if 'valueSeparator' in attribute:
          valueSeparator = attribute['valueSeparator']
        values = item[attribute['csvKey']].split(valueSeparator)
        for value in values:
          formattedValue = value
          if 'type' in attribute:
            if attribute['type'] == "NUMBER":
              formattedValue = int(value)
            if attribute['type'] == "DECIMAL":
              formattedValue = float(value)
            if attribute['type'] == "BOOLEAN":
              formattedValue = value == "TRUE"
          payloadAttribute['values'].append({"key" : formattedValue})
        payload['attributes'].append(payloadAttribute)
  return payload