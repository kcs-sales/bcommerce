
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
'''
	Developer Navdeep Ghai
	Email navdeep@korecent.com
'''

import frappe
from frappe import _, throw
from frappe.utils import cint, cstr, flt
from bcommerce.utils.api import get_connection, is_exists
from bcommerce.utils.logger import get_logger, make_logs
from bcommerce.utils.products import has_variants, save_product, sync_product
from erpnext.controllers.item_variant import create_variant
from bcommerce.utils.customers import sync_customer
from bcommerce.exceptions import BcommerceOrderError, ProductDoesNotExist, CustomerDoesNotExist
from bcommerce.utils.status import get_order_status, update_order_status
from erpnext.selling.doctype.sales_order.sales_order import  make_delivery_note, make_sales_invoice
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry


'''
	Sync Single order or update Order, Delivery Note, Sales Invoice
'''
def sync_order(order_id, setting):
	if not order_id:
		return

	sales_order = frappe.db.get_value("Sales Order", filters={"bcommerce_order_id":order_id}, as_dict=True)

	if sales_order:
		return sales_order.get("name")

	else:
		try:
			conn = get_connection()
			order = conn.Orders.get(id=order_id)
			save_order(order, setting, conn)

		except Exception as e:
			msg = "{0}, {1}".format("Error while sycing order", frappe.get_traceback())
			make_logs("Failed", "Order", message=msg)


'''
	Sync Bulk order, limit 250, at same time only 250 orders will be synced

'''
def sync_bulk_orders(orders, setting, conn):
	ordr = None
	for order in orders:
		try:
			ordr = order
			save_order(order, setting, conn)
	
		except:
			msg = _("Error while saving Order {0}".format(ordr.id))
			make_logs("Failed", "Order", msg, ordr.id)


'''
	Save sales order
'''	
def save_order(order, setting, conn):	
	products = get_products(order, setting, conn)
	customer = sync_customer(order.customer_id, setting)
	taxes = get_shipping_charges_and_taxes(order, setting)
	doc = create_sales_order(order, products, customer, taxes, setting)
	

'''
	Mapping ERPNext item to order, if item does not exists in ERPNext system, 
	then new request will be initialize to get the missing product from bigcommerce
'''
def get_products(order, setting, conn):

	products  = order.products()
	items = frappe._dict()
	for product in products:	
		if has_variants(product):
			variants = get_variants(product, setting, order,  conn)
			for variant in variants:
				if not items.has_key(variant.get("item_code")):
					items[variant.get("item_code")]	= variant
					items[variant.get("item_code")]['qty']  = product.quantity
				else:
					items[variant.get("item_code")]['qty'] += product.quantity	
		else:
			item = get_item(product, setting, order, conn)
			if not item:
				continue	
			if not items.has_key(item.get("item_code")):
				items[item.get("item_code")] = item
			else:
				items[item.get("item_code")]['qty'] += product.quantity
				

	items_list = []
	for key, val in items.iteritems():
		items_list.append(val)
	return items_list


'''
	Map cost center to every item linked with Sales Order
'''
def set_cost_center(items, setting):
	
	for item in items:
		item.cost_center = setting.cost_center



'''
	Parse the items from product using option_set_id and Options selected within product
'''
def get_item(product, setting, order, conn):
	
	item = frappe.db.get_value("Item", filters={"bcommerce_product_id": product.product_id, "has_variants":0}, 
					fieldname=["default_warehouse", "item_code", "item_name"], as_dict=True)
	if item:
		item.update({"qty": product.quantity})
	else:
		sync_product(product.product_id, setting)
		item =  frappe.db.get_value("Item", filters={"bcommerce_product_id": product.product_id},
				fieldname=["default_warehouse", "item_code", "item_name"], as_dict=True)

		if not item:	
			msg = _("Item {0} does not exists in ERPNext System, Please try to sync the Item {1},  and then \
					try to sync Order {2} manually".format(product.name, product.name, order.id))
			make_logs("Failed", "Product", msg, order.id)

	return item
	



