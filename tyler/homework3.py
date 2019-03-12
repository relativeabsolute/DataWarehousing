# Tyler Carberry and Mohammad Motamedi
# Homework 3
#
# Original program by Cole Robertson, David Carlin, and Clifford Black

import datetime
import random
import csv
import os

SIMULATION_START_DATE = datetime.datetime(2017, 1, 1)
SIMULATION_END_DATE = datetime.datetime(2017, 12, 31)
WEEKEND_INCREASE = 50
CUSTOMER_LOW = 1020
CUSTOMER_HIGH = 1060
ITEM_LOW = 1
ITEM_HIGH = 80
PRICE_MULT = 1.2

random.seed(12345)

os.chdir('/Users/tyler/code/data-warehousing/homework3') # Change based on environment

def write_record(writer, date, customer_num, sku, base_price, inventory):
    if inventory.get(sku) is None:
        a = 1

    writer.writerow(
        {
            'Date': date,
            'Customer #': customer_num,
            'SKU': sku,
            'Sale Price': round(base_price * PRICE_MULT, 2),
            'Items Left': inventory[sku]['on_hand'],
            'Total Cases Ordered': inventory[sku]['cases_bought']
        }
    )

def buy_product_non_milk(sku, one_day_supply, inventory):
    needed = 3 * one_day_supply[sku] - inventory[sku]['on_hand']
    if  needed >= 0:
        n_cases = needed // 12 + 1
        inventory_increase = n_cases * 12
        inventory[sku]['on_hand'] += inventory_increase
        inventory[sku]['cases_bought'] += n_cases

def buy_product_milk(sku, one_day_supply, inventory):
    needed = int(1.5 * one_day_supply[sku]) - inventory[sku]['on_hand']
    if  needed >= 0:
        n_cases = needed // 12 + 1
        inventory_increase = n_cases * 12
        inventory[sku]['on_hand'] += inventory_increase
        inventory[sku]['cases_bought'] += n_cases


def get_random_item(inventory, items_list):
    all_zero = True
    i = 0
    while i < len(items_list) and all_zero:
        all_zero = items_list[i][0] == 0
    if all_zero:
        return -1

    data = random.choice(items_list)
    while inventory[data[0]] == 0:
        data = random.choice(items_list)
    inventory[data[0]]['on_hand'] -= 1
    return data

# read products and write them to the dictionary
with open('Products1.txt', 'r', encoding='ISO-8859-1') as products_file:
    products_by_type = dict()
    products = []
    csv.register_dialect('pipes', delimiter='|')
    reader = csv.DictReader(products_file, dialect='pipes')
    for row in reader:
        data = [row['SKU'], float(row['BasePrice'][1:]), row['itemType']]
        products.append(data)
        if row['itemType'] not in products_by_type:
            products_by_type.update({row['itemType']: [data]})
        else:
            products_by_type[row['itemType']].append(data)

with open('sku_avg.csv', 'r') as day_quanity_file:
    # {sku: one_day_supply}
    one_day_supply = dict()
    reader = csv.DictReader(day_quanity_file)
    for row in reader:
        one_day_supply.update({row['SKU']: int(row['Average'])})

# {sku: {'on_hand', 'cases_bought'}
inventory = dict()
for sku in one_day_supply:
    inventory.update({
        sku:
            {
                'on_hand': 0,
                'cases_bought': 0
            }
    })
for sku in inventory:
    buy_product_non_milk(sku, one_day_supply, inventory)


