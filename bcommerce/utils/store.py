


# -*- coding: utf-8 -*-
from __future__ import unicode_literals
'''	
	Developer Navdeep Ghai
	Email navdeep@korecent.com
'''

import frappe
from frappe import _, msgprint
from frappe.utils import cint, cstr, flt
from bcommerce.utils.api import get_connection, get_last_sync_id, get_queue_status
from bcommerce.utils import get_resource, validate_resource
from bcommerce.utils.logger import make_logs
KEYS = ['last_name', 'first_name', 'secure_url', 'country_code', 'domain', 'phone',
	'address','plan_level', 'admin_email', 'plan_name', 'order_email']

'''
	This file has function to sync up the master data
	Used to Sync the Bcommerce Setting with ERPNext
'''

def sync_with_store():

	try:
		setting = frappe.get_doc("Bcommerce Setting", "Bcommerce Setting")

		if not get_queue_status():
			msgprint(_("Sync is already in progress"))
			return
		make_logs("Queued", "Syncing", message="Queued for syncing, Store Setting")
		sync_store()
		sync_currencies(setting)
		sync_countries(setting)
		sync_payments(setting)
		make_logs("Sync Completed", "Syncing", "Syncing complete successfully")
		frappe.db.commit()
	except Exception as e:
		msg = "{0}, {1}".format("Error while syncing store setting", frappe.get_traceback())
		make_logs("Failed", "Syncing", message=msg)

def sync_store(store=None, save=True, doc=None):

	if not doc:
		doc = frappe.get_doc("Bcommerce Setting", "Bcommerce Setting")
	d = doc.as_dict()
	if not store:
		store = get_connection().Store.all()
	for key, val in store.iteritems():
		if key in  KEYS:
			doc.set(key, val)						
	doc.set("default_currency", store.currency)
	
	if save:
		doc.save(ignore_permissions=True)
	

		

def sync_currencies(setting, id=None):
	
	setting = frappe.get_doc("Bcommerce Setting", "Bcommerce Setting")

	if id and not frappe.db.get_value("Currency",{"bcommerce_currency_id":id}):
		
		currency = get_resource("Currencies", id)
		if not currency:
			return
		update_currency(currency,setting)
	
	else:
		currencies = get_connection().Currencies.all()
		for currency in currencies:
			if validate_resource(currency):
				update_currency(currency, setting)		
				


def update_currency(currency, setting):

	flag = frappe.db.get_value("Currency", {"name": currency.currency_code}, as_dict=True)
	if flag:
		doc = frappe.get_doc("Currency", currency.currency_code)
		doc.update({
			"bcommerce_currency_id": currency.id
		})
		doc.save(ignore_permissions=True)
		if currency.currency_exchange_rate and not currency.currency_code == setting.default_currency:
			frm = setting.default_currency
			to = currency.currency_code
			rate = currency.currency_exchange_rate
			make_currency_exchange(frm, to, rate)


def make_currency_exchange(frm, to, rate):

	name = get_currency_exchange_name(frm, to)
	if not frappe.db.get_value("Currency Exchange", filters={"name":name}):
		frappe.get_doc({
				"doctype": "Currency Exchange",
				"date": frappe.utils.nowdate(),
				"from_currency": frm,
				"to_currency": to,
				"exchange_rate": rate
			}).save(ignore_permissions=True)
	else:
		
		doc = frappe.get_doc("Currency Exchange", name)
		doc.update({
			"date": frappe.utils.nowdate(),
			"from_currency": frm,
			"to_currency": to,
			"exchange_rate": rate
		})
		doc.save(ignore_permissions=True)

	
def get_currency_exchange_name(frm, to):
	
	name = "{0}-{1}-{2}".format(frappe.utils.nowdate(), frm, to)
	return name

def sync_countries(setting):

	"""
		There are less countries in the world than limit of record
		provided as with parameter in request

	"""
	countries = get_connection().Countries.all(limit=250)
	for country in countries if countries else []:
		try:
			update_country(country, setting)
			make_states(country)	
		except:
			pass



def update_country(country, setting):

	"""
		There are two ISO code used within Big Commerce Sytem ISO2 is same as  country 
		code in EPRNext ISO3  is different from from country code in ERPNext
	"""
	flag = frappe.db.get_value("Country", filters={"name":country.country}, as_dict=True)

	doc = None
	if flag:
		doc = frappe.get_doc("Country", flag.get("name"))
		doc.update({
			"name": country.country,
			"code": country.country_iso2,
		})
		
	else:
		doc = frappe.get_doc({
			"doctype": "Country",
			"name": country.country,
			"code": country.country_iso2,
			})
	
	if doc:
		doc.flags.ignore_mandatory = 1
		doc.save(ignore_permissions=True)
		



