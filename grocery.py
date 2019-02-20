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

    cursor.execute('''DROP TABLE IF EXISTS sales_record''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS sales_record (Date TEXT, CustomerNum INT, SKU INT, SalePrice REAL)''')

    cursor.execute('''DROP TABLE IF EXISTS hw2''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS sales_record (ItemType TEXT, SalesPerDay INT, AvgSalePer2Weeks INT)''')


# c is database cursor
# filename is name of file to import products from
def import_products(c, filename):
    with open(filename, 'r') as file_handle:
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
    return {'SKU': record[5], 'SalePrice': record[6] * price_multiplier}


# get a random row that is the given type
def get_item_type(c, type_name):
    c.execute('''SELECT * FROM products where ItemType = ?''', [type_name])
    rows = c.fetchall()
    return rows[random.randrange(0, len(rows))]


# Added this to get the non probability products, not sure if this is correct
def non_probability_items(c, number_items, price_multiplier):
    c.execute('''SELECT * FROM products where ItemType NOT IN ('Milk', 'Cereal', 'Baby Food', 'Diapers', 'Bread', 'Peanut Butter', 'Jelly/Jam')''')
    rows = c.fetchall()
    records = random.sample(rows,k=number_items)
    return [{'SKU': record[5], 'SalePrice': record[6] * price_multiplier} for record in records]


