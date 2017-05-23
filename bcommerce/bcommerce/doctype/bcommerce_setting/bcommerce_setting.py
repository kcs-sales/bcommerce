# -*- coding: utf-8 -*-
# Copyright (c) 2015, Korecent and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _, msgprint, throw
from bigcommerce.api import BigcommerceApi
from bcommerce.utils.api import get_connection
from bcommerce.exceptions import BcommerceSetupError
from bcommerce.utils.store import sync_store
class BcommerceSetting(Document):

	def  validate(self):
		self.check_point()
		self.init_hooks()
	
	def check_point(self):
		if self.enable:
			self.validate_credentials()
			return 
		else:
			msgprint(_("Please check the enable button to start the syncing"))
			return 

	def validate_credentials(self):
		flag = self.authentication_type
		if flag == "Basic Authentication":
			self.validate_basic_auth()
		else:
			self.validate_oauth()	

	def validate_basic_auth(self):
	
		host = self.host
		token = self.token
		app_name = self.app_name
		basic_auth = (app_name, token)
		
		if not host or  not token or not app_name:
			raise BcommerceSetupError(_("Invalid credentials"))
		try:
			api = BigcommerceApi(host, basic_auth=basic_auth)
			store = api.Store.all()
			sync_store(store, False, self)
			frappe.msgprint(_("Success! You're using Basic Authorization Method"))
		except BcommerceSetupError, e:	
			throw(_(e.message))
	

	def validate_oauth(self):
		
		if not self.client_id or not self.access_token or not self.store_hash:
			throw(_("Client ID, Client Secret and Access Token, all the mandatory field"))


		try:
			api = BigcommerceApi(client_id=self.client_id, access_token=self.access_token, store_hash=self.store_hash)
			store = api.Store.all()
			sync_store(store, False, self)
		
			frappe.msgprint(_("Success!  You're using OAuth Authorization Method"))

		except Exception as e:
			throw(_(e.message))


	def init_hooks(self):
		from bcommerce.utils.webhooks import init_hooks
		init_hooks(self)
