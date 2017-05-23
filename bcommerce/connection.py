# -*- coding: utf-8 -*-
from __future__ import unicode_literals
'''
	Developer Navdeep Ghai
	email navdeep@korecent.com
'''

import frappe
import requests
import json
import time
from frappe.utils import get_request_session
import bigcommerce
from bigcommerce.api import BigcommerceApi, ApiResourceWrapper
from bigcommerce import connection
import bcommerce
from bigcommerce.exception import EmptyResponseWarning, ClientRequestException, ServerException, \
				  RedirectionException, NotLoggedInException


class Connect(connection.Connection):

	def __init__(self, host, auth, api_path='/api/v2/{}'):
		super(Connect, self).__init__(host, auth, api_path)
		self.timeout = 20.0 # Extend the time for slow-connection/local-connection
		self.temp = {}

	def _handle_response(self, url, res, suppress_empty=True):
		from .utils.logger import make_logs
		results = {}
		try:
			results = super(Connect, self)._handle_response(url, res, suppress_empty)
		except Exception, e:
			make_logs("Error", "Sync Error", message=e.message)

		except EmptyResponseWarning, e:
			make_logs("Error", "Sync Error", message=e.message)

		except ClientRequestException, e:
			make_logs("Error", "Sync Error", message=e.message)

		except ServerException, e:
			make_logs("Error", "Sync Error", message=e.message)

		except RedirectionException, e:
			make_logs("Error", "Sync Error", message=e.message)	
	
		return results


	
class OAuthConnect(connection.OAuthConnection):

    def __init__(self, client_id, store_hash, access_token=None, host='api.bigcommerce.com', api_path='/stores/{}/v2/{}'):
		super(OAuthConnect, self).__init__(client_id, store_hash, access_token, host, api_path)
	
    def _handle_response(self, url, res, suppress_empty=True):
		from .utils.logger import make_logs
		results = {}
		try:
			results = super(OAuthConnect, self)._handle_response(url, res, suppress_empty)
		except Exception, e:
			make_logs("Error", "Sync Error", message=e.message)

		except EmptyResponseWarning, e:
			make_logs("Error", "Sync Error", message=e.message)

		except ClientRequestException, e:
			make_logs("Error", "Sync Error", message=e.message)

		except ServerException, e:
			make_logs("Error", "Sync Error", message=e.message)

		except RedirectionException, e:
			make_logs("Error", "Sync Error", message=e.message)	
		
		
		return results

    def _run_method(self, method, url, data=None, query={}, headers={}):
		
	res = None
	try:
		res = super(OAuthConnect, self)._run_method(method, url, data, query, headers)
	
	except Exception as e:
		make_logs("Error", "Sync Error", message= e.message)	
	return res

    def validate_headers(self, res):
	headers = res.headers
	retry_after = headers.get("X-Retry-After")
	if retry_after:
		time.sleep(retry_after) #Retry after seconds		
		


	
class BcommerceAPI(BigcommerceApi):
	
	def __init__(self, host=None, basic_auth=None, client_id=None, store_hash=None, access_token=None):
		super(BcommerceAPI, self).__init__(host, basic_auth, client_id, store_hash, access_token)
		if host and basic_auth:
			self.connection = Connect(host, basic_auth)
		elif client_id and store_hash:
			self.connection =  OAuthConnect(client_id, store_hash, access_token, self.api_service)


	def get_response(self):
		return None


	def __getattr__(self, item):
		return APIResourceWrapper(item, self)

		
class APIResourceWrapper(ApiResourceWrapper):
	
	def __init__(self, resource_class, api):
		super(APIResourceWrapper, self).__init__(resource_class, api)

	
	
	def __getattr__(self, item):
		return lambda *args, **kwargs: (getattr(self.resource_class, item))(*args, connection=self.connection, **kwargs)






def get_oauth_request(req, data):

	sess = get_request_session()
	headers = get_oauth_headers()
	sess.headers.update(headers)

	return sess

def get_oauth_headers():
	headers = {
		"Content-Type": "application/x-www-form-urlencoded"
		}
	return headers


def get_oauth_params(form_data):
	
	
	app_setup = frappe.get_doc("Bcommerce App Detail", "Bcommerce App Detail")
	params ={
		"scope":form_data.get("scope"),
		"code": form_data.get("code"),
		"context": form_data.get("context"),
		"client_id": app_setup.client_id,
		"client_secret": app_setup.client_secret,
		"grant_type": "authorization_code",
		"redirect_uri": "https://erpnextbigcomm.com/api/method/bcommerce.oauth.generate_token"
	}
	return params
	
	
		
	
