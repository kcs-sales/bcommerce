# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
import bcommerce
import json
from bcommerce.utils.api import get_connection

'''

	Developer Navdeep Ghai
	Email navdeep@korecent.com




File used to  sync ERPNext resource with Big Commerce

'''




'''
	Sync Customer with Big Commerce
'''
def create_customer(doc):

	if doc.sync_with_bcommerce:
		conn = get_connection()
		name = doc.name
		if  not doc.bcommerce_customer_id:
			try:
				customer = conn.Customers.create("first_name"=doc.customer_name,
								"last_name"="",
								"email"=doc.email
								)	
				doc = frappe.get_doc("Customer", name)
				doc.bcommerce_customer_id = customer.id
				doc.flags.ignore_mandatory = 1
				doc.save(ignore_permissions=True)
				frappe.db.commit()	
			except Exception as e:
				print e.message



def create_product(doc, method=None):

	print doc.as_dict()
	if doc.sync_with_bcommerce:
		print doc.as_dict()


def create_order(doc):

	pass
