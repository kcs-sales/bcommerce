# -*- coding: utf-8 -*-

'''
	Developer Navdeep Ghai
	Email: navdeep@korecent.com
	License Korecent Solution Pvt. Ltd/MIT
'''

from __future__ import unicode_literals
from bcommerce.utils.api import get_connection, is_exists
from frappe.utils import cint, cstr, flt
import sys
import os
import frappe
from frappe import _, throw
from bcommerce.utils.logger import make_logs
from bcommerce.exceptions import BcommerceCustomerError, CustomerDoesNotExist
from bcommerce.utils.store import get_customer_group
from bcommerce.utils import get_resource, validate_resource


'''
	Function can be called  from sales order
	to fetch single customer from bcommerce
'''
def sync_customer(id, setting):
	flag = frappe.db.get_value("Customer", filters={"bcommerce_customer_id": id}, as_dict=True)
	if flag:
		return flag.get("name")

	from bcommerce.utils import get_resource
	customer = get_resource("Customers", id)	
	save_customer(customer, setting, commit=True)	

'''

	Sync Multiple customer
'''
def sync_bulk_customers(customers, setting, conn):
	temp = None
	for customer in customers:
		temp = customer
		if not frappe.db.get_value("Customer", {"bcommerce_customer_id":customer.id}, as_dict=True):
			try:
				save_customer(customer, setting)
			except Exception, e:
				msg = _("Error while saving Customer {0}, Frappe traceback {1}".\
						format(temp.id,frappe.get_traceback()))
				make_logs("Failed", "Customer", msg, temp.id)

'''
	Make customer entry in database
'''
def save_customer(customer, setting, commit=False):

	if not validate_resource(customer):
		return
	full_name  = get_customer_full_name(customer)
	doc =  frappe.get_doc({
			"doctype": "Customer",
			"name": customer.id,
			"__islocal":1,
			"customer_name": full_name,
			"bcommerce_customer_id": customer.id,
			"territory": setting.get("customer_territory"),
			"customer_type": setting.get("customer_type"),
			"customer_group": setting.get("customer_group")
		})
	doc.flags.ignore_mandatory  = 1
	doc.save(ignore_permissions=True)
	update_customer_address(customer, doc, setting)
	if commit:
		frappe.db.commit()
	return full_name

		
def save_customer_address(bcommerce_customer, customer, address, setting, addr_type, addr_title, addr_line1, addr_line2):
			
	doc = frappe.get_doc({
		"doctype": "Address",
		"address_title": addr_title,
		"address_type": addr_type,
		"address_line1": addr_line1,
		"address_line2": addr_line2,
		"city": address.city,
		"state":address.state,
		"phone": address.phone,
		"country": address.country,
		"pincode":address.zip,
		"email_id": bcommerce_customer.email,
			"links":[
				{"link_name": customer.name, "link_doctype":"Customer"}
				]
		}).insert(ignore_permissions=True)



def get_customer_full_name(customer):

	first_name = customer.first_name if customer.first_name else customer.last_name
	last_name = customer.last_name if customer.last_name else ""
	full_name  = "{0} {1}-{2}".format(first_name, last_name, customer.id)
		
	return full_name

def get_address_lines(address):
	addr_1 = address.street_1 if address.street_1 else address.street_2
	addr_2 = address.street_2 if address.street_2 and address.street_2 != addr_1 else ""	

	return addr_1, addr_2
		
def get_address_type_and_title(address, customer):
	
	address_type = _("Billing")
	address_title =  "{0}-{1}".format(customer.customer_name, address.id)
		
	return address_type, address_title




# Below are Webhooks related functions

'''
	Update Customer if someone  update customer on Big commerce
'''
def update_customer(customer_id, setting):
        doc = None
        name = frappe.db.get_value("Customer", filters={"bcommerce_customer_id":customer_id}, as_dict=True)
        if name:
		from bcommerce.utils import get_resource
		customer = get_resource("Customers", customer_id)
		if not customer:
			return
                doc = frappe.get_doc("Customer", name.get("name"))
		full_name = get_customer_full_name(customer)	
		doc.update({
			"full_name": full_name
		})
		doc.save(ignore_permissions=True)
		update_customer_address(customer, doc, setting)
		frappe.db.commit()	
		
	else:
		sync_customer(customer_id, seting)
		
		
	
'''
	Disable Customer when its deleted from bigcommerce server
'''
def disable_customer(customer_id):
	
	customer_name = frappe.db.get_value("Customer", filters={"bcommerce_customer_id":customer_id}, as_dict=True)
	if customer_name:
		doc = frappe.get_doc("Customer", customer_name.get("name"))
		doc.disabled = 1
		doc.sync_with_bcommerce = 0

		doc.bcommerce_customer_id = 0
		doc.save(ignore_permissions=True)
		frappe.db.commit()




'''
	Update Customer Address if address exists in database 
	Otherwise create new address and link address to customer
'''
def update_customer_address(bcommerce_customer, customer, setting):

	from bcommerce.utils import validate_resource
	for address in bcommerce_customer.addresses():
	
		if validate_resource(address):	
			addr_type, addr_title = get_address_type_and_title(address, customer)
			addr_line1, addr_line2 = get_address_lines(address)	
			addr_name = "{0}-{1}".format(addr_title, addr_type)
			update_flag = frappe.db.get_value("Address", {"name": addr_name},as_dict=True)
			if update_flag:
				doc = frappe.get_doc("Address", update_flag.get("name"))
				doc.update({
					"phone":address.phone,
					"city": address.city,
					"state": address.state,
					"country": address.country,
					"email_id": bcommerce_customer.email,
					"pincode": address.zip,
					"address_line1":addr_line1,
					"address_line2": addr_line2
				})
				doc.save(ignore_permissions=True)
		
			else:
				print "save customer address"
				save_customer_address(bcommerce_customer, customer, address, setting, addr_type, 
							addr_title, addr_line1, addr_line2)

