
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

'''
	Developer Navdeep Ghai
	Email navdeep@korecent.com

This is beta version code, can be make enhancements in future

'''

import sys
import os
import frappe
from frappe.utils.background_jobs import enqueue
from frappe import _, msgprint, throw
from bcommerce.connection  import BcommerceAPI
from bcommerce.utils.logger import make_logs
from frappe.utils import cint, flt, cstr, now_datetime
import bcommerce
from bcommerce.exceptions import SyncError, BcommerceSetupError, BcommerceConnectionError , \
				BcommerceOptionError, BcommerceOptionSetError, BcommerceProductError, \
				ProductDoesNotExist, CustomerDoesNotExist, BcommerceCustomerError, \
				BcommerceOptionError, BcommerceOrderError

from bigcommerce.exception import EmptyResponseWarning, ClientRequestException, RateLimitingException, \
				ServerException

MIN_ID = 0
MAX_ID = 250
DEBUG = 0

'''
	Get Connection information
'''
def get_connection():

	setting = frappe.get_doc("Bcommerce Setting", "Bcommerce Setting")
	validate_mandatory(setting)
	auth_type = setting.authentication_type
	api = None
	if auth_type == "Basic Authentication":	
		api = BcommerceAPI(setting.host, basic_auth=(setting.app_name, setting.token))
			
	else:
		api =  BcommerceAPI(client_id=setting.client_id, access_token=setting.access_token, store_hash=setting.store_hash)	

		
	return api
		
'''
	Validate Bcommerce Store Setting
'''

def validate_mandatory(setting):
	if not setting:
		raise BcommerceSetupError(_("Please Setup your Bcommerce Setting"))
		return
	else:
		auth_type = setting.authentication_type
		if auth_type == "Basic Authentication":
			if not setting.host or not setting.token or not setting.app_name:
				#later Stage will implement logs for tracking the issue for developer
				raise BcommerceSetupError(_("Please Check your all fields related to Basic Authetication"))
		else:
			if not setting.client_id or not setting.access_token or not setting.store_hash:
				raise BcommerceSetupError(_("Client ID,  Access Token, Store Hash all are mandatory"))
			
	return

'''
	Just to ensure record already exists in database or not
	If Yes/ Then return the name of record to be link further with transactional data
'''
def is_exists(_id, doctype, fieldname):
	resource_id, resource_doctype = _id, doctype
	if isinstance(resource_id, basestring):
		resource_id = cint(resource_id)
	# Below code will return only name of resource
	flag = frappe.db.get_value(resource_doctype, filters={fieldname:resource_id}, as_dict=True)

	return flag if flag else None

'''
	Sync Master Store Setting [ Store Reference ]
'''
def sync_store_setting():

	setting = frappe.get_doc("Bcommerce Setting", "Bcommerce Setting")
	try:
		
		from bcommerce.utils.store import sync_with_store
		enqueue("bcommerce.utils.store.sync_with_store", queue="long")
	except Exception as e:
		make_logs("Failed", "Sync Error", message=frappe.get_traceback())


 


'''
	Function to Start the Syncing process between Bcommerce and ERPNext 
'''
def start_sync():

	setting = frappe.get_doc("Bcommerce Setting", "Bcommerce Setting")	
	if not setting.enable:
		frappe.msgprint(_("Please enable bcommerce app for EPRNext"))
		return  False
	elif not validate_setting(setting):
		return False
	sync_bulk(setting)
	
 
'''
	Start synchronization between both servers
'''
def sync_bulk(setting):
	"""
		Function used to sync all the prodcut from provide Min ID and Max ID
	"""
	if not get_queue_status():
		frappe.msgprint(_("Syncing already in progress"))	
		return {}
	try:
		make_logs("Queued", "Syncing", message="Syncing in progress")
		sync_customers(setting)
		sync_products(setting)
		sync_orders(setting)
		make_logs("Syncing Completed", "Syncing", message="Syncing complete successfully")
		frappe.db.commit()	
		'''
			Exceptions are more important  for tracking the logs the error
			For Future you can even Sync the same resource/create new resource
			using manual sync
		'''
	except Exception, e:
		make_logs("Failed", "Syncing", message="Syncing Failed")
			



