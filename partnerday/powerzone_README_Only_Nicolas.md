#### Only for Nicolas #### 
cd /Users/nicolasberney/Library/CloudStorage/Dropbox/Emporix/Product/Github/demo-data-importer

#### uniform #### 
python3 main.py --apiUrl "https://api.emporix.io" --tenant uniform --clientId bSgXYJMfCe6zf9ZPisGX4HBqy7xIpeeA --clientSecret Rn52I8AwMtlGAnMI --mapping "powerzone/powerzone_mapping.json" --products="powerzone/Power_Zone_Product_Import_Small - Products.csv" --categories="powerzone/Power_Zone_Product_Import_Small - Categories.csv" --prices="powerzone/Power_Zone_Product_Import_Small - Prices.csv" --availabilities="powerzone/Power_Zone_Product_Import_Small - Products.csv" --imports=products,categories,prices,availabilities

python3 clean.py --apiUrl "https://api-dev.emporix.io" --tenant uniform --clientId bSgXYJMfCe6zf9ZPisGX4HBqy7xIpeeA --clientSecret Rn52I8AwMtlGAnMI --mapping "powerzone/powerzone_mapping.json" --clean=products,prices,categories,availabilities 
#### end uniform ####

#### mrworke1rstage #### 
python3 main.py --apiUrl "https://api-dev.emporix.io" --tenant mrworker1stage --clientId nW6jls8GdO16GYUEon9wraH6Ebvpnhjv --clientSecret rEyAynVt70FDalGO --mapping "mrworke1rstage/mrworke1rstage_mapping_small.json" --products="mrworke1rstage/Power_Zone_Product_Import_Small - Products.csv" --categories="mrworke1rstage/Power_Zone_Product_Import_Small - Categories.csv" --prices="mrworke1rstage/Power_Zone_Product_Import_Small - Prices.csv" --availabilities="mrworke1rstage/Power_Zone_Product_Import_Small - Products.csv" --imports=products,categories,prices,availabilities

python3 clean.py --apiUrl "https://api-dev.emporix.io" --tenant mrworker1stage --clientId nW6jls8GdO16GYUEon9wraH6Ebvpnhjv --clientSecret rEyAynVt70FDalGO --mapping "mrworke1rstage/mrworke1rstage_mapping_small.json" --clean=products,prices,categories,availabilities
#### end mrworke1rstage #### 

#### mrworkerstage #### 
# python3 main.py --apiUrl "https://api-dev.emporix.io" --tenant mrworkerstage --clientId kxE1E6Y6nEPGl3osSPItKjGGKpOeau2M --clientSecret JGI7JT9kFF2oGl66 --mapping "powerzone/powerzone_mapping.json" --products="powerzone/Power_Zone_Product_Import - Products.csv" --categories="powerzone/Power_Zone_Product_Import - Categories.csv" --prices="powerzone/Power_Zone_Product_Import - Prices.csv" --availabilities="powerzone/Power_Zone_Product_Import - Products.csv" --imports=products,categories,prices,availabilities

# python3 clean.py --apiUrl "https://api-dev.emporix.io" --tenant mrworkerstage --clientId kxE1E6Y6nEPGl3osSPItKjGGKpOeau2M --clientSecret JGI7JT9kFF2oGl66 --mapping "powerzone/powerzone_mapping.json" --clean=products,prices,categories,availabilities 
#### end mrworkerstage #### 

