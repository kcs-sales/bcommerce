# -*- coding: utf-8 -*-
from __future__ import unicode_literals
'''
	Developer Navdeep Ghai
	Email navdeep@korecent.com
'''

import frappe
import bcommerce
from frappe.utils import cint, cstr, flt, nowdate
from frappe import _, msgprint, throw


'''
	Order status
'''
def get_order_status(status_id):
	status  = {	
			0:
				{"name":"Incomplete", "order":0},
			1:
				{ "name":"Pending", "order":1},	
			2:
				{ "name":"Shipped", "order":2},
			3:
				{ "name":"Partially Shipped", "order":3},
			4:
				{"name":"Refunded", "order":4},
			5:
				{ "name":"Cancelled", "order":5},
			6:
				{"name":"Declined", "order":6},
			7:
				{ "name":"Awaiting Payment", "order":7},
			8:
				{ "name":"Awaiting Pickup", "order":8},
			9:
				{"name":"Awaiting Shipment", "order":9},
			10:
				{ "name":"Completed", "order":10},
			11:
				{"name":"Awaiting Fulfillment", "order":11},
			12:
				{"name":"Manual Verificate Required", "order":12},
			13:
				{ "name":"Disputed", "order":13},
		}
	


	return status.get(cint(status_id)) 


'''
	Update order status when customer/admin update the status of order in bigcommerce server
'''
def update_order_status(so_name, status_name, status_id):
	data = {"so_name":so_name, "status":status_name, "status_id":status_id}
	print data
	frappe.db.sql("""Update `tabSales Order` SET bcommerce_order_status=%(status)s, bcommerce_status_id=%(status_id)s \
			WHERE name=%(so_name)s AND docstatus=1 """, data)
	
