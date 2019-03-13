import sys
import sqlite3
import csv
import re
import random
import datetime
import math


def manage_tables(cursor):
    cursor.execute('''DROP TABLE IF EXISTS products''')
    cursor.execute('''CREATE TABLE products
        (Manufacturer TEXT, ProductName TEXT, Size REAL, SizeUnit TEXT, ItemType TEXT, SKU INT, BasePrice REAL)''')

    cursor.execute('''DROP TABLE IF EXISTS sales_record''')
    cursor.execute('''CREATE TABLE sales_record (Date TEXT, CustomerNum INT, SKU INT, SalePrice REAL)''')

    cursor.execute('''DROP TABLE IF EXISTS inventory''')
    cursor.execute('''CREATE TABLE inventory (SKU INT, NumberOnHand INT, TotalCasesOrdered INT, ExpectedDaily INT)''')


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
    if record is None:
        return None
    return {'SKU': record[0], 'SalePrice': record[1] * price_multiplier}


# get a random row that is the given type
# returns [SKU, BasePrice]
def get_item_type(c, type_name):
    is_milk = type_name == 'Milk'
    c.execute('''SELECT products.SKU, products.BasePrice
     FROM products join inventory on products.SKU = inventory.SKU
     where ItemType = ? and NumberOnHand > 0''', [type_name])
    rows = c.fetchall()
    if len(rows) == 0:
        return None
    return rows[random.randrange(0, len(rows))]


# Added this to get the non probability products, not sure if this is correct
def non_probability_items(c, number_items, price_multiplier):
    c.execute('''SELECT products.SKU, products.BasePrice
        FROM products join inventory on products.SKU = inventory.SKU
        where ItemType NOT IN ('Milk', 'Cereal', 'Baby Food', 'Diapers', 'Peanut Butter', 'Jelly/Jam')
        and NumberOnHand > 0''')
    rows = c.fetchall()
    records = random.sample(rows,k=number_items)
    return [{'SKU': record[0], 'SalePrice': record[1] * price_multiplier} for record in records]


probabilities = [{ 'type': 'Milk', 'prob': 0.7, 'yes': {'type': 'Cereal', 'prob': 0.5},
                      'no': {'type': 'Cereal', 'prob': 0.05}},
                     {'type': 'Baby Food', 'prob': 0.2, 'yes': {'type': 'Diapers', 'prob': 0.8},
                      'no': {'type': 'Diapers', 'prob': 0.01}},
                     {'type': 'Bread', 'prob': 0.5},
                     {'type': 'Peanut Butter', 'prob': 0.1, 'yes': {'type': 'Jelly/Jam', 'prob': 0.9},
                      'no': {'type': 'Jelly/Jam', 'prob': 0.05}}]

min_customers = 1000
max_customers = 1040
weekend_increase = 50
price_multiplier = 1.05
max_items = 70


def initial_inventory(c):
    expected = expected_sales()
    result = []
    for row in c.execute('''SELECT SKU, ItemType FROM products'''):
        row_dict = {'SKU': row[0]}
        type_name = row[1]
        if row[1] not in expected:
            type_name = 'regular'
        multiplier = 3
        if row[1] == 'Milk':
            multiplier = 1.5
        cases = int(multiplier * expected[type_name]) // 12 + 1
        #row_dict['ItemType'] = type_name
        row_dict['TotalCasesOrdered'] = cases
        row_dict['NumberOnHand'] = cases * 12
        row_dict['ExpectedDaily'] = expected[type_name]
        result.append(row_dict)
    c.executemany('''INSERT INTO inventory VALUES (:SKU, :NumberOnHand, :TotalCasesOrdered, :ExpectedDaily)''', result)


def expected_sales():
    expected_customers = max_customers
    result = {}
    for item_dict in probabilities:
        prob = item_dict['prob']
        result[item_dict['type']] = math.ceil(expected_customers * prob)
        if 'yes' in item_dict:
            result[item_dict['yes']['type']] = math.ceil(expected_customers * prob * item_dict['yes']['prob'])
        if 'no' in item_dict:
            result[item_dict['no']['type']] = math.ceil(expected_customers * (1 - prob) * item_dict['no']['prob'])
    result['regular'] = math.ceil(expected_customers * (max_items / 2) / 66)
    return result


# returns partial (SKU and sale price) sales records of items bought with probability
def do_probability_sales(c, price_multiplier):
    result = []
    for item_dict in probabilities:
        chance = random.random()
        if chance <= item_dict['prob']:
            partial = get_partial_sale(c, item_dict['type'], price_multiplier)
            if partial is not None:
                result.append(partial)
            if 'yes' in item_dict:
                chance = random.random()
                if chance <= item_dict['yes']['prob']:
                    partial = get_partial_sale(c, item_dict['yes']['type'], price_multiplier)
                    if partial is not None:
                        result.append(partial)
        elif 'no' in item_dict:
            chance = random.random()
            if chance <= item_dict['no']['prob']:
                partial = get_partial_sale(c, item_dict['no']['type'], price_multiplier)
                if partial is not None:
                    result.append(partial)
    return result


