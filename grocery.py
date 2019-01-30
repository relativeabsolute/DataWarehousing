import sys
import sqlite3
import csv
import re
import random
import datetime


def manage_tables(cursor):
    cursor.execute('''DROP TABLE IF EXISTS products''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS products
        (Manufacturer TEXT, ProductName TEXT, Size REAL, SizeUnit TEXT, ItemType TEXT, SKU INT, BasePrice REAL)''')
    # TODO: replicate above two calls for sales_record table


# c is database cursor
# filename is name of file to import products from
def import_products(c, filename):
    with open(filename, 'r', newline='') as file_handle:
        reader = csv.DictReader(file_handle, delimiter='|', quoting=csv.QUOTE_NONE)
        rows = []
        for row in reader:
            result = {}
            for key in row.keys():
                if key == 'Size':
                    print(row[key])
                    match = re.match(r'(\w*[\./]?\w+)\s*(\w+)?', row[key])
                    # not going to error check...
                    groups = match.groups()
                    print(str(groups))
                    result['SizeUnit'] = ''
                    if groups[1] is not None:
                        result['SizeUnit'] = groups[1]
                    result['Size'] = eval(groups[0])
                elif key == 'BasePrice':
                    match = re.match(r'\$(.+)', row[key])
                    result['BasePrice'] = eval(match.group(1))
                else:
                    result[key] = row[key]
            rows.append(result)
        c.executemany('''INSERT INTO products VALUES (:Manufacturer, :ProductName, :Size, :SizeUnit,
            :ItemType, :SKU, :BasePrice)''', rows)


def get_partial_sale(c, type_name, price_multiplier):
    record = get_item_type(c, type_name)
    return {'SKU': record[5], 'SalePrice': record[6] * price_multiplier}


# get a random row that is the given type
def get_item_type(c, type_name):
    c.execute('''SELECT * FROM products where ItemType = ?''', [type_name])
    rows = c.fetchall()
    return rows[random.randrange(0, len(rows))]


# returns partial (SKU and sale price) sales records of items bought with probability
def do_probability_sales(c, price_multiplier):
    result = []
    probabilities = [{ 'type': 'Milk', 'prob': 0.7, 'yes': {'type': 'Cereal', 'prob': 0.5},
                      'no': {'type': 'Cereal', 'prob': 0.05}},
                     {'type': 'Baby Food', 'prob': 0.2, 'yes': {'type': 'Diapers', 'prob': 0.8},
                      'no': {'type': 'Diaper', 'prob': 0.01}},
                     {'type': 'Bread', 'prob': 0.5},
                     {'type': 'Peanut Butter', 'prob': 0.1, 'yes': {'type': 'Jelly/Jam', 'prob': 0.9},
                      'no': {'type': 'Jam/Jelly', 'prob': 0.05}}
                     ]
    counter = 0
    for item_dict in probabilities:
        chance = random.random()
        if chance <= item_dict['prob']:

            result.append(get_partial_sale(c, item_dict['type'], price_multiplier))
            if 'yes' in item_dict:
                chance = random.random()
                if chance <= item_dict['yes']['prob']:
                    result.append(get_partial_sale(c, item_dict['yes']['type'], price_multiplier))
        elif 'no' in item_dict:
            chance = random.random()
            if chance <= item_dict['no']['prob']:
                result.append(get_partial_sale(c, item_dict['no']['type'], price_multiplier))
    return result


def do_sales(c):
    min_customers = 1000
    max_customers = 1040
    weekend_increase = 50
    price_multiplier = 1.05
    max_items = 70

    records = []

    for i in range(365):
        num_customers = random.randint(min_customers, max_customers) # min_customers <= num_customers <= max_customers
        if i % 7 == 0 or i % 7 == 6: # jan 1 2017 was a sunday
            num_customers += weekend_increase
        for customer in range(num_customers):
            num_items = random.randint(1, max_items)
            prob_items = do_probability_sales(c, price_multiplier)
            current_sales = prob_items
            if num_items < len(prob_items):
                current_sales = prob_items[:num_items]
            else:
                # TODO: extend current_sales with partial sales records of items that are not probability types
                # I'd suggest doing a select of products whose type are not in the list and then picking a random one
                # replace pass with the functionality
                pass
            for i in range(len(current_sales)):
                current_sales[i].update({'CustomerNum': customer + 1, 'Date': (datetime.date(2017, 1, 1) +
                                                                              datetime.timedelta(days=i)).isoformat()})
            records.extend(current_sales)
    # TODO: insert sales records into database and summarize them


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: grocery <product_file>")
    else:
        random.seed()
        conn = sqlite3.connect('grocery.db')
        c = conn.cursor()
        manage_tables(c)
        import_products(c, sys.argv[1])
        conn.commit()
        print(str(get_item_type(c, 'Milk')))
        do_sales(c)