'''
	Items object needed, because this array will be modify if item
	already exists in items array
'''
def get_variants(product, setting, order, conn):
		
	flag = frappe.db.get_value("Item", filters={"bcommerce_product_id": product.product_id, "has_variants":1}, as_dict=True)
	item_list = []
	if not flag:
		sync_product(product.product_id, setting)
		flag = frappe.db.get_value("Item", filters={"bcommerce_product_id": product.product_id, "has_variants":1}, as_dict=True)
		if not flag: # Still unable to sync product from Bigcommerce
			#Product has been delete from Bigcommerce
			return item_list
	item_code = flag.get("name")
	for attr in product.product_options:
		attr_val = attr.get("display_value")
		attr_name = get_attribute_name(product.option_set_id)
		
		item = frappe.db.sql("""SELECT I.item_code, I.item_name, I.default_warehouse FROM `tabItem`  I INNER JOIN 
					`tabItem Variant Attribute` IA ON I.item_code=IA.parent WHERE variant_of= %(variant_of)s 
					AND IA.attribute= %(attr)s AND IA.attribute_value=%(attr_value)s """, 
					{"variant_of":item_code, "attr": attr_name, "attr_value":attr_val}, as_dict=True)
		item_list.extend(item)
	
	if not item_list:
		msg = _("Item {0}, does not exists in ERPNext Sytem, Please sync Item {1}, and then try to sync \
				Order {2} manually (Item with Options, That is Item Variant) ")
		msg.format(product.name, product.name, order.id)
		raise ProductDoesNotExist(msg)
 
	return item_list	
	

'''
	Get attribute from ERPNext, Attribute saved in ERPNext using option_set_id
	field of product
'''
def get_attribute_name(opt_set_id):
	
	flag = frappe.db.get_value("Item Attribute", {"bcommerce_optionset_id": opt_set_id}, "attribute_name", as_dict=True)
	return flag.get("attribute_name") if flag else None


'''
	Submit sales order in database if everything is fine
	else save the sales order in database, so that later user can add the
	items manually then submit the sales order
'''
def create_sales_order(order,  items, customer, taxes, setting):


	exception = validate_mandatory(order, items, customer)
	order_status = get_order_status(order.status_id)
	doc = None
	if not frappe.db.get_value("Sales Order", filters={"bcommerce_order_id":order.id}):
		doc  = frappe.get_doc({
			"doctype": "Sales Order",
			"selling_price_list": setting.selling_price_list,
			"items": items,
			"naming_series":setting.bcommerce_naming,
			"bcommerce_order_id": order.id,
			"bcommerce_order_status": order_status.get("name"),
			"bcommerce_status_id":order.status_id,
			"customer": customer,
			"taxes": taxes,
			"delivery_date": frappe.utils.nowdate(),
			"trasaction_date": frappe.utils.nowdate(),
			"order_type": "Sales",
			"total": order.total_ex_tax,
			"apply_discount_on": "Grand Total",
			"discount_amount":flt(order.discount_amount)
			})
		set_cost_center(doc.items, setting)
		doc.flags.ignore_mandatory = 1
		doc.save(ignore_permissions=True)
		if not exception:
			# If  order has all the required data, then submit the order
			# If Order have some missing fields then just save the order, later user can add the data
			doc.submit()
		
		frappe.db.commit()
	else:
		name = frappe.db.get_value("Sales Order", filters={"bcommerce_order_id":order.id}, as_dict=True)
		doc = frappe.get_doc("Sales Order", name.get("name"))
	
	status = order_status.get("name")

	'''
	if status == "Shipped":
		# Create Delivery Note
		create_delivery_note(doc, setting)

	elif status == "Completed":
		# Create Sales Invoice
		create_delivery_note(doc, setting)
		create_sales_invoice(doc, setting)
	'''

	frappe.db.commit()


'''
	Validate mandatory to ensure there is no mandatory missing values in sales order
'''
def validate_mandatory(order, items, customer):

	exception = False
	# This is when there is  no single Item, Customer in ERPNext System selected with Order
	if not customer:
		exception = True
		message = _("Customer with ID: {0}  is missing  within Order ID: {1}".format(order.customer_id, order.id))
	
	elif not items:
		exception = True
		message = _("Items are missing within Orders ID {0}".format(order.id))

	elif not items and not customer:
		exception = True
		message = _("Items and Customer ID: {0} is missing within Order ID: {1}".format(order.customer_id,order.id))
		
	return exception	

'''
	Get Discount to apply discount to sales order
'''
def get_discount(order):

	discount = get_discount(order)
	discount += order.discount_amount
	return discount 


'''
	Apply coupons discount if any linked with order in bigcomerce
'''
def get_coupons_discount(order):
	discount = 0.0
	for coupon in order.coupons():
		if (counpon and  isinstance(coupon, dict) and coupon.has_key("amount")):
			discount += coupon.amount

	return discount


'''
	Apply shipping charges if  shipping charges prodvided with order in bigcommerce
'''

