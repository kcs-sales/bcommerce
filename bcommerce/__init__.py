# -*- coding: utf-8 -*-
from __future__ import unicode_literals

__version__ = '0.0.1'

import frappe
import bcommerce
from frappe.utils.background_jobs import enqueue
from frappe import _, msgprint
#logger = frappe.logger("bcommerce")
LIMIT = 250
	
@frappe.whitelist()
def sync_store_setting():
	from .utils.api import sync_store_setting
	sync_store_setting()

@frappe.whitelist()
def start_sync():
	from .utils.api import start_sync
	enqueue("bcommerce.utils.api.start_sync", queue="long")
	msgprint(_("Queued for syncing, It may take few minutes to hour, if it's first sync"))	

@frappe.whitelist(allow_guest=True)
def webhooks():
	from .utils.webhooks import handle
	handle()