# returns partial (SKU and sale price) sales records of items bought with probability
def do_probability_sales(c, price_multiplier):
    result = []
    probabilities = [{ 'type': 'Milk', 'prob': 0.7, 'yes': {'type': 'Cereal', 'prob': 0.5},
                      'no': {'type': 'Cereal', 'prob': 0.05}},
                     {'type': 'Baby Food', 'prob': 0.2, 'yes': {'type': 'Diapers', 'prob': 0.8},
                      'no': {'type': 'Diapers', 'prob': 0.01}},
                     {'type': 'Bread', 'prob': 0.5},
                     {'type': 'Peanut Butter', 'prob': 0.1, 'yes': {'type': 'Jelly/Jam', 'prob': 0.9},
                      'no': {'type': 'Jelly/Jam', 'prob': 0.05}}
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

    for i in range(365):
        print("Day {}".format(i))
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
        # add sales per customer
            c.executemany('''INSERT INTO sales_record VALUES (:Date, :CustomerNum, :SKU, :SalePrice)''', current_sales)


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
    c.execute('''SELECT SKU, COUNT(SKU) from sales_record GROUP BY SKU ORDER BY COUNT(SKU) LIMIT 10''')
    print("Top 10 selling items: {}".format(c.fetchall()))


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
        do_sales(c)
        conn.commit()
        compute_summaries(c)

####### Part 2
# sales_record column names Date, CustomerNum, SKU, SalePrice
conn = sqlite3.connect('grocery.db')
c = conn.cursor()

# Number of milk sold in one day
c.execute("select count(date) from sales_record where sku in (select sku from products where itemtype = 'Milk') and Date == '2017-01-01'")
daymilk = c.fetchall()
# Average sale of milk per day looking at 2 weeks of transactions
c.execute("select count(date)/14 from sales_record where sku in (select sku from products where itemtype = 'Milk') and Date between '2017-01-01' and '2017-01-15'")
avgmilk = c.fetchall()
milkdata = ('Milk', daymilk[0][0], avgmilk[0][0])
print(milkdata)
c.executemany('''INSERT INTO hw2 VALUES (:ItemType, :SalesPerDay, :AvgSalePer2Weeks)''', milkdata)

Do the same for Cereal, Baby Food, Diapers, Peanut Butter, Jelly/Jam, etc
c.execute("select count(date) from sales_record where sku in (select sku from products where itemtype = 'Cereal') and Date == '2017-01-01'")
daycereal = c.fetchall()
c.execute("select count(date)/14 from sales_record where sku in (select sku from products where itemtype = 'Cereal') and Date between '2017-01-01' and '2017-01-15'")
avgcereal = c.fetchall()
cerealdata = ('Cereal', daycereal[0][0], avgcereal[0][0])
print(cerealdata)
c.executemany('''INSERT INTO hw2 VALUES (:ItemType, :SalesPerDay, :AvgSalePer2Weeks)''', cerealdata)

c.execute("select count(date) from sales_record where sku in (select sku from products where itemtype = 'Baby Food') and Date == '2017-01-01'")
daybbfood = c.fetchall()
c.execute("select count(date)/14 from sales_record where sku in (select sku from products where itemtype = 'Baby Food') and Date between '2017-01-01' and '2017-01-15'")
avgbbfood = c.fetchall()
bbfooddata = ('Baby Food', daybbfood[0][0], avgbbfood[0][0])
print(bbfooddata)
c.executemany('''INSERT INTO hw2 VALUES (:ItemType, :SalesPerDay, :AvgSalePer2Weeks)''', bbfooddata)

c.execute("select count(date) from sales_record where sku in (select sku from products where itemtype = 'Diapers') and Date == '2017-01-01'")
dayDiapers = c.fetchall()
c.execute("select count(date)/14 from sales_record where sku in (select sku from products where itemtype = 'Diapers') and Date between '2017-01-01' and '2017-01-15'")
avgDiapers = c.fetchall()
Diapersdata = ('Diapers', dayDiapers[0][0], avgDiapers[0][0])
print(Diapersdata)
c.executemany('''INSERT INTO hw2 VALUES (:ItemType, :SalesPerDay, :AvgSalePer2Weeks)''', Diapersdata)

c.execute("select count(date) from sales_record where sku in (select sku from products where itemtype = 'Bread') and Date == '2017-01-01'")
dayBread = c.fetchall()
c.execute("select count(date)/14 from sales_record where sku in (select sku from products where itemtype = 'Bread') and Date between '2017-01-01' and '2017-01-15'")
avgBread = c.fetchall()
Breaddata = ('Bread', dayBread[0][0], avgBread[0][0])
print(Breaddata)
c.executemany('''INSERT INTO hw2 VALUES (:ItemType, :SalesPerDay, :AvgSalePer2Weeks)''', Breaddata)

c.execute("select count(date) from sales_record where sku in (select sku from products where itemtype = 'Peanut Butter') and Date == '2017-01-01'")
daypb = c.fetchall()
c.execute("select count(date)/14 from sales_record where sku in (select sku from products where itemtype = 'Peanut Butter') and Date between '2017-01-01' and '2017-01-15'")
avgpb = c.fetchall()
pbdata = ('Peanut Butter', daypb[0][0], avgpb[0][0])
print(pbdata)
c.executemany('''INSERT INTO hw2 VALUES (:ItemType, :SalesPerDay, :AvgSalePer2Weeks)''', pbdata)

c.execute("select count(date) from sales_record where sku in (select sku from products where itemtype = 'Jelly/Jam') and Date == '2017-01-01'")
dayjj = c.fetchall()
c.execute("select count(date)/14 from sales_record where sku in (select sku from products where itemtype = 'Jelly/Jam') and Date between '2017-01-01' and '2017-01-15'")
avgjj = c.fetchall()
jjdata = ('Jelly/Jam', dayjj[0][0], avgjj[0][0])
print(jjdata)
c.executemany('''INSERT INTO hw2 VALUES (:ItemType, :SalesPerDay, :AvgSalePer2Weeks)''', jjdata)

c.execute("select count(date) from sales_record where sku in (select sku from products where itemtype not in "
          "('Milk', 'Cereal', 'Baby Food', 'Diapers', 'Bread', 'Peanut Butter', 'Jelly/Jam')) and Date == '2017-01-01'")
dayee = c.fetchall()
c.execute("select count(date)/14 from sales_record where sku in (select sku from products where itemtype not in "
          "('Milk', 'Cereal', 'Baby Food', 'Diapers', 'Bread', 'Peanut Butter', 'Jelly/Jam')) and Date between '2017-01-01' and '2017-01-15'")
avgee = c.fetchall()
eedata = ('Everything else', dayee[0][0], avgee[0][0])
print(eedata)
c.executemany('''INSERT INTO hw2 VALUES (:ItemType, :SalesPerDay, :AvgSalePer2Weeks)''', eedata)

#to export the db table hw2 as a csv?
#csvWriter.writerows(hw2)