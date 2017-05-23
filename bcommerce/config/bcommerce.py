
from frappe import _

def get_data():
	return [

		{
			"label": _("Documents"),
			"items":[
					{
					"type": "doctype",
					"name": "Bcommerce Option",
					"description": _("Bcommerce Options/Attribute List")
				},
					{
					"type": "doctype",
					"name": "Bcommerce State",
					"description": _("Bcommerce State")
				}
			]
		},
		{
			"label": _("Tools"),
			"items": [
					{
					"type": "doctype",
					"name": "Bcommerce Setting",
					"description": _("Bcommerce setup with ERPNext")
				},
					{
					"type": "doctype",
					"name": "Bcommerce Manual Sync",
					"description": _("Bcommerce Manual sync for resource which are failed while sycing")
				}
			]
		},
		{
			
			"label": _("Resource Logs"),
			"items":[
					{
					"type": "doctype",
					"name": "Bcommerce Log",
					"description": _("Error while syncing")
					}
			],
		}
	]