'''
	Get Curency status of queue, so that user can't make same request again and again
'''
def get_queue_status():

	flag = True
	status = frappe.db.sql(""" SELECT title,  resource_type FROM `tabBcommerce Log` WHERE resource_type="Syncing" \
				ORDER BY modified DESC LIMIT 1""", as_dict=True)
	if status and len(status) == 1:
		status  = status[0]
		if status.get("title") == "Queued":
			flag = False
		elif status.get("title") == "Syncing Completed":
			flag = True
		elif status.get("title") == "Failed":
			flag = True

		
	return flag
			
'''
	Start sycing Customer
'''
def sync_customers(setting, min_id=None, max_id=None, id=None):

	
	from bcommerce.utils.customers import sync_bulk_customers
	customers = []
	conn = get_connection()
	if min_id and max_id:
		customers = conn.Customers.all(min_id=min_id, max_id=max_id, limit=250)

	elif id:
		pass

	else:

		min_id = get_last_sync_id("bcommerce_customer_id", "Customer")
		max_id =  min_id + MAX_ID	
		customers = conn.Customers.all(min_id=min_id, max_id=max_id, limit=250)
		if not validate_resources(customers):
			return
	sync_bulk_customers(customers, setting, conn)
	
'''
	Start sycing products
'''
def sync_products(setting):

	conn = get_connection()
	from bcommerce.utils.products import sync_bulk_products
	min_id = get_last_sync_id("bcommerce_product_id", "Item")
	max_id = min_id + MAX_ID
	products = conn.Products.all(min_id=min_id, max_id=max_id, limit=250)
	if not validate_resources(products):
		return
	
	sync_bulk_products(products, setting, conn)
	
'''
	Start syncing Orders
'''			
def sync_orders(setting):
	
	conn = get_connection()
	from bcommerce.utils.orders import sync_bulk_orders
	min_id = get_last_sync_id("bcommerce_order_id", "Sales Order")
	if min_id == 0 and setting.start_syncing_from_id:
		min_id = setting.start_syncing_from_id
			
	max_id = min_id + MAX_ID
	orders = conn.Orders.all(min_id=min_id, max_id=max_id, limit=250)
	if not validate_resources(orders):
		return
	sync_bulk_orders(orders, setting, conn)	
		

'''
	Validate resources, just to ensure response has data or not
'''
def validate_resources(resources):
	
	if (resources and  not isinstance(resources, list)) or (isinstance(resources, list) and len(resources) == 0):
		return False
	
	return True


'''
	To ensure resource does exist on remote [Big Commerce]
	exist or not
'''
def is_exists_on_remote(resource_type, id):
	
	conn = get_connection()
	if hasattr(conn, resource_type):
		try:
			getattr(conn, resource_type).get(id=id)

		except Exception as e:

			print frappe.get_traceback()

'''
	Last synced ID, from where next syncing will be start
'''
def get_last_sync_id(fieldname, doctype):

	b_id = frappe.db.sql("""SELECT {fieldname} FROM `tab{doctype}` WHERE  {flag} != 0  ORDER BY creation DESC  \
				LIMIT 1""".format(fieldname=fieldname, doctype=doctype, flag=fieldname), as_dict=1)

	id = b_id[0].get(fieldname) if (b_id and len(b_id) >= 1) else 1
	return id+1


def validate_setting(setting):

	flag = True
	if   not setting:
		flag = False

	elif setting and setting.authentication_type == "Basic Authentication":
		if not setting.app_name or not setting.token or not setting.host:
			flag = False		

	elif setting and setting.authentication_type == "OAuth Authentication":
		if not setting.client_id or not setting.store_hash or not setting.access_token:
			flag = False

	if flag == True:

		from bcommerce.utils import validate_products_setting
		from bcommerce.utils import validate_customers_setting
		from bcommerce.utils import validate_orders_setting
	
		product = validate_products_setting(setting)
		customer = validate_customers_setting(setting)
		order = validate_orders_setting(setting)
		if not product or not customer or not order:
			flag = False

	return flag
