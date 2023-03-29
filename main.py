#!/usr/bin/env python3
import argparse
import json
import sys
import os
import csv
from importUtils import *
from importProducts import *
from importCategories import *
from importPrices import *
from importAvailabilities import *
from importReferences import *
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

    parent_parser.add_argument('--imports', metavar='import', type=str, required=True,
                                       help='Comma separated list of data to import. For example: --import=products,categories,prices,availabilities')

    parent_parser.add_argument('--mapping', metavar='mapping', type=str, required=True,
                                   help='Path to mapping file')

    parent_parser.add_argument('--products', metavar='products', type=str, required=True,
                                   help='Path to products csv file')

    parent_parser.add_argument('--categories', metavar='categories', type=str, required=False,
                                       help='Path to categories csv file')

    parent_parser.add_argument('--prices', metavar='prices', type=str, required=False,
                                       help='Path to prices csv file')

    parent_parser.add_argument('--availabilities', metavar='availabilities', type=str, required=False,
                                       help='Path to availabilities csv file')

    parser = argparse.ArgumentParser(description="Script for adding tenant to tenant list in configuration",
                                     parents=[parent_parser])

    args = parser.parse_args(argv[1:])
    apiUrl = args.apiUrl
    tenant = args.tenant
    clientId = args.clientId
    clientSecret = args.clientSecret
    mapping = args.mapping
    imports = args.imports
    products = args.products
    categories = args.categories
    prices = args.prices
    availabilities = args.availabilities

    token = get_access_token(apiUrl, tenant, clientId, clientSecret)

    if "products" in imports:
      print("Starting products import...")
      import_products(mapping, products, apiUrl, tenant, token)
    if "categories" in imports:
      print("Starting categories import...")
      import_categories(mapping, products, categories, apiUrl, tenant, token)
    if "prices" in imports:
      print("Starting prices import...")
      import_prices(mapping, products, prices, apiUrl, tenant, token)
    if "availabilities" in imports:
      print("Starting availabilities import...")
      import_availabilities(mapping, products, availabilities, apiUrl, tenant, token)


def get_access_token(apiUrl, tenant, clientId, clientSecret):
    r = http.post(f'{apiUrl}/oauth/token',
      data = {'grant_type' : 'client_credentials', 'client_id' : clientId, 'client_secret' : clientSecret},
      headers = {'Content-Type' : 'application/x-www-form-urlencoded'})
    r.raise_for_status()
    json = r.json()
    return json['access_token']

if __name__ == '__main__':
    sys.exit(main() or 0)
