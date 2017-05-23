# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe

__all__ = ['BcommerceOAuthError', 'BcommerceBasicAuthError']

class BcommerceException(Exception):
	
	def __init__(self, message):
		self.message = message


class SyncError(BcommerceException): pass

class BcommerceSetupError(BcommerceException): pass

class BcommerceOrderError(BcommerceException): pass

class BcommerceProductError(BcommerceException): pass

class BcommerceCustomerError(BcommerceException): pass

class ProductDoesNotExist(BcommerceException): pass

class CustomerDoesNotExist(BcommerceException): pass

class BcommerceOptionError(BcommerceException): pass

class OptionDoesNotExists(BcommerceException): pass

class BcommerceOptionSetError(BcommerceException): pass

class OptionSetDoesNotExist(BcommerceException): pass

class BcommerceConnectionError(BcommerceException): pass
