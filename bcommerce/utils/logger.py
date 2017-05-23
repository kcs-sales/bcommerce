# -*- coding: utf-8 -*-
from __future__ import unicode_literals
'''
	Developer Navdeep Ghai
	Email navdeep@korecent.com
'''

import frappe
from frappe import _, throw
#from bcommerce.exceptions import SyncError


def make_logs(title, resource_type,  message, resource_id=None,  exception=False):

	
	if exception:
		frappe.db.rollback() # Roll back saved Documents
	doc = frappe.get_doc({"doctype":"Bcommerce Log", "title": title,  "message":message, 
				"resource_id":resource_id, "resource_type":resource_type})
	doc.save(ignore_permissions=True)
	frappe.db.commit()

'''
	Logs to  Error to Frappe File just for developer aid
'''
def get_logger(): # Everytime will return the same logger, if its already registered

	return frappe.get_logger("bcommerce")
	
			
