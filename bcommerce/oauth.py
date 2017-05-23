'''
	Developer Navdeep Ghai
	Email navdeep@korecent.com
	License Korecent Solutions Pvt. Ltd.
'''
import frappe
import urllib, hashlib, hmac, base64
import json
from frappe.utils import get_request_session
import requests
from werkzeug.wrappers import Response
from frappe.website.render import build_response
from frappe.utils.response import redirect
from functools import wraps

@frappe.whitelist(allow_guest=True)
def generate_token():
	from .connection import get_oauth_request, get_oauth_params
	
	form_dict = frappe.local.form_dict
	req = frappe.local.request
	params = get_oauth_params(form_dict)
	if validate_request(form_dict):
		sess = get_oauth_request(req, form_dict)
		url = "https://login.bigcommerce.com/oauth2/token"
		res = sess.post(url, data=params)
		return redirect_request(res)

def validate_request(form_data):
	scope = form_data.get("scope")
	code = form_data.get("code")
	context = form_data.get("context")
	if not scope or not code or not context:
		return False

	elif context:
		store, store_hash = context.split("/")
		if not store or not store_hash:
			return False
	return True



def redirect_request(res):
	try:
		from .bcommerce.doctype.big_commerce_service_request.big_commerce_service_request import save_info
		user_info = res.json()
		info  = save_info(user_info)
		template = frappe.get_template("templates/includes/form.html")
		return frappe.respond_as_web_page("ERPNext Big Commerce",template.render({"doc":info}),primary_label="", 
						primary_action="", fullpage=True)

	except Exception as e:
		print frappe.get_traceback()
	
	

def bwrapper(f):

	def validate_payload(data, client_secret, hmac_signature):
		client_secret = str(client_secret)
		body = base64.b64decode(data)
		hmac_to_verify = base64.b64decode(hmac_signature)

		hash = hmac.new(client_secret, body, hashlib.sha256)
		hmac_cal = hash.hexdigest()

		return hmac_cal == hmac_to_verify


	@wraps(f)
	def wrapper(*args, **kwargs):
	
		try:
			payload = frappe.local.form_dict.get("signed_payload")
			if not payload:
				return

			json_string, hmac_signature = payload.split(".")
			client_secret = frappe.get_doc("Bcommerce App Detail").client_secret
			flag = validate_payload(json_string, client_secret, hmac_signature)
			user_info = json.loads(base64.b64decode(json_string))
			
			return f(data=user_info)	
		except Exception as e:
			print frappe.get_traceback()
	return wrapper

@frappe.whitelist(allow_guest=True)
@bwrapper
def uninstall_app(*args, **kwargs):

	try:
		data = kwargs.get("data")
		if data:
			user = data.get("user")
			flag = frappe.db.get_value("Big Commerce Service Request", {"email_address":user.get("email")}, as_dict=True)
			if flag:
				doc = frappe.get_doc("Big Commerce Service Request", flag.get("name"))
				doc.delete()
				frappe.db.commit()

	except Exception as e:
		print frappe.get_traceback()







@frappe.whitelist(allow_guest=True)
@bwrapper
def login(*args, **kwargs):

	try:
		data = kwargs.get("data")
		if data:
			user = data.get("user")
			print data
		
	except Exception as e:
		print frappe.get_traceback()	


def notify(doc, method=None):
	pass
