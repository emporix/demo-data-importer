#!/usr/bin/env python3
import argparse
import json
import sys
import os
import csv
import traceback
import logging
from importUtils import *
import requests
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.util.retry import Retry


retries = Retry(total=3, backoff_factor=1, status_forcelist=[400, 500, 502, 503, 504])
http = requests.Session()
http.mount("https://", HTTPAdapter(max_retries=retries))


def main(argv=None):
    if argv is None:
        argv = sys.argv

    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('--apiUrl', metavar='apiUrl', type=str, required=True,
                               help='The Emporix base API URL. For example: --apiUrl=https://api.emporix.io')
    parent_parser.add_argument('--tenant', metavar='tenant', type=str, required=True,
                               help='Tenant name')
    parent_parser.add_argument('--clientId', metavar='clientId', type=str, required=True,
                               help='Client id')
    parent_parser.add_argument('--clientSecret', metavar='clientSecret', type=str, required=True,
                               help='Client secret')

    parent_parser.add_argument('--mapping', metavar='mapping', type=str, required=True,
                                   help='Path to mapping file')

    parent_parser.add_argument('--clean', metavar='import', type=str, required=True,
                                       help='Comma separated list of data to clean. For example: --clean=products,categories,prices')


    parser = argparse.ArgumentParser(description="Script for adding tenant to tenant list in configuration",
                                     parents=[parent_parser])

    args = parser.parse_args(argv[1:])
    apiUrl = args.apiUrl
    tenant = args.tenant
    clientId = args.clientId
    clientSecret = args.clientSecret
    clean = args.clean
    mapping = read_json(args.mapping)

    token = get_access_token(apiUrl, tenant, clientId, clientSecret)

    if "products" in clean:
      print("Starting products clean up...")
      clean_products(apiUrl, tenant, token)
    if "categories" in clean:
      print("Starting categories clean-up...")
      clean_categories(apiUrl, tenant, token, mapping)
    if "prices" in clean:
      print("Starting prices clean-up...")
      clean_prices(apiUrl, tenant, token)
    if "availabilities" in clean:
      print("Starting availabilities clean-up...")
      clean_availabilities(apiUrl, tenant, token, mapping)

def get_access_token(apiUrl, tenant, clientId, clientSecret):
    r = http.post(f'{apiUrl}/oauth/token',
      data = {'grant_type' : 'client_credentials', 'client_id' : clientId, 'client_secret' : clientSecret},
      headers = {'Content-Type' : 'application/x-www-form-urlencoded'})
    r.raise_for_status()
    json = r.json()
    return json['access_token']

def clean_products(apiUrl, tenant, token):
   clean_variant_products(apiUrl, tenant, token)
   clean_parent_variant_products(apiUrl, tenant, token)
   clean_basic_products(apiUrl, tenant, token)

def clean_basic_products(apiUrl, tenant, token):
  while True:
    r = http.get(f'{apiUrl}/product/{tenant}/products?pageSize=200', headers = {'Authorization' : f'Bearer {token}'})
    products = r.json()
    if not products:
      break
    for product in products:
      productId = product['id']
      print(f"deleting product: {productId}")
      try:
        deleteResponse = http.delete(f'{apiUrl}/product/{tenant}/products/{productId}?sort=', headers = {'Authorization' : f'Bearer {token}'})
        deleteResponse.raise_for_status()
      except Exception as e:
        print(f"Issue with deleting product {productId}")
        logging.error(traceback.format_exc())

def clean_variant_products(apiUrl, tenant, token):
  while True:
    r = http.get(f'{apiUrl}/product/{tenant}/products?q=productType:VARIANT&pageSize=200', headers = {'Authorization' : f'Bearer {token}'})
    products = r.json()
    if not products:
      break
    for product in products:
      productId = product['id']
      print(f"deleting product: {productId}")
      try:
        deleteResponse = http.delete(f'{apiUrl}/product/{tenant}/products/{productId}?sort=', headers = {'Authorization' : f'Bearer {token}'})
        deleteResponse.raise_for_status()
      except Exception as e:
        print(f"Issue with deleting product {productId}")
        logging.error(traceback.format_exc())