def do_milk_deliveries(c):
    print("Milk deliveries")
    c.execute('''SELECT products.SKU, NumberOnHand, ExpectedDaily from products
            join inventory on products.SKU = inventory.SKU
            where ItemType = 'Milk' and NumberOnHand < 1.5 * ExpectedDaily''')
    rows = c.fetchall()
    for row in rows:
        print('Ordering more of item with SKU {}'.format(row[0]))
        needed = math.ceil(1.5 * row[2]) - row[1]
        cases = needed // 12 + 1
        ordered = cases * 12
        c.execute('''UPDATE inventory
                    SET NumberOnHand = NumberOnHand + ?,
                    TotalCasesOrdered = TotalCasesOrdered + ?
                    WHERE SKU = ?''', [ordered, cases, row[0]])


def do_deliveries(c):
    print("Non-milk deliveries")
    c.execute('''SELECT products.SKU, NumberOnHand, ExpectedDaily from products
            join inventory on products.SKU = inventory.SKU
            where ItemType <> 'Milk' and NumberOnHand < 3 * ExpectedDaily''')
    rows = c.fetchall()
    for row in rows:
        print("Ordering more of item with SKU {}".format(row[0]))
        needed = 3 * row[2] - row[1] # 3 * Expected - NumberOnHand
        cases = needed // 12 + 1
        ordered = cases * 12
        c.execute('''UPDATE inventory
            SET NumberOnHand = NumberOnHand + ?,
            TotalCasesOrdered = TotalCasesOrdered + ?
            WHERE SKU = ?''', [ordered, cases, row[0]])


def do_sales(c, days):
    for i in range(days):
        print("Day {}".format(i))
        do_milk_deliveries(c)
        if i % 3 == 0:
            do_deliveries(c)
        num_customers = random.randint(min_customers, max_customers) # min_customers <= num_customers <= max_customers
        if i % 7 == 0 or i % 7 == 6: # jan 1 2017 was a sunday
            num_customers += weekend_increase
        for customer in range(num_customers):
            print("Customer {}".format(customer))
            num_items = random.randint(1, max_items)
            print("Probability sales")
            prob_items = do_probability_sales(c, price_multiplier)
            current_sales = prob_items
            if num_items < len(prob_items):
                current_sales = prob_items[:num_items]
            else:
                print("Non probability sales")
                # my attempt to add to the current sales
                current_sales.extend(non_probability_items(c, num_items - len(current_sales), price_multiplier))

            for sale_index in range(len(current_sales)):
                current_sales[sale_index].update({'Date': (datetime.date(2017, 1, 1) + datetime.timedelta(days=i)).isoformat(),
                                         'CustomerNum': customer + 1})
            inventory_update = [[item['SKU']] for item in current_sales]
            c.executemany('''UPDATE inventory set NumberOnHand = NumberOnHand - 1
                where SKU = ?''', inventory_update)
        # add sales per customer
            c.executemany('''INSERT INTO sales_record VALUES (:Date, :CustomerNum, :SKU, :SalePrice)''', current_sales)


def read_expected_daily(filename):
    result = []
    with open(filename, 'r', newline='') as filehandle:
        reader = csv.DictReader(filehandle)
        result = {row['Type'] : int(row['Number']) for row in reader}
    return result


def compute_summaries(c):
    # number of customers is sum of max customer numbers per day
    c.execute('''SELECT SUM(customers.maxNum) from
        (SELECT MAX(sr.CustomerNum) as maxNum, sr.Date from sales_record as sr GROUP BY sr.Date) as customers''')
    print("Number of customers {}".format(c.fetchone()))

    # total sales
    c.execute('''SELECT SUM(SalePrice) from sales_record''')
    print("Total sales: {}".format(c.fetchone()))

    # total items bought
    c.execute('''SELECT COUNT(SKU) from sales_record''')
    print("Total items bought: {}".format(c.fetchone()))

    # top 10 selling items with counts
    c.execute('''SELECT products.SKU, COUNT(products.SKU), NumberOnHand, TotalCasesOrdered from sales_record
    join inventory on products.SKU = inventory.SKU
    GROUP BY SKU ORDER BY COUNT(SKU) LIMIT 10''')
    print("Top 10 selling items: {}".format(c.fetchall()))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: grocery <product_file> [days]")
    else:
        random.seed()
        conn = sqlite3.connect('grocery.db')
        c = conn.cursor()
        manage_tables(c)
        import_products(c, sys.argv[1])
        initial_inventory(c)
        conn.commit()
        days = 365
        if len(sys.argv) == 3:
            days = int(sys.argv[2])
        do_sales(c, days)
        conn.commit()
