
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
'''
	Developer Navdeep Ghai
	Email navdeep@korecent.com
	License Korecent Solution Pvt. Ltd.
'''

import frappe
from frappe import _, msgprint, throw
from bcommerce.utils.api import get_connection, is_exists
from erpnext.controllers.item_variant import create_variant
from bcommerce.utils.logger import make_logs
from bcommerce.exceptions import BcommerceProductError, CustomerDoesNotExist, OptionSetDoesNotExist 
from frappe import ValidationError
from bcommerce.utils import get_resource, validate_resource
from bcommerce.utils.store import get_brand, sync_bulk_brands

'''
	Sync Product if not already exists in local ERPNext system
	This function is to aid to sync product while create order
	If product does not exists on Local ERPNext System
'''	
def sync_product(id, setting):
	
	flag = frappe.db.get_value("Item", {"bcommerce_product_id":id}, as_dict=1)
	if flag:
		return flag.get("name")
	
	else:
		sync_options()
		sync_bulk_brands()
		conn = get_connection()
		product = get_resource("Products", id)
		if not product:
			return
		save_product(product, setting, conn)

'''
	This is for Order Products 
'''
def has_variants(product):
	return True if len(product.product_options) >= 1 else False


'''
	Traverse bulk synced products
'''
def sync_bulk_products(products, setting, conn):
	
	sync_options()
	sync_bulk_brands()
	temp = None
	for product in products:
		temp = product
		if not frappe.db.get_value("Item", {"bcommerce_product_id": product.id}):
			try:
				save_product(product, setting, conn)

			except:
				msg = _("Error while saving Product {0}, Frappe traceback {1}".\
						format(temp.id, frappe.get_traceback()))
				make_logs("Failed", "Product", msg, temp.id)

'''
	Entry point for create items/variants
'''
def save_product(product, setting, conn):

	if product.option_set_id:
		save_variants(product, setting, conn)
	else:
		create_item(product,setting, False, None, conn)	


'''
	Parse all the product variant as these variant are
	Refer to options on BigCommerce system
'''
def save_variants(product, setting, conn, update=False):
		
	attributes = get_item_attributes(product)
	create_item(product, setting, True, attributes, conn, update)


'''
	Insert   Item  entry in database
'''
def create_item(product, setting,  has_variants=False, attributes=None, conn=None, update=False):

	brand = get_brand(product.brand_id)
	if has_variants and not attributes:
		message = _("There is problem with Product {0}, traceback:  {1}".format(product.name,
				"Item  has no attribute"))
		make_logs("Failed", "Product", message, product.id, False)
		return
	doc = None
	filters = {}
	if has_variants:
		filters["has_variants"] = 1
	filters["bcommerce_product_id"] = product.id

	product_name = frappe.db.get_value("Item", filters, as_dict=True)
	if not product_name:
		image = get_image_url(product)
		doc = frappe.get_doc({
				"doctype": "Item",
				"uom": _("Nos"),
				"title": product.page_title,
				"item_code": product.name,
				"is_stock_item":1,
				"image": image,
				"stock_keeping_unit":product.sku,
				"height": product.height,
				"net_weight": product.weight,
				"width": product.width,
				"depth":product.depth,
				"bcommerce_product_id": product.id,
				"sync_with_bcommerce":1,
				"default_warehouse": setting.warehouse,
				"item_group": setting.item_group,
				"has_variants": has_variants,
				"attributes": attributes,
				"brand": brand,
				"description": product.description,
			
			})
		doc.save(ignore_permissions=True)
		
	else:
		doc = frappe.get_doc("Item", product_name.get("name"))
		image = get_image_url(product)
		doc.update({
			"title":product.page_title,
			"attributes":attributes,
			"brand": brand,
			"image":image,
			"stock_keeping_unit":product.sku,
			"depth":product.depth,
			"width": product.width,
			"height": product.height,
			"net_weight": product.weight,
			"item_group":setting.item_group,
			"default_warehouse":setting.warehouse,
			"description":product.description
			})
		doc.save(ignore_permissions=True)
	if has_variants:
		create_variants(attributes, doc, product, setting)
	else:
		create_item_price(product, doc, setting)
	

