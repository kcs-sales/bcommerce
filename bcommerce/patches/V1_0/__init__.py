

import frappe
from frappe.utils.fixtures import sync_fixtures

def execute():
	sync_fixtures("bcommerce")	