with open('grocery_data_hw3.csv', 'w', encoding='ISO-8859-1') as data_file:
    writer = csv.DictWriter(data_file,
        fieldnames = ['Date', 'Customer #', 'SKU', 'Sale Price', 'Items Left', 'Total Cases Ordered'])
    writer.writeheader()
    current_date = SIMULATION_START_DATE

    while current_date <= SIMULATION_END_DATE:
        # Have logic for each day here
        date_str = "{:%Y%m%d}".format(current_date)
        print(date_str)
        increase = 0
        if current_date.weekday() >= 5:
            # current_date.weekday() returns 5 and 6 for saturday and sunday
            increase = WEEKEND_INCREASE
        # increase will be 0 when it is Mon-Fri
        daily_customers = random.randint(CUSTOMER_LOW, CUSTOMER_HIGH)

        # Put logic here for what each customer and what they buy
        for customer in range(1, daily_customers + 1):
            num_items = random.randint(ITEM_LOW, ITEM_HIGH)
            milk = random.randint(1, 100) <= 70
            bread = random.randint(1, 100) <= 50
            babyfood = random.randint(1, 100) <= 20
            pb = random.randint(1, 100) <= 10
            types_not_used = [] #eg. the 30% of the time that milk is not bought

            if not milk:
                types_not_used.append('Milk')
                cereal = random.randint(1, 100) <= 5
                if not cereal:
                    types_not_used.append('Cereal')
                else:
                    data = get_random_item(inventory, products_by_type['Cereal'])
                    if data != -1:
                        write_record(writer, date_str, customer, data[0], data[1], inventory)
                        num_items -= 1
            else:
                data = get_random_item(inventory, products_by_type['Milk'])
                if data != -1:
                    write_record(writer, date_str, customer, data[0], data[1], inventory)
                    num_items -= 1

                if num_items == 0:
                    continue

                cereal = random.randint(1, 100) <= 50
                if not cereal:
                    types_not_used.append('Cereal')
                else:
                    data = get_random_item(inventory, products_by_type['Cereal'])
                    if data != -1:
                        write_record(writer, date_str, customer, data[0], data[1], inventory)
                        num_items -= 1

            if num_items == 0:
                continue

            if not bread:
                types_not_used.append('Bread')
            else:
                data = get_random_item(inventory, products_by_type['Bread'])
                if data != -1:
                    write_record(writer, date_str, customer, data[0], data[1], inventory)
                    num_items -= 1

                if num_items == 0:
                    continue


            if not babyfood:
                types_not_used.append('Baby Food')
                diapers = random.randint(1,100) <= 1
                if not diapers:
                    types_not_used.append('Diapers')
                else:
                    data = get_random_item(inventory, products_by_type['Diapers'])
                    if data != -1:
                        write_record(writer, date_str, customer, data[0], data[1], inventory)
                        num_items -= 1
            else:
                data = get_random_item(inventory, products_by_type['Baby Food'])
                if data != -1:
                    write_record(writer, date_str, customer, data[0], data[1], inventory)
                    num_items -= 1

                if num_items == 0:
                    continue
                diapers = random.randint(1, 100) <= 80
                if not diapers:
                    types_not_used.append('Diapers')
                else:
                    data = get_random_item(inventory, products_by_type['Diapers'])
                    if data != -1:
                        write_record(writer, date_str, customer, data[0], data[1], inventory)
                        num_items -= 1

            if num_items == 0:
                continue

            if not pb:
                types_not_used.append('Peanut Butter')
                jelly = random.randint(1, 100) <= 5
                if not jelly:
                    types_not_used.append('Jelly/Jam')
                else:
                    data = get_random_item(inventory, products_by_type['Jelly/Jam'])
                    if data != -1:
                        write_record(writer, date_str, customer, data[0], data[1], inventory)
                        num_items -= 1
            else:
                data = get_random_item(inventory, products_by_type['Peanut Butter'])
                if data != -1:
                    write_record(writer, date_str, customer, data[0], data[1], inventory)
                    num_items -= 1

                if num_items == 0:
                    continue

                jelly = random.randint(1, 100) <= 90
                if not jelly:
                    types_not_used.append('Jelly/Jam')
                else:
                    data = get_random_item(inventory, products_by_type['Jelly/Jam'])
                    if data != -1:
                        write_record(writer, date_str, customer, data[0], data[1], inventory)
                        num_items -= 1

            if num_items == 0:
                continue

            for k in range(num_items):
                data = random.choice(products)
                while data[2] in types_not_used:
                    data = get_random_item(inventory, products)
                write_record(writer, date_str, customer, data[0], data[1], inventory)

        # order any item and it will magically appear here
        weekday = current_date.weekday()
        # Last Name Parameter ##################################################
        boolean_delivery_day = weekday == 0 or weekday == 2 or weekday == 4 # MWF
        # boolean_delivery_day = weekday == 1 or weekday == 3 or weekday == 5 # TRS
        ########################################################################
        if boolean_delivery_day:
            for product in products:
                if product[2] != 'Milk':
                    buy_product_non_milk(product[0], one_day_supply, inventory)

        for product in products_by_type['Milk']:
            buy_product_milk(product[0], one_day_supply, inventory)

        current_date = current_date + datetime.timedelta(days=1)