'''
	Create Variant function to traverse all the sub options in 
	OptionSet and then create the Item Attribute
'''
def create_variants(attribute, template, product, setting):
	attr_name = attribute[0].get("attribute") if len(attribute) >= 1 else None
	if not attr_name:
		return
	options = frappe.db.get_values("Item Attribute Value", filters={"parent": attr_name},
			fieldname=["attribute_value", "abbr"], as_dict=True)
	
	for opt in options:
		args = {}
		item_code = "{0}-{1}".format(template.item_code, opt.get("abbr"))
		if not frappe.db.get_value("Item", item_code):
			args[attr_name] = opt.get("attribute_value")
			doc = create_variant(template.item_code, args)
			doc.save(ignore_permissions=True)
			create_item_price(product, doc, setting)
		else:
			doc = frappe.get_doc("Item", item_code)
			item_name = "{0}-{1}".format(product.name, opt.get("abbr"))
			doc.update({
				"item_name": item_name
			})
			doc.save(ignore_permissions=True)
			create_item_price(product, doc, setting)


'''
	Parse the Product Options as  Item attributes in ERPNext
	Then save the item attributes and return the attributes
	Which will further link to Item Master table to create Variants
'''
def get_item_attributes(product):

	flag = frappe.db.get_value("Item Attribute", filters={"bcommerce_optionset_id":product.option_set_id}, as_dict=1)
	if flag:
		return [frappe.get_doc({
					"doctype": "Item Variant Attribute",
					"attribute": flag.get("name")
				})]
	else:
		get_optionset(id=product.option_set_id)
		flag = frappe.db.get_value("Item Attribute", filters={"bcommerce_optionset_id":product.option_set_id}, as_dict=1)
		if flag:
			return [frappe.get_doc({
					"doctype": "Item Variant Attribute",
					"attribute": flag.get("name")
					})]

'''
	Get standard images URL from bigcommerce and map it to Item
'''
def get_image_url(product):
	
	url = ""
	images = product.images()
	if isinstance(images, list):
		if len(images) >= 1:
			image = images[0]
			url = image.standard_url
		
	return url
			
'''
	Buying/Selling Item Prices
'''
def create_item_price(product, item, setting):

	item_code, item_name  = item.item_code, item.item_name
	create_price(item_code, item_name, product.price, setting.selling_price_list, "selling")
	create_price(item_code, item_name, product.cost_price, setting.buying_price_list,  "buying")
		
'''
	Set Item price for item
'''
def create_price(item_code, item_name, item_price, price_list, price_type):
	flag =frappe.db.get_value("Item Price", filters={"item_code":item_code, "price_list":price_list}, as_dict=True)
	
	
	if not flag:
		frappe.get_doc({
			"doctype": "Item Price",
			"item_name": item_name,
			"item_code": item_code,
			"price_list": price_list,
		 	 price_type:1,
			"price_list_rate":item_price
		
		}).save(ignore_permissions=True)
	else:
		doc = frappe.get_doc("Item Price", flag.get("name"))
		doc.update({
			"price_list_rate": item_price
		}).save(ignore_permissions=True)


'''
	Get OptionSet
'''
def get_optionset(id):

	try:
		resource = get_resource("OptionSets", id)
		options_values = get_options_values(resource)
	
		create_item_attribute(resource, options_values)	
	except Exception as e:
		msg = "{0} {1} {2}".format("OptionSet with id ", id, "Doesn't exist")
		make_logs("Failed", "OptionSet", message=msg)


'''
	Get OptionSets Options Value
'''
def get_options_values(optionset):

	options_values = frappe._dict()	
	for option in optionset.options():
		if option and (isinstance(option, dict)):
		
			flag = frappe.db.get_value("Bcommerce Option", {"option_id":option.option_id}, as_dict=True)
			if not flag:
				sync_options(id=option.option_id)
			flag = frappe.db.get_value("Bcommerce Option", {"option_id":option.option_id}, as_dict=True)
			if not flag:
				msg = "{0} {1} {2}".format("Option with id ", option.option_id, " Does not exists")
				make_logs("Failed", "Option", message=msg)
				continue	
			values = frappe.db.get_values("Bcommerce Option Value", {"parent":flag.get("name")}, 
					"bcommerce_option_value_name", as_dict=1)
			if not options_values.has_key(option.option_id):
				options_values[option.option_id] = values
		
	values = []
	if options_values:
		for key, val in options_values.iteritems():
			values.extend(val)	
	return values


'''
	Create Item Attribute
'''
def create_item_attribute(optionset, options):	

	options = remove_duplicate_attr(options)		
	frappe.get_doc({
		"doctype": "Item Attribute",
		"attribute_name": optionset.name,
		"bcommerce_optionset_id": optionset.id,
		"item_attribute_values":[{
			"abbr": opt,
			"attribute_value": opt
		} for opt in options
	]}).save(ignore_permissions=True)


	

'''
	Remove duplicate values from  attributes list

'''
def remove_duplicate_attr(options):
	
	attrs = []
	for attr in options:
		if attr.get("bcommerce_option_value_name") not in attrs:
			attrs.append(attr.get("bcommerce_option_value_name"))

	return attrs
		
