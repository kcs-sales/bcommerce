'''
	Navdeep Ghai
'''

import frappe
from bigcommerce.utils.api import get_connection

conn = get_connection() #After applying all the details about Bcommerce Setting


# Get Resource By ID

#Orders
order = conn.Orders.get(id=10)
order_products = order.products()
customer = order.customer_id


#Product
product = conn.Products.get(id=11)
option_set = products.option_set_id #Option set Linked with Item Attribute

#customer
customer = conn.Customers.get(id=12)
customer_addresses = customer.addresses() #To get Customer addresses





#Get Multiple resources

#Orders
orders  = conn.Orders.all(limit=250) # 250 is max limit for ordres.
orders = conn.Orders.all(min_id=1, max_id=200, limit=200) # To sync only 200 Order from big commerce from id 1 to 200


#Products
products = conn.Products.all(limit=250) # 250 is max limit you can only fetch 250 products at time.
products = conn.Products.all(name="table") # Sync customer which name  is table.
products = conn.Products.all(min_id=200, max_id = 250, limit=50)


#Customers
customers = conn.Customers.all(limit=250) # Sync to the maximum extent i.e 250
customers = conn.customers.all(min_id=4, max_id=10) # Sync only six customers













