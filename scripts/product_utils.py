import json
import random
import os
import io
from prestapyt import PrestaShopWebServiceDict
from category_utils import get_category_and_subcategory
from concurrent.futures import ThreadPoolExecutor, as_completed

# API credentials and URL
api_url = 'http://localhost:8080/api/'
api_key = 'JRUL76DYZHM8KLUS7SZ244PF179G9LI8'

def get_template():
    prestashop = PrestaShopWebServiceDict(api_url, api_key)
    product_template = prestashop.get("products", options={"schema": "blank"})
    
    del product_template["product"]["associations"]["combinations"]
    del product_template["product"]["position_in_category"]
    
    return product_template

def delete_product(product_id, left):
    prestashop = PrestaShopWebServiceDict(api_url, api_key)

    try:
        prestashop.delete("products", product_id)
        print(f"Deleted product with ID {product_id}. Left to delete: {left}")
    except Exception as e:
        print(f"Error occured while deleting product with ID {product_id}: {e}")


def delete_products():
    prestashop = PrestaShopWebServiceDict(api_url, api_key)

    products = prestashop.get("products")["products"]
    if products == '' or len(products["product"]) == 0:
        print("No products to delete.")
        return
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = []
        left = len(products["product"])
        for product in products["product"]:
            product_id = product["attrs"]["id"]
            futures.append(executor.submit(delete_product, product_id, left))
            left-=1

        for future in as_completed(futures):
            future.result()

def set_stock(prestashop, product_id: int):
    try:
        available_id = prestashop.search('stock_availables', options={'filter[id_product]': product_id})[0]
        stock_available_schema = prestashop.get('stock_availables', available_id)
        stock_available_schema['stock_available']['quantity'] = random.randint(0, 10)
        prestashop.edit('stock_availables', stock_available_schema)
        print(f'Stock added for {product_id}')
    except Exception as e:
        print(f'Error setting stock for {product_id}.')
        
def upload_image(prestashop, product_id: int, product):
    imgpath = product['ImgPath']
    if 'No image' in imgpath:
        print(f'No image for {product_id}')
        return
    
    imgpath = os.path.basename(imgpath.replace("\\", "/"))
    imgpath = os.path.join('..', 'scraping_results', 'img', imgpath)
    
    fd = io.open(imgpath, 'rb')
    content = fd.read()
    fd.close()
    try:
        prestashop.add(f'images/products/{product_id}', files=[('image', os.path.basename(imgpath), content)])
        print(f'Added image for {product_id}')
    except Exception as e:
        print(f'Failed to add image for {product_id}')

def add_product(prestashop, product, category_id: int, subcategory_id: int, product_template, leftToUpload):
    product_template["product"]["name"]["language"]["value"] = product["Title"]
    
    product_template["product"]["id_category_default"] = category_id
    
    product_template["product"]["id_tax_rules_group"] = 1
    product_template["product"]["price"] = round(product["Price"] / 1.23, 2)
    
    product_template["product"]["active"] = 1
    product_template["product"]["state"] = 1
    product_template["product"]["available_for_order"] = 1
    product_template["product"]["minimal_quantity"] = 1
    product_template["product"]["show_price"] = 1
    
    product_template["product"]["meta_title"]["language"]["value"] = product["Manufacturer"]
    
    product_template["product"]["link_rewrite"]["language"]["value"] = product["Manufacturer"].replace(" ", "-").lower()
    
    categories_list = [{'id': 2}, {'id': category_id}, {'id': subcategory_id}]
    
    product_template["product"]["associations"]["categories"] = {"category": categories_list}
    
    product_template["product"]["weight"] = round(random.uniform(0.1, 0.4), 2)
    product_template["product"]["description_short"]["language"]["value"] = product["Title"]
    
    product_template["product"]["description"]["language"]["value"] = product["Description"]

    
    product_id = prestashop.add("products", product_template)["prestashop"]["product"]["id"]

    print(f"Product {product_id} added. Products left to add: {leftToUpload}")
    
    set_stock(prestashop, product_id)
    upload_image(prestashop, product_id, product)


def add_product_to_category(product, categories_dictionary, prestashop, template, leftToUpload):
    # Użyj tego słownika, żeby wsadzić produkt do odpowiedniej kategorii
    category_id, subcategory_id = get_category_and_subcategory(categories_dictionary, product["CategoryName"], product["SubcategoryName"])
    add_product(prestashop, product, category_id, subcategory_id, template, leftToUpload)

def load_products(categories_dictionary: dict):
    prestashop = PrestaShopWebServiceDict(api_url, api_key)

    products = prestashop.get("products")["products"]
    if products != '' and len(products["product"]) > 0:
        print("Products already loaded.")
        return

    with open("../scraping_results/serialization/products.json", 'r', encoding='utf-8') as file:
        data = json.load(file)

    template = get_template()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = []
        leftToUpload = len(data)
        for product in data:
            futures.append(executor.submit(add_product_to_category, product, categories_dictionary, prestashop, template, leftToUpload))
            leftToUpload -= 1
        for future in as_completed(futures):
            future.result()

            