'''
	Remove Duplicate values from OptionSet Options -> values
'''
def remove_duplicate_options(values):
	
	values_list = []
	for val in values:
		if not val.get("bcommerce_option_value_name") in values_list:	
			values_list.append(val.get("bcommerce_option_value_name"))

	return values_list	



'''
	Sync Options
'''		
def sync_options(id=None, optionset_id=None):
	try:
		conn = get_connection()
		if  id and not frappe.db.get_value("Bcommerce Option", filters={"option_id": id}):
			option = conn.Options.get(id)
			values = get_option_values(option)	
			if len(values) >= 1:
				save_option(option, values)	
		else:
			options = conn.Options.all(limit=250)
			for option in options:
				id = option.id
				if  not frappe.db.get_value("Bcommerce Option", {"option_id":option.id}):
					values = get_option_values(option)
					if len(values) >= 1:
						save_option(option, values)
	
	except:
		msg = _("Error while saving Option {0}, Frappe traceback {1}".format(id, frappe.get_traceback()))
		make_logs("Failed", "Option", message=msg)

'''
	Get values from Option
'''
def get_option_values(option):
	values = []	
	if option and (isinstance(option, dict) and hasattr(option, "values")):
		values = option.values()
		if values and isinstance(values, basestring):
			values = []
		
	return values	

'''
	Save Option
'''
def save_option(option, values):

	if not option or not  isinstance(values, list):
		return
	
	if not frappe.db.get_value("Bcommerce Option", {"option_id": option.id}):
		doc = frappe.get_doc({
			"doctype": "Bcommerce Option",
			"option_name": option.name,
			"option_display_name": option.display_name,
			"option_id": option.id,
			"values":[{
				"bcommerce_option_value_value":opt.value,
				"bcommerce_option_value_name": opt.label,
				"bcommerce_option_value_id": opt.id
				} for opt in values
			]})

		doc.save(ignore_permissions=True)










# 	Below all functions are related to hooks events	

'''
	Disable Product if someone delete  product from Big Commerce Store
'''

def disable_product(product_id):
	
	name = frappe.db.get_value("Item", {"bcommerce_product_id": product_id}, as_dict=True)
	if name:
		doc = frappe.get_doc("Item",  name.get("name"))
		doc.sync_with_bcommerce = 0
		doc.bcommerce_product_id = 0
		doc.disabled = 1
		doc.save(ignore_permissions=True)		
		frappe.db.commit()

'''
	Called while calling webhooks from Big Commerce Server
'''
def update_product(product_id, setting):
	if not frappe.db.get_value("Item", {"bcommerce_product_id": product_id}, as_dict=True):
		sync_product(product_id, setting)

	else:
		product = get_resource("Products", product_id)
		if not product:
			return
		doc = None
		has_variant = True if product.option_set_id else False
		if has_variant:
			sync_options()
			template = frappe.db.get_value("Item", {"bcommerce_product_id":product.id, "has_variants":1}, as_dict=True)
			if not template:
				template = update_template(product)
				if not template:
					return

			variants = frappe.db.sql("""SELECT item_code, item_name, name FROM `tabItem` WHERE variant_of=%(variant_of)s \
							""", {"variant_of":template.get("name")}, as_dict=True)

			save_variants(product, setting, None, True)
			update_item(product, variants, setting)
		else:
	
			name = frappe.db.get_value("Item", filters={"bcommerce_product_id":product.id,"has_variants":0},
							fieldname=["name", "item_code", "item_name"],  as_dict=True)
			if name:
				create_item(product, setting)
				update_item(product, name, setting)

'''
	Update Item Price if user/admin made changes in Prices
'''
def update_item(product, items, setting):
	
	if isinstance(items, list):
		for item in items:
			update_price(product, item, setting)
			
	else:
		update_price(product, items, setting)
		
	frappe.db.commit()
			
		

def update_price(product, item, setting):
	item_code, item_name = item.get("item_code"), item.get("item_name")

	create_price(item_code, item_name, product.cost_price, setting.buying_price_list, "buying")
	create_price(item_code, item_name, product.price, setting.selling_price_list, "selling")	


def update_template(product):

	name = frappe.db.get_value("Item", {"bcommerce_product_id":product.id}, as_dict=True)
	if name:
		template = frappe.get_doc("Item", name.get("name"))
		attributes = get_item_attributes(product)
		template.update({"has_variants":1, "attributes": attributes})
		template.save(ignore_permissions=True)
		frappe.db.commit()
		return name

