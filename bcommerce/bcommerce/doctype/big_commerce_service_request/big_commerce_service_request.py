# -*- coding: utf-8 -*-
# Copyright (c) 2017, Korecent and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class BigCommerceServiceRequest(Document):
	
	def validate(self):
		pass




def save_info(info):

        user = info.get("user")
	doc = None
        flag = frappe.db.get_value("Big Commerce Service Request", {"email_address": user.get("email")},as_dict=True)
        if flag:
                doc = frappe.get_doc("Big Commerce Service Request", flag.get("name"))
		doc.update({
			"email_address": user.get("email"),
			"user_id": user.get("id"),
			"user_name": user.get("username"),
			"context": info.get("context"),
			"scope": info.get("scope"),
			"access_token": info.get("access_token")
		})
	else:
        	doc = frappe.get_doc({
                	"doctype":"Big Commerce Service Request",
               		"email_address": user.get("email"),
                	"user_id": user.get("id"),
                	"username": user.get("username"),
                	"context": info.get("context"),
                	"scope": info.get("scope"),
                	"access_token": info.get("access_token"),
               		})
	if doc:
        	doc.flags.ignore_mandatory = 1
        	doc.save(ignore_permissions=True)
        frappe.db.commit()
        return doc

