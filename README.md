# Import script for product, categories and prices data

Before running the script with the product examples in the Google Sheets, you need to pre-set the tenant with multiple values. You can use the Postman collection to setup the tenant automatically: powerzone/postman/*

How to run the script:

```shell
python3 main.py  --apiUrl {Emporix API URL} --tenant {TENANT} --clientId {CLIENT_ID} --clientSecret {CLIENT_SECRET} --mapping "powerzone/powerzone_mapping_small.json" --products="powerzone/Power_Zone_Product_Import_Small - Products.csv" --categories="powerzone/Power_Zone_Product_Import_Small - Categories.csv" --prices="powerzone/Power_Zone_Product_Import_Small - Prices.csv" --availabilities="powerzone/Power_Zone_Product_Import_Small - Products.csv" --imports=products,categories,prices,availabilities 
```

How to clean up data:
```shell
python3 clean.py  --apiUrl {Emporix API URL} --tenant {TENANT} --clientId {CLIENT_ID} --clientSecret {CLIENT_SECRET} --mapping "powerzone/powerzone_mapping_small.json" --clean=products,prices,categories,availabilities
```

In order to run the script the following prerequisite steps are required:
### CSV data file preparation

#### Products Tab
csv file for product entity can have any structure. Nevertheless, it needs to have the following columns:
* a column for a product type (available values: BASIC, PARENT_VARIANT and VARIANT)
* a column for product template id (valid for PARENT_VARIANT)
* a column for product template version (valid for PARENT_VARIANT)
* a column for product parent id (valid for VARIANT)
* a columns for product tax configuration (one column for each supported site/country)
* a column for variant attributes (PARENT_VARIANT should contain all possible values in the cell, VARIANT should have single value in the cell)

As a referral example, the following google sheet tab (Products) can be used: https://docs.google.com/spreadsheets/d/1EIvwUbtks9uKCl6tTcEFtHa8zzq5K04wehz3-E-CTNI/edit?usp=sharing

#### Categories Tab
csv file for category entity should have the following columns:
* a column with a product ID (it's used for product assignment)
* a column with category tree for a particular product assignment (for example `HOME PAGE > FESTOOL > CLOTHING AND MERCHANDISING > CLOTHING`)

As a referral example, the following google sheet tab (Categories) can be used: https://docs.google.com/spreadsheets/d/1EIvwUbtks9uKCl6tTcEFtHa8zzq5K04wehz3-E-CTNI/edit?usp=sharing

#### Prices Tab
csv file for price entity should have the following columns:
* a column with a product ID (it's used for a price -> product assignment)
* separate columns for each price value (for example: `US Price Tier 1 - 0 pc`, `US Price Tier 2 - 10 pc`, `FR Price Tier 1 - 0 pc` etc)

As a referral example, the following google sheet tab (Prices) can be used: https://docs.google.com/spreadsheets/d/1EIvwUbtks9uKCl6tTcEFtHa8zzq5K04wehz3-E-CTNI/edit?usp=sharing

### NOTE
* All the google sheets tabs (Products, Categories & Prices) have to be exported into csv file in order to run the import!
* Another small example product (Basic, Variant and Bundle) google sheet import file: https://docs.google.com/spreadsheets/d/1bqFZerL5Nfy49vzjumekmWUWDWoSaJgruE5iGaUtzZY/edit?usp=sharing
* The script doesn't support yet the product catalog updates. Please use clean.py and re-import the catalog

### Configuration (mapping) file
* As a reference have a look at `powerzone/powerzone_mapping.json`.
* You need to replace with the Catalog ID where all the Top categories will be attached to: "catalog" : "<The catalog ID needs to exist>". To get the catalog ID, click on this URL and then on the catalog: https://dashboard.emporix.io/apps/management/catalogs/

### Mapping:
The configuration has 5 main parts (products, images, categories, prices and availabilities).
Empty template of the mapping has the following structure:
```json
{
  "products": {
    "identifier" : {
      "csvKey": ""
    },
    "parentIdentifier" : {
      "csvKey": ""
    },
    "productType" : {
      "csvKey" : ""
    },
    "attributes": [
      {
        "csvKey": "",
        "emporixKey": "id"
      }
    ]
  },
  "images" : {
    "directoryPath" : "",
    "columns" : []
  },
  "categories" : {
    "catalog" : "<The catalog ID needs to exist>",
    "categoryTree" : {
      "csvKey" : "",
      "separator" : ""
    },
    "productAssignment" : {
      "csvKey" : ""
    }
  },
  "prices" : {
    "productIdentifier" : {
      "csvKey" : ""
    },
    "sites" : [
      {
        "siteCode": "",
        "currency": "",
        "location": "",
        "tiers": [
          {
            "csvKey": ""
          }
        ]
      }
    ]
  },
  "availabilities" : {
    "productIdentifier" : {
      "csvKey" : ""
    },
    "sites" : [
      {
        "siteCode" : "",
        "csvKey" : ""
      }
    ]
  }
}
```