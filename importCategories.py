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


def import_categories(mappingFile, productCsvFile, csvFile, apiUrl, tenant, accessToken):
    mapping = read_json(mappingFile)
    csv_to_json(csvFile, "tmp/categories.json")
    database = read_json("tmp/categories.json")
    csv_to_json(productCsvFile, "tmp/products.json")
    productDatabase = read_json("tmp/products.json")
    persistedCategories = create_category_tree(apiUrl, tenant, accessToken, mapping, database)
    create_category_assignments(apiUrl, tenant, accessToken, mapping, database, productDatabase, persistedCategories)

def create_category_tree(apiUrl, tenant, accessToken, mapping, database):
    createdCategories = {}
    categoriesTrees = find_all_categories_trees(mapping, database)
    for key in categoriesTrees:
      create_categories(apiUrl, tenant, accessToken, mapping, key, categoriesTrees[key], createdCategories)
    return createdCategories

def find_all_categories_trees(mapping, database):
    categoriesWithoutDuplicates = {}
    for item in database:
      categoriesWithoutDuplicates[item[mapping['categories']['categoryTree']['csvKey']]] = item
    return categoriesWithoutDuplicates

def create_categories(apiUrl, tenant, accessToken, mapping, categoryTree, categoryRow, createdCategories):
    categories = categoryTree.split(mapping['categories']['categoryTree']['separator'])
    parent = None
    for category in categories:
      if category not in createdCategories:
        categoryNames = create_localized_names(mapping, category, categoryRow, categories.index(category))
        payload = prepare_category_payload(parent, categoryNames)
        persistedCategory = persist_category(apiUrl, tenant, accessToken, payload)
        createdCategories[category] = { 'id' : persistedCategory['id'], 'categoryTree' : categoryTree }
        if parent == None:
          assign_root_category_to_catalog(apiUrl, tenant, accessToken, mapping, persistedCategory['id'])
        parent = persistedCategory['id']
      else:
        parent = createdCategories[category]['id']

def create_localized_names(mapping, categoryName, categoryRow, index):
    localizedName = {}
    if 'localizedNames' in mapping['categories']['categoryTree']:
       for lang in mapping['categories']['categoryTree']['localizedNames']:
          csvColumnKey = mapping['categories']['categoryTree']['localizedNames'][lang]
          localizedTree = categoryRow[csvColumnKey].split(mapping['categories']['categoryTree']['separator'])
          if len(localizedTree) > index:
            localizedName[lang] = localizedTree[index]
    else:
      localizedName["en"] = categoryName
    return localizedName

def assign_root_category_to_catalog(apiUrl, tenant, accessToken, mapping, categoryId):
    if 'catalog' in mapping['categories']:
      catalogName = mapping['categories']['catalog']
      r = http.get(f'{apiUrl}/catalog/{tenant}/catalogs?name={catalogName}', headers = {'Authorization' : f'Bearer {accessToken}'})
      response = r.json()
      if response:
        catalogId = response[0]["id"]
      else:
        raise Exception(f"Error: The main category {catalogName} doesn't exist. Please create it or change the mapping file accordingly.")

      r = http.get(f'{apiUrl}/catalog/{tenant}/catalogs/{catalogId}', headers = {'Authorization' : f'Bearer {accessToken}'})
      response = r.json()
      if  r.status_code == 404:
        print("\n\nError occurred while assigning the category to catalog. Details: {}\n\n".format(response))
        r.raise_for_status()
      if 'categoryIds' not in response:
        response['categoryIds'] = []
      response['categoryIds'].append(categoryId)
      r2 = http.put(f'{apiUrl}/catalog/{tenant}/catalogs/{catalogId}',
       json = response,
       headers = {'Authorization' : f'Bearer {accessToken}'})
      r2.raise_for_status()
      if r2.status_code == 400:
        print("\n\nError occurred while assigning the category to catalog. Details: {}\n\n".format(r2.json()))


def create_category_assignments(apiUrl, tenant, accessToken, mapping, database, productDatabase, persistedCategories):
   for item in database:
      tree = item[mapping['categories']['categoryTree']['csvKey']]
      leaf = tree.split(mapping['categories']['categoryTree']['separator'])[-1]
      sku = item[mapping['categories']['productAssignment']['csvKey']]
      productId = construct_product_id(productDatabase, mapping, sku)
      if productId == None:
        print(f"Skipping category assignment creation for {sku} because the identifier does not exist in product database")
      else:
        payload = prepare_category_assignment_payload(productId)
        persistedCategory = persistedCategories[leaf]
        persist_category_assignment(apiUrl, tenant, accessToken, persistedCategory['id'], payload)

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

def prepare_category_payload(parentId, localizedNames):
  return {
      "parentId" : parentId,
      "localizedName" : localizedNames,
      "published" : True
  }

def prepare_category_assignment_payload(productId):
  return {
      "ref" : {
        "id" : productId,
        "type" : "PRODUCT"
      }
  }

def persist_category(apiUrl, tenant, accessToken, payload):
    r = http.post(f'{apiUrl}/category/{tenant}/categories?publish=true',
      json = payload,
      headers = {'Authorization' : f'Bearer {accessToken}', 'X-Version' : 'v2', 'Content-Language': '*'})
    response = r.json()
    if r.status_code == 400:
      print("\n\nError occurred during category creation")
      print(response)
      print("for the following payload")
      print("{}\n\n".format(payload))
    else:
      print("Created category for the following payload: {}".format(payload))
    return response

def persist_category_assignment(apiUrl, tenant, accessToken, categoryId, payload):
    r = http.post(f'{apiUrl}/category/{tenant}/categories/{categoryId}/assignments',
      json = payload,
      headers = {'Authorization' : f'Bearer {accessToken}', 'X-Version' : 'v2'})
    response = r.json()
    if r.status_code == 400:
      print("\n\nError occurred during category assignment creation")
      print(response)
      print("for the following payload")
      print("{}\n\n".format(payload))
    else:
      print("Created category assignment {} for product={} and category={}".format(response, categoryId, payload["ref"]["id"]))
    return response
