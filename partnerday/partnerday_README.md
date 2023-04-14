#### partnerday API Keys #### 
Emporix API: p6u6nNGf72UhE1pPp0LvW3KHeoPGCSGP, Secret: YAMCo7qQUePfXgPb
Storefront API: GxxLjU2ghG82EJchYF1QkBhefyUfEnbt
https://storefront.emporix.io/

cd /Users/nicolasberney/Library/CloudStorage/Dropbox/Emporix/Product/Github/internal-demo-data-importer

#### testpartner #### 
python3 main.py --apiUrl "https://api.emporix.io" --tenant partnerday --clientId p6u6nNGf72UhE1pPp0LvW3KHeoPGCSGP --clientSecret YAMCo7qQUePfXgPb --mapping "partnerday/partnerday_mapping_small.json" --products="partnerday/Power_Zone_Product_Import_Small - Products.csv" --categories="partnerday/Power_Zone_Product_Import_Small - Categories.csv" --prices="partnerday/Power_Zone_Product_Import_Small - Prices.csv" --availabilities="partnerday/Power_Zone_Product_Import_Small - Products.csv" --imports=products,categories,prices,availabilities

/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 clean.py --apiUrl "https://api.emporix.io" --tenant partnerday --clientId p6u6nNGf72UhE1pPp0LvW3KHeoPGCSGP --clientSecret YAMCo7qQUePfXgPb --mapping "partnerday/partnerday_mapping_small.json" --clean=products,prices,categories,availabilities