def clean_parent_variant_products(apiUrl, tenant, token):
  while True:
    r = http.get(f'{apiUrl}/product/{tenant}/products?q=productType:PARENT_VARIANT&pageSize=200', headers = {'Authorization' : f'Bearer {token}'})
    products = r.json()
    if not products:
      break
    for product in products:
      productId = product['id']
      print(f"deleting product: {productId}")
      try:
        deleteResponse = http.delete(f'{apiUrl}/product/{tenant}/products/{productId}?sort=', headers = {'Authorization' : f'Bearer {token}'})
        deleteResponse.raise_for_status()
      except Error:
        print(f"Issue with deleting product {productId}")
        logging.error(traceback.format_exc())


def clean_prices(apiUrl, tenant, token):
  while True:
    r = http.get(f'{apiUrl}/price/{tenant}/prices', headers = {'Authorization' : f'Bearer {token}', 'X-Version' : 'v2'})
    prices = r.json()
    if not prices:
      break
    for price in prices:

      priceId = price['id']
      print(f"deleting price: {priceId}")
      try:
        deleteResponse = http.delete(f'{apiUrl}/price/{tenant}/prices/{priceId}', headers = {'Authorization' : f'Bearer {token}',  'X-Version' : 'v2'})
        deleteResponse.raise_for_status()
      except Exception as e:
        print(f"Issue with deleting price {priceId}")
        logging.error(traceback.format_exc())

def clean_categories(apiUrl, tenant, token, mapping):
  while True:
    r = http.get(f'{apiUrl}/category/{tenant}/categories', headers = {'Authorization' : f'Bearer {token}', 'X-Version' : 'v2'})
    categories = r.json()
    if not categories:
      break
    for category in categories:

      categoryId = category['id']
      print(f"deleting category: {categoryId}")
      try:
        deleteResponse = http.delete(f'{apiUrl}/category/{tenant}/categories/{categoryId}?withSubcategories=true', headers = {'Authorization' : f'Bearer {token}',  'X-Version' : 'v2'})
        deleteResponse.raise_for_status()
      except Exception as e:
        print(f"Issue with deleting category {categoryId}")
        logging.error(traceback.format_exc())
  clean_root_category_to_catalog(apiUrl, tenant, token, mapping)


def clean_availabilities(apiUrl, tenant, token, mapping):
  for site in mapping['availabilities']['sites']:
    clean_availabilities_for_site(apiUrl, tenant, token, site['siteCode'])


def clean_availabilities_for_site(apiUrl, tenant, token, site):
  while True:
    r = http.get(f'{apiUrl}/availability/{tenant}/availability?site={site}', headers = {'Authorization' : f'Bearer {token}'})
    availabilities = r.json()
    if not availabilities:
      break
    for availability in availabilities:

      availabilityId = availability['id']
      productId = availability['productId']
      print(f"deleting availability: {availabilityId}")
      try:
        deleteResponse = http.delete(f'{apiUrl}/availability/{tenant}/availability/{productId}?site={site}', headers = {'Authorization' : f'Bearer {token}'})
        deleteResponse.raise_for_status()
      except Exception as e:
        print(f"Issue while deleting availability {availabilityId}")
        logging.error(traceback.format_exc())

def clean_root_category_to_catalog(apiUrl, tenant, accessToken, mapping):
    print("Cleaning root category assignments")
    if 'catalog' in mapping['categories']:
      catalogId = mapping['categories']['catalog']
      r = http.get(f'{apiUrl}/catalog/{tenant}/catalogs/{catalogId}', headers = {'Authorization' : f'Bearer {accessToken}'})
      currentCatalog = r.json()
      currentCatalog['categoryIds'] = []
      r2 = http.put(f'{apiUrl}/catalog/{tenant}/catalogs/{catalogId}',
       json = currentCatalog,
       headers = {'Authorization' : f'Bearer {accessToken}'})


if __name__ == '__main__':
    sys.exit(main() or 0)