def get_shipping_charges_and_taxes(order, setting):

	'''
		It'll include handling and shipping cost for order
	'''

	taxes = []
	'''
		Total Taxes if any
	'''
	if flt(order.total_tax):
		for tax in order.taxes():
			if (tax and isinstance(tax, dict) and tax.has_key("name")):
			
				taxes.append({
					"charge_type": _("On Net Total"),
					"account_head": get_tax_account_head(tax),
					"description": "{0} - {1}".format(tax.name, flt(tax.rate) * 100.00),
					"rate": flt(tax.rate) * 100.00,
					"cost_center": setting.cost_center
				})
		
	'''
		Shipping Charges if any
	'''	
	if flt(order.shipping_cost_inc_tax):
		taxes.append({
			"charge_type": _("Actual"),
			"account_head": get_shipping_account_head(),
			"description": "{0} - {1}".format("Shipping Charges", order.shipping_cost_inc_tax),
			"tax_amount": flt(order.shipping_cost_inc_tax),
			"cost_center": setting.cost_center
		})

	'''
		Handling cost if any
	'''
	if flt(order.handling_cost_inc_tax):
		taxes.append({
			"charge_type": _("Actual"),
			"account_head": get_shipping_account_head(),
			"desciption": "{0} = {1}".format("Handling Charges", order.handling_cost_inc_tax),
			"tax_amount": flt(order.handling_cost_inc_tax),
			"cost_center": setting.cost_center
		})

	return taxes


'''
	Have to setup the shipping account for shipping charges,
	there is no shipping name with shipping charges within order
'''

def get_shipping_account_head():
	
	flag = frappe.db.get_value("Bcommerce Tax Account", filters={"parent": "Bcommerce Setting", "bcommerce_tax": "Shipping"},
				fieldname="bcommerce_tax_account", as_dict=True)

	if not flag:
		pass
		#logs
		
	return flag.get("bcommerce_account_head") if flag else None



'''
	Tax account will be fetched from Big Commerce master setting
'''
def get_tax_account_head(tax):	
	acc_head = frappe.db.get_value("Bcommerce Tax Account", filters={"parent": "Bcommerce  Order Default", 
				"bcommerce_tax": tax.name}, fieldname="bcommerce_tax_account", as_dict=True)
	if not acc_head:
		pass
		# Logs
	acc_head = acc_head.get("bcommerce_tax_account") if acc_head else None









# Update hooks related functions
'''
	This function will be called from webhooks when  order get update on bigcommerce
'''
def update_order(order_id, prev_status_id, new_status_id):

	name = frappe.db.get_value("Sales Order", filters={"bcommerce_order_id":order_id}, as_dict=True)
	setting = frappe.get_doc("Bcommerce Setting", "Bcommerce Setting")
	if not name:
		sync_order(order_id, setting)	
	else:
		so = frappe.get_doc("Sales Order", name.get("name"))
		status = get_order_status(new_status_id)
		if so.bcommerce_status_id == new_status_id:
			return
		update_order_status(name.get("name"), status.get("name"), new_status_id)
	
		if status.get("name") == "Shipped":
			create_delivery_note(so, setting)
		elif status.get("name") == "Completed":
			create_delivery_note(so, setting)
			create_sales_invoice(so, setting)


'''
	Create Deivery Note when order status on bigcommerce become Shipped
'''	
def create_delivery_note(so, setting):

	if not frappe.db.get_value("Delivery Note", filters={"bcommerce_order_id": so.bcommerce_order_id})\
						and so.docstatus == 1:

		doc =  make_delivery_note(so.name)
		doc.naming_series = setting.bcommerce_naming
		doc.flags.ignore_mandatory = 1
		doc.bcommerce_delivery_id = 1
		try:
			doc.save(ignore_permissions=True)
		except:
			print "Error while saving Delivery note, Traceback: {0}".format(frappe.get_traceback())



'''
	Create Sales Invoice when order status on bigcommerce become Completed
'''
def create_sales_invoice(so, setting):


	if not frappe.db.get_value("Sales Invoice", filters={"bcommerce_order_id": so.bcommerce_order_id})\
					and not so.per_billed and so.docstatus == 1:

		doc = make_sales_invoice(so.name)
		doc.naming_series = setting.bcommerce_naming
		doc.flags.ignore_mandatory = 1
		doc.bcommerce_delivery_id = so.bcommerce_order_id
		set_cost_center(doc.items, setting)

		try:
			doc.save(ignore_permissions=True)
			doc.submit()
			#make_payment_entry(doc, setting)
			frappe.db.commit()
		except:
			print "Error while saving sales invoice, Traceback {0}".format(frappe.get_traceback())




'''
	Make Payment entry when order status become Completed on bigcommerce server
'''

def make_payment_entry(si, setting):
	
	payment_entry =  get_payment_entry(si.doctype, si.name, bank_account = setting.cash_bank_account)
	payment_entry.flags.ignore_mandatory = 1
	payment_entry.reference_nubmer = si.name
	payment_entry.reference_date = nowdate()
	payment_entry.submit()

