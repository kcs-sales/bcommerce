'''

	Developer Navdeep Ghai
	Email navdeep@korecent.com
	License Korcent Solutions Pvt. Ltd.
'''



# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import frappe
from frappe import  _, msgprint, throw
from bcommerce.utils.logger import make_logs
from functools import wraps
import hashlib, base64, hmac
from bcommerce.utils.api import get_connection
from bcommerce.utils.customers import sync_customer, update_customer, disable_customer
from bcommerce.utils.products import disable_product, update_product, sync_product
from bcommerce.utils.status import get_order_status
from bcommerce.utils.orders import update_order, sync_order
from bcommerce.utils import get_resource, validate_resource

def bcommerce_webhook(fn):

	def _hmac_is_valid(body,  secret, hamc_to_verify):

		_hash = hmac.new(body, secret, haslib.sha256)
		hmac_calculated = base64.b64encode(_hash.digest())
	
		return hmac_to_verify == hmac_calculated



	@wraps(fn)
	def wrapper(*args, **kwargs):
		return fn()

	return wrapper		

@bcommerce_webhook
def handle():

	try:
		from bcommerce.utils.api import validate_setting
		print frappe.local.request.headers
		print frappe.local.form_dict
		setting = frappe.get_doc("Bcommerce Setting", "Bcommerce Setting")
		if not validate_setting(setting):
			return
		form_data = frappe.local.form_dict
		data = None
		if form_data and (form_data.has_key("data") and form_data.get("data")) and \
						 isinstance(form_data.get("data"), basestring):
			data =  json.loads(form_data.get("data"))
	
		if not data: # Unable to recieve the data
			return
	
		handle_data(data)
		frappe.db.commit()
	except Exception as e:
		print frappe.get_traceback()


	

def handle_data(data):

	scope = data.get("scope")
	store, resource, status = scope.split("/")
	bcom_data = data.get("data")
	if resource == "order":
	
		resource_id = bcom_data.get("id")
		handle_order(resource_id, status, bcom_data)

	elif resource == "product":	
		resource_id = bcom_data.get("id")
		handle_product(resource_id, status)

	elif resource == "customer":
		resource_id = bcom_data.get("id")
		handle_customer(resource_id, status)


def handle_order(order_id, status,  data):

	setting = frappe.get_doc("Bcommerce Setting", "Bcommerce Setting")
	if status == "created":
		sync_order(order_id, setting)
	'''	
	elif status == "statusUpdated":
		print "updated"
		order_status = data.get("status")
		status_id = order_status.get("new_status_id")
		prev_status_id = order_status.get("previous_status_id")
		update_order(order_id, prev_status_id, status_id)
	'''


def handle_product(product_id, status):

	'''
		sync_product(product_id, setting)
	'''
	setting = frappe.get_doc("Bcommerce Setting" , "Bcommerce Setting")
	if status  == "created":
		sync_product(product_id, setting)

	elif status == "updated":
		update_product(product_id, setting)

	elif status == "deleted":
		disable_product(product_id)


def handle_customer(customer_id, status):
	'''
		get_customer(customer_id, setting)
	'''
	setting = frappe.get_doc("Bcommerce Setting", "Bcommerce Setting")
	if status == "created":
		sync_customer(customer_id, setting)
	elif status == "updated":
		update_customer(customer_id, setting)	
	elif status == "deleted":
		# You can't delete the customer, because there can be multiple sales order registered with customer
		# and you have to delete all the customer, despite you can disable the customer	
		disable_customer(customer_id)

def create_scope(setting):

	conn = get_connection()	
	for scope in ["store/order/created", "store/order/updated", "store/order/archived", "store/order/statusUpdated",
		 "store/product/created", "store/product/updated","store/product/deleted","store/customer/created", 
		 "store/customer/updated","store/customer/deleted", "store/shipment/created", "store/shipment/updated", 
		 "store/shipment/deleted","store/information/updated"]:
		try:
			if not frappe.db.get_value("Bcommerce Webhook", {"webhook_scope":scope}):
				res = conn.Webhooks.create(scope=scope, destination=setting.webhook_url)
				save_web_hook(res)
		except Exception as e:
			msg = "Scope = {0}, URL = {1}, Traceback = {2}".format(scope, setting.webhook_url, frappe.get_traceback())
			make_logs("Failed", "Webhooks", message=msg)

	frappe.db.commit()


def init_hooks(setting):

	if setting.enable and setting.webhook_url:
		validate_webhook_url(setting)


def validate_webhook_url(setting):

	url = setting.webhook_url

	scheme = url[:5]
	if scheme != "https":
		frappe.msgprint(_("You should be use SSL level security for webhooks"))
		return
	create_scope(setting)


def save_web_hook(webhook):

	if validate_resource(webhook):
		
		if not frappe.db.get_value("Bcommerce Webhook", filters={"webhook_id": webhook.id}, as_dict=True):
			frappe.get_doc({
				"doctype": "Bcommerce Webhook",
				"webhook_id": webhook.id,
				"webhook_scope": webhook.scope,
				"webhook_destination": webhook.destination,
				"is_active": webhook.is_active,
				}).save(ignore_permissions=True)

			frappe.db.commit()


def delete_webhooks(id=None):
	
	if id:
		webhook = get_resource("Webhooks", id)
		flag = frappe.db.get_value("Bcommerce Webhook", {"webhook_id":id}, as_dict=True)
		if flag:
			frappe.get_doc("Bcommerce Webhook", flag.get("name")).delete()
		webhook.delete()

	else:
		for webhook in get_connection().Webhooks.all(limit=250):
			if not validate_resource(webhook):
				continue
			flag = frappe.db.get("Bcommerce Webhook", {"webhook_id":webhook.id}, as_dict=True)
			if flag:
				frappe.get_doc("Bcommerce Webhook", flag.get("name")).delete()
			webhook.delete()
			
	
