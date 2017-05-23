# -*- coding: utf-8 -*-
from __future__ import unicode_literals
'''

	Develop Navdeep Ghai
	Email navdeep@korecent.com
'''
 
from __future__ import unicode_literals, absolute_import 

import frappe, bcommerce
from frappe import throw, _
from frappe.utils import cint, cstr
from bcommerce.utils.api import get_connection

RESOURCES = ['Orders', 'Products', 'Customers', 'Geography']
MIN_ID = 0 # For Bulk Sync
MAX_ID = 250 # For Bulk Sync



def validate_customers_setting(setting):
	
	flag = True
	customer_group = setting.get("customer_group")
	customer_territory = setting.get("customer_territory")
	customer_type = setting.get("customer_type")

	if not customer_group or not customer_territory or not customer_type:
		flag = False
		frappe.msgprint(_("Customer: [Customer Type, Customer Territory, Customer Group], Please \
					enter mandatory  fields under Customer Section"))
	
	return flag



def validate_products_setting(setting):
	flag = True
	item_group = setting.get("item_group")
	warehouse = setting.get("warehouse")
	selling_price_list = setting.get("selling_price_list")
	buying_price_list = setting.get("buying_price_list")	
	
	if not item_group or not warehouse or not selling_price_list or not buying_price_list:
		flag = False
		frappe.msgprint(_("Product:[Item Group, Warehouse, Selling Price List, Buying Price List], Please enter mandatory fields under Product Section"))

	return flag

def validate_orders_setting(setting):

	flag  = True
	company = setting.get("company")
	cost_center = setting.get("cost_center")
	taxes = setting.get("bcommerce_taxes")

	if not company or not cost_center or not taxes:
		flag = False
		frappe.msgprint(_("Order:[Company, Taxes, Cost Center], Please enter mandatory fields under Order section"))
	return flag

'''
	Every Resource on Big Commerce identified by Unique ID
	If resource doesn't exists  it'll return empty response
	You've to ensure that resource is empty or not, if its not empty
	then verify what data resources is holding
'''

def validate_resource(resource, fieldname=None):

	flag = True
	fieldname = fieldname if fieldname else "id"
	if not resource:
		flag = False

	elif (resource and isinstance(resource, dict) and not resource.has_key(fieldname)):
		flag = False

	elif (resource and isinstance(resource, basestring)):
		flag = False

	return flag
'''
	Get resource from bcommerce for update
'''
def get_resource(resource, id, multiple=False):

	try:
		conn = get_connection()
		data = {}
		if hasattr(conn, resource):
			resource = getattr(conn, resource)
			data = resource.get(id)
			if not validate_resource(data):
				data = {}
		return data
	except Exception as e:
		print e
		print frappe.get_traceback()


