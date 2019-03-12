Tyler Carberry and Mohammad Motamedi
Group #5
Homework 3
Original program by Cole Robertson, David Carlin, and Clifford Black

SQL command to generate sku_avg.csv
SELECT p.SKU, round(count(*) / 14) as Average FROM carberry_grocery_data_hw2 c JOIN products p on c.SKU = p.SKU GROUP BY p.SKU;