def make_states(country):

	states = []
	for state in country.states():
		if validate_resource(state):
			name = frappe.db.get_value("Bcommerce State", {"state":state.state})
			doc = None
			if name:
				doc = frappe.get_doc("Bcommerce State", name.get("name"))
				doc.update({
					"abbr":state.state_abbreviation,
					"state": state.state,
					"country": country.country
				})
			else:
				
				doc = frappe.get_doc({
					"doctype": "Bcommerce State",
					"abbr": state.state_abbreviation,
					"state": state.state,
					"country": country.country
					})	
			if doc:
				doc.save(ignore_permissions=True)
				frappe.db.commit()
			

def sync_payments(setting):
		
	payment_methods = get_connection().PaymentMethods.all()
	
	for pay_method  in payment_methods:
		if validate_resource(pay_method, "name"):	
			flag = frappe.db.get_value("Mode of Payment", {"mode_of_payment":pay_method.name})
			doc = None
			if flag:
				doc = frappe.get_doc("Mode of Payment", {"mode_of_payment":pay_method.name})
				doc.update({
					"mode_of_payment":pay_method.name
				})
			else:
				doc = frappe.get_doc({
					"doctype": "Mode of Payment",
					"mode_of_payment": pay_method.name
					})
			
			if doc:
				doc.flags.ignore_mandatory = 1
				doc.save(ignore_permissions=True)
		frappe.db.commit()




'''
	Get Brand from Bigcommerce
'''

def get_brand(resource_id):
	brand = None
	if not resource_id:
		return  brand
	flag = frappe.db.get_value("Brand", {"bcommerce_brand_id":resource_id}, as_dict=True)
	if flag:
		brand = flag.get("name")
	
	else:
		brand = get_resource("Brands", resource_id)
		if brand:
			doc = frappe.get_doc({
					"doctype": "Brand",
					"description": brand.meta_description,
					"brand": brand.name,
					"bcommerce_brand_id": brand.id
				})
			doc.flags.ignore_mandatory = 1
			doc.save(ignore_permissions=True)
			
			brand = doc.name


	return None if not brand else brand



def sync_bulk_brands():
	
	try:
		min_id = get_last_sync_id("bcommerce_brand_id", "Brand")
		max_id = min_id + 250 #250 is limit of resource list
		brands = get_connection().Brands.all(min_id=min_id, max_id=max_id, limit=250)
		if brands:
			for brand in brands:
				if validate_resource(brand):
					if not frappe.db.get_value("Brand", {"bcommerce_brand_id": brand.id}):
						doc  = frappe.get_doc({
							"doctype": "Brand",
							"description": brand.meta_description,
							"brand": brand.name,
							"bcommerce_brand_id": brand.id
							})
						doc.flags.ignore_mandatory = 1
						doc.save(ignore_permissions=True)

	except Exception as e:
		print "Exception  raised while syncing brand from bigcommerce"
		print frappe.get_traceback()

'''
	Save master data, Customer Group
'''
def get_customer_group(group_id, setting):
	
	group_id = cint(group_id)

	flag = frappe.db.get_value("Customer Group", {"bcommerce_customer_group_id":group_id}, as_dict=True)
	if flag:
		return flag.get("name")
	else:
		cg = get_resurce("CustomerGroups", group_id)
		
		if not cg:
			return setting.customer_group
		
		doc =  frappe.get_doc({
				"doctype":"Customer Group",
				"is_group":0, 
				"parent_customer_group": setting.customer_group,
				"customer_group_name": cg.name,
				"bcommerce_customer_group_id":cg.id
			})
		doc.save(ignore_permissions=True)
		return cg.name





def sync_bulk_customer_group():

	try:
		customer_groups = get_connection().CustomerGroups.all(limit=250)
		if customer_groups:
			for cg in customer_groups:
				if validate_resource(cg):
					doc =  frappe.get_doc({
						"doctype":"Customer Group",
						"is_group":0, 
						"parent_customer_group": setting.customer_group,
						"customer_group_name": cg.name,
						"bcommerce_customer_group_id":cg.id
					})
					doc.save(ignore_permissions=True)
					

	except Exception as e:
		print frappe.get_traceback()	
	
 

