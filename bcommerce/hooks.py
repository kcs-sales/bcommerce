# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "bcommerce"
app_title = "Bcommerce"
app_publisher = "Korecent"
app_description = "bcom"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "navdeep@korecent.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/bcommerce/css/bcommerce.css"
# app_include_js = "/assets/bcommerce/js/bcommerce.js"

# include js, css files in header of web template
# web_include_css = "/assets/bcommerce/css/bcommerce.css"
# web_include_js = "/assets/bcommerce/js/bcommerce.js"

# Home Pages
# ----------
fixtures = ["Custom Field", "Custom Script", "Custom DocPerm"]
# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "bcommerce.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "bcommerce.install.before_install"
after_install = "bcommerce.after_install.test"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "bcommerce.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
 	"Customer": {
		"after_save": "bcommerce.utils.create_resources.create_customer"
	},
	"Item":{
		"after_save": "bcommerce.utils.create_resources.create_product",
	},
	"Sales Order":{
		"after_save": "bcommerce.utils.create_resources.create_order"
	},
	"Big Commerce Service Request":{
		"on_update": "bcommerce.oauth.notify"
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"hourly": [
		"bcommerce.utils.api.start_sync"
 	]
}
# 	"daily": [
# 		"bcommerce.tasks.daily"
# 	],
# 	"hourly": [
# 		"bcommerce.tasks.hourly"
# 	],
# 	"weekly": [
# 		"bcommerce.tasks.weekly"
# 	]
# 	"monthly": [
# 		"bcommerce.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "bcommerce.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "bcommerce.event.get_events"
# }

