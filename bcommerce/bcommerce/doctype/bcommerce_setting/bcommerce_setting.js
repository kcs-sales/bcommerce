// Copyright (c) 2016, Korecent and contributors
// For license information, please see license.txt

frappe.provide("bcommerce.bcommerce_setting");

frappe.ui.form.on("Bcommerce Setting", "onload", function(frm){

	bcommerce.bcommerce_setting.setup_queries(frm);

});

$.extend(cur_frm.cscript, {
	onload: function(doc){
		var me = this;
		console.log(me);
		me.authentication_type(doc);
	
	},
	refresh: function(doc) {
		
		cur_frm.add_custom_button(__("Sync Store Setting"), function(){
			if(doc.authentication_type == "Basic Authentication"){
				if (!doc.app_name || !doc.token || !doc.host){
					frappe.msgprint(__("Mandatory Fields App Name, Token, Host"));
					return

				}
				else{
					frappe.call({
						method: "bcommerce.sync_store_setting",
						args: {},
						callback: function(res){
							alert("navdeep");
							cur_frm.refresh();
						}
					});
				}
			}
			else{
				if(!doc.client_id || !doc.access_token || !doc.store_hash){
					frappe.msgprint(__("You are using OAuth Authentication method, Kindly entry data in [Client ID, Access Token, Store Hash field]"));
					return
				
				}
				else{
					frappe.call({
						method: "bcommerce.sync_store_setting",
						args: {},
						callback: function(res){
							cur_frm.refresh();
						}
					});

				}
			}
				
		}).addClass("btn-primary");

		cur_frm.add_custom_button(__("Start Sync"), function(){
			
				frappe.call({
					method: "bcommerce.start_sync",
					args: {},
					callback: function(res){
						
						cur_frm.refresh()
					}
				});
		}).addClass("btn-primary");

	
	},
	before_save: function(doc){
		if(!doc.authentication_type){
			frappe.msgprint(__("Please select authentication type"));
			return false;
		}
	},
	authentication_type: function(doc){
		var me = this;
		var basic_auth = ["token", "app_name"];
		var oauth  = ["client_id", "store_hash", "access_token"];
		var flag = doc.authentication_type;
		if(!flag || flag == ""){
			frappe.msgprint(__("Please select authentication type"));
			return false;
		}
		if(flag == "Basic Authentication"){
			me.show_hide_fields(doc, basic_auth, oauth);
		}
		else{
			me.show_hide_fields(doc, oauth, basic_auth);
		}	
	},
	show_hide_fields: function(doc, show_fields, hide_fields){
		var me = this;	
		for(var i=0; i<show_fields.length; i++){
			var show = me.frm.get_field(show_fields[i]);
			show.df.hidden = 0;
			show.df.reqd = 1;
		}
		for(var i=0; i<hide_fields.length; i++){
			var hide = me.frm.get_field(hide_fields[i]);
			hide.df.hidden = 1;
			hide.df.reqd = 0;
		}
		me.frm.refresh_fields(show_fields);
		me.frm.refresh_fields(hide_fields);
	}

});

$.extend(bcommerce.bcommerce_setting, {

	setup_queries: function(frm){

		frm.fields_dict['warehouse'].get_query = function(doc){
			return {
				filters:{
					"company":doc.company,
					"is_group":"No"
				}
			}
		}


		frm.fields_dict["bcommerce_taxes"].grid.get_field("bcommerce_tax_account").get_query = function(doc, cdt, cdn){
		
			return {
				filters: {
					"account_type": ["Tax", "Chargeable", "Expense Account"],
					"company": doc.company
				},
				query :"erpnext.controllers.queries.tax_account_query",
			}
		}
	
		frm.fields_dict["cost_center"].get_query = function(doc){
			return{
				filters: {
					"company": doc.company,
					"is_group": "No"
				}
			}
		}
	}
});
