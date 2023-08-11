# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import money_in_words
from frappe.model.naming import make_autoname
from frappe.model.mapper import get_mapped_doc
from frappe.model.document import Document
from frappe.utils import *
from erpnext.stock.doctype.item.item import get_item_defaults
from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
from frappe.contacts.doctype.address.address import get_company_address
from erpnext.e_commerce.shopping_cart.cart import get_billing_addresses
from erpnext.accounts.party import get_party_account

class JewelleryInvoice(Document):
	def validate(self):
		self.set_total_amount()

	def on_submit(self):
		''' Method to Create Sales Order & Purchase Order and link them with Jewellery Invoice '''
		sales_order = create_sales_order(self.name)
		if sales_order:
			frappe.db.set_value(self.doctype, self.name, 'sales_order', sales_order)
			frappe.db.set_value(self.doctype, self.name, 'status', 'Ordered')
			frappe.db.commit()
			self.reload()
		else:
			frappe.throw("Something went wrong while creating Sales Order, Please try again!")
		
		if self.aumms_exchange and self.customer:
			supplier = create_common_party_and_supplier(self.customer)
			purchase_order = create_purchase_order(self.name, supplier)
			if purchase_order:
				frappe.db.set_value(self.doctype, self.name, 'purchase_order', purchase_order)
				frappe.db.commit()
				self.reload()
			else:
				frappe.throw("Something went wrong while creating Puchase Order, Please try again!")
		

	def on_cancel(self):
		''' On Cancel event of Jewellery Invoice '''
		self.cancel_delivery_note()
		self.cancel_sales_invoice()
		self.cancel_sales_order()
		self.cancel_purchase_invoice()
		self.cancel_purchase_order()


	def set_total_amount(self):
		''' Method to calculate and set totals '''
		amount = 0
		for item in self.items:
			amount += item.amount
		currency = self.currency
		self.grand_total = amount
		if self.disable_rounded_total:
			self.rounded_total = amount
			self.rounding_adjustment = 0
		else:
			self.rounded_total = round(amount)
			self.rounding_adjustment = self.rounded_total - amount
		self.in_words = money_in_words(self.rounded_total, currency)
		self.outstanding_amount = self.rounded_total - self.paid_amount

	def cancel_sales_order(self):
		''' Method to Cancel Sales Order linked with Jewellery Invoice '''
		if self.sales_order:
			if frappe.db.exists('Sales Order', self.sales_order):
				sales_order_doc = frappe.get_doc('Sales Order', self.sales_order)
				if sales_order_doc.docstatus == 1:
					sales_order_doc.cancel()
			else:
				frappe.throw('Sales Order `{0}` not found!'.format(self.sales_order))

	def cancel_purchase_order(self):
		''' Method to Cancel Purchase Order linked with Jewellery Invoice '''
		if self.purchase_order:
			if frappe.db.exists('Purchase Order', self.purchase_order):
				purchase_order_doc = frappe.get_doc('Purchase Order', self.purchase_order)
				if purchase_order_doc.docstatus == 1:
					purchase_order_doc.cancel()
			else:
				frappe.throw('Purchase Order `{0}` not found!'.format(self.purchase_order))

	def cancel_sales_invoice(self):
		''' Method to Cancel Sales Invoice linked with Jewellery Invoice '''
		if self.sales_invoice:
			if frappe.db.exists('Sales Invoice', self.sales_invoice):
				sales_invoice_doc = frappe.get_doc('Sales Invoice', self.sales_invoice)
				if sales_invoice_doc.docstatus == 1:
					sales_invoice_doc.cancel()
			else:
				frappe.throw('Sales Invoice `{0}` not found!'.format(self.sales_invoice))

	def cancel_purchase_invoice(self):
		''' Method to Cancel Purchase Invoice linked with Jewellery Invoice '''
		if self.purchase_invoice:
			if frappe.db.exists('Purchase Invoice', self.purchase_invoice):
				purchase_invoice_doc = frappe.get_doc('Purchase Invoice', self.purchase_invoice)
				if purchase_invoice_doc.docstatus == 1:
					purchase_invoice_doc.cancel()
			else:
				frappe.throw('Purchase Invoice `{0}` not found!'.format(self.purchase_invoice))			

	def cancel_delivery_note(self):
		''' Method to Cancel Delivery Note linked with Jewellery Invoice '''
		if self.delivery_note:
			if frappe.db.exists('Delivery Note', self.delivery_note):
				delivery_note_doc = frappe.get_doc('Delivery Note', self.delivery_note)
				if delivery_note_doc.docstatus == 1:
					delivery_note_doc.cancel()
			else:
				frappe.throw('Delivery Note `{0}` not found!'.format(self.delivery_note))

def create_sales_order(source_name, target_doc=None):
	''' Method to create Sales Order from Jewellery Invoice '''
	def set_missing_values(source, target):
		pass
	target_doc = get_mapped_doc("Jewellery Invoice", source_name,
		{
			"Jewellery Invoice": {
				"doctype": "Sales Order",
				"field_map":{
				},
			},
			"Jewellery Invoice Item": {
				"doctype": "Sales Order Item",
				"field_map": {
					'delivery_date':'delivery_date',
				},
			},
    	}, target_doc, set_missing_values)
	target_doc.submit()
	frappe.msgprint(('Sales Order created'), indicator="green", alert=1)
	frappe.db.commit()
	return target_doc.name

def get_party_link_if_exist(party_type, party):
	query = """
		SELECT
			CASE
				WHEN primary_role = %(party_type)s THEN secondary_party
				WHEN secondary_role = %(party_type)s THEN primary_party
			END AS party
		FROM
			`tabParty Link`
		WHERE
			(primary_role = %(party_type)s AND primary_party = %(party)s ) OR (secondary_role = %(party_type)s AND secondary_party = %(party)s )
	"""
	party_link = frappe.db.sql(query, { 'party_type':party_type, 'party':party }, as_dict = 1)

	if not party_link:
		# Return None if party link is not set
		return None
	else:
		return party_link[0].party


def create_common_party_and_supplier(customer):
	common_party = get_party_link_if_exist('Customer', customer)
	if not common_party:
		#create supplier for common party 
		supplier_doc = frappe.new_doc('Supplier')
		customer_name =  frappe.db.get_value('Customer', customer, 'customer_name')
		supplier_doc.supplier_name = customer_name
		supplier_group = frappe.db.get_single_value('Buying Settings','supplier_group')
		supplier_doc.supplier_group = supplier_group
		supplier_doc.insert()
		#link common party
		if supplier_doc.name:
			link_doc = frappe.new_doc('Party Link')
			link_doc.primary_role = 'Customer'
			link_doc.primary_party = customer
			link_doc.secondary_role = 'Supplier'	
			link_doc.secondary_party = supplier_doc.name
			link_doc.insert()
		frappe.msgprint(('Common Party and Supplier Created and Link'), indicator="green", alert=1)
		common_party = supplier_doc.name
	return common_party


def create_purchase_order(source_name, supplier, target_doc=None):
	''' Method to create Purchase Order from Jewellery Invoice '''
	def set_missing_values(source, target):
		target.supplier = supplier
	target_doc = get_mapped_doc("Jewellery Invoice", source_name,
		{
			"Jewellery Invoice": {
				"doctype": "Purchase Order",
				"field_map":{
					'delivery_date':'schedule_date'
				},  
			},
			"Old Jewellery Item": {
				"doctype": "Purchase Order Item",
				"field_map": {
					'date':'schedule_date',
					'old_item':'item_code',
				},
			},
    	}, target_doc, set_missing_values)
	target_doc.submit()
	frappe.msgprint(('Purchase Order created'), indicator="green", alert=1)
	frappe.db.commit()
	return target_doc.name

@frappe.whitelist()
def create_payment_entry(mode_of_payment, amount, docname, posting_date=None, reference_no=None, reference_date=None):
	''' Method to create Payment Entry against linked Sales Order or Sales Invoice '''
	company = frappe.get_doc('Company',frappe.defaults.get_user_default("Company"))
	reference_doctype, reference_name, outstanding_amount, total, paid_amount = 0, 0, 0, 0, 0
	if not frappe.db.exists("Jewellery Invoice", docname):
		frappe.throw("Jewellery Invoice `{0}` not found!".format(docname))
	if not frappe.db.exists("Mode of Payment", mode_of_payment):
		frappe.throw("Mode of Payment `{0}` not found!".format(mode_of_payment))
	mode_of_payment_doc = frappe.get_doc("Mode of Payment", mode_of_payment)
	doc = frappe.get_doc("Jewellery Invoice", docname)
	total_amount_paid = float(doc.paid_amount) + float(amount)
	if doc.sales_invoice:
		reference_doctype = 'Sales Invoice'
		reference_name = doc.sales_invoice
	elif doc.sales_order:
		reference_doctype = 'Sales Order'
		reference_name = doc.sales_order
	if reference_doctype and reference_name:
		if frappe.db.get_value(reference_doctype, reference_name, 'disable_rounded_total'):
			total = frappe.db.get_value(reference_doctype, reference_name, 'grand_total')
		else:
			total = frappe.db.get_value(reference_doctype, reference_name, 'rounded_total')
		if reference_doctype == 'Sales Order':
			paid_amount = frappe.db.get_value(reference_doctype, reference_name, 'advance_paid')
			outstanding_amount = total - paid_amount
		if reference_doctype == 'Sales Invoice':
			outstanding_amount = frappe.db.get_value(reference_doctype, reference_name, 'outstanding_amount')
			paid_amount = total - outstanding_amount
		payment_entry_doc = frappe.new_doc('Payment Entry')
		advance_paid = frappe.db.get_value('Sales Order',docname,'advance_paid')
		payment_entry_doc.payment_type = 'Receive'
		payment_entry_doc.mode_of_payment = mode_of_payment
		payment_entry_doc.party_type = 'Customer'
		payment_entry_doc.party = doc.customer
		payment_entry_doc.paid_from = company.default_receivable_account
		payment_entry_doc.source_exchange_rate = 1
		payment_entry_doc.paid_amount = float(amount)
		payment_entry_doc.received_amount = float(amount)
		payment_entry_doc.paid_to = mode_of_payment_doc.accounts[0].default_account if mode_of_payment_doc.accounts else ''
		payment_entry_doc.reference_no = reference_no
		payment_entry_doc.reference_date = reference_date
		if posting_date:
			payment_entry_doc.posting_date = posting_date
		payment_entry_doc.append('references', {
			'reference_doctype' : reference_doctype,
			'reference_name': reference_name,
			'total_amount': float(total),
			'outstanding_amount': float(outstanding_amount),
			'allocated_amount': float(amount)
		})
		payment_entry_doc.submit()
		frappe.db.set_value("Jewellery Invoice", docname, 'paid_amount', float(total_amount_paid))
		frappe.db.set_value("Jewellery Invoice", docname, 'outstanding_amount', float(total) - float(total_amount_paid))
		if doc.status == 'Ordered':
			frappe.db.set_value("Jewellery Invoice", docname, 'status', 'Advance Received')
		doc.reload()
		frappe.db.commit()
		frappe.msgprint(('Payment Entry created'), indicator="green", alert=1)

@frappe.whitelist()
def create_sales_invoice(source_name, jewellery_invoice, update_stock=0, target_doc=None):
	''' Method to create Sales Invoice from Jewellery Invoice with Sales Order reference '''
	def postprocess(source, target):
		set_missing_values(source, target)

	def set_missing_values(source, target):
		target.flags.ignore_permissions = True
		target.run_method("set_missing_values")
		target.run_method("set_po_nos")
		target.run_method("calculate_taxes_and_totals")

		if source.company_address:
			target.update({"company_address": source.company_address})
		else:
			# set company address
			target.update(get_company_address(target.company))

		if target.company_address:
			target.update(get_fetch_values("Sales Invoice", "company_address", target.company_address))

		target.debit_to = get_party_account("Customer", source.customer, source.company)
		target.allocate_advances_automatically = 1
		target.update_stock = update_stock

	def update_item(source, target, source_parent):
		target.amount = flt(source.amount) - flt(source.billed_amt)
		target.base_amount = target.amount * flt(source_parent.conversion_rate)
		target.qty = (
			target.amount / flt(source.rate)
			if (source.rate and source.billed_amt)
			else source.qty - source.returned_qty
		)

		if source_parent.project:
			target.cost_center = frappe.db.get_value("Project", source_parent.project, "cost_center")
		if target.item_code:
			item = get_item_defaults(target.item_code, source_parent.company)
			item_group = get_item_group_defaults(target.item_code, source_parent.company)
			cost_center = item.get("selling_cost_center") or item_group.get("selling_cost_center")

			if cost_center:
				target.cost_center = cost_center

	doclist = get_mapped_doc(
		"Sales Order",
		source_name,
		{
			"Sales Order": {
				"doctype": "Sales Invoice",
				"field_map": {
					"party_account_currency": "party_account_currency",
					"payment_terms_template": "payment_terms_template",
				},
				"field_no_map": ["payment_terms_template"],
				"validation": {"docstatus": ["=", 1]},
			},
			"Sales Order Item": {
				"doctype": "Sales Invoice Item",
				"field_map": {
					"name": "so_detail",
					"parent": "sales_order",
				},
				"postprocess": update_item,
				"condition": lambda doc: doc.qty
				and (doc.base_amount == 0 or abs(doc.billed_amt) < abs(doc.amount)),
			},
			"Sales Taxes and Charges": {"doctype": "Sales Taxes and Charges", "add_if_empty": True},
			"Sales Team": {"doctype": "Sales Team", "add_if_empty": True},
		},
		target_doc,
		postprocess,
	)

	automatically_fetch_payment_terms = cint(
		frappe.db.get_single_value("Accounts Settings", "automatically_fetch_payment_terms")
	)
	if automatically_fetch_payment_terms:
		doclist.set_payment_schedule()

	doclist.set_onload("ignore_price_list", True)
	doclist.submit()
	if doclist:
		frappe.db.set_value('Jewellery Invoice', jewellery_invoice, 'sales_invoice', doclist.name)
		if update_stock:
			frappe.db.set_value('Jewellery Invoice', jewellery_invoice, 'status', 'Delivered')
		else:
			frappe.db.set_value('Jewellery Invoice', jewellery_invoice, 'status', 'Invoiced')
		frappe.db.commit()
		frappe.msgprint(('Sales Invoice created'), indicator="green", alert=1)

@frappe.whitelist()
def create_purchase_invoice(source_name, jewellery_invoice, update_stock=0, target_doc=None):
    ''' Method to create Purchase Invoice from Jewellery Invoice with Purchase Order reference '''
    def postprocess(source, target):
        set_missing_values(source, target)

    def set_missing_values(source, target):
        target.flags.ignore_permissions = True
        target.run_method("set_missing_values")
        target.run_method("set_po_nos")
        target.run_method("calculate_taxes_and_totals")
        target.credit_to = get_party_account("Supplier", source.supplier, source.company)
        target.allocate_advances_automatically = 1
        target.update_stock = update_stock

    def update_item(source, target, source_parent):
        target.amount = flt(source.amount) - flt(source.billed_amt)
        target.base_amount = target.amount * flt(source_parent.conversion_rate)
        target.qty = (
            target.amount / flt(source.rate)
            if (source.rate and source.billed_amt)
            else source.qty - source.returned_qty
        )
        # Update cost center, item defaults, etc. for Purchase Invoice items

    doclist = get_mapped_doc(
        "Purchase Order",
        source_name,
        {
            "Purchase Order": {
                "doctype": "Purchase Invoice",
                "field_map": {
                    "party_account_currency": "party_account_currency",
                    "payment_terms_template": "payment_terms_template",
                },
                "field_no_map": ["payment_terms_template"],
                "validation": {"docstatus": ["=", 1]},
            },
            "Purchase Order Item": {
                "doctype": "Purchase Invoice Item",
                "field_map": {
                    "name": "po_detail",
                    "parent": "purchase_order",
                },
                "postprocess": update_item,
                "condition": lambda doc: doc.qty
                and (doc.base_amount == 0 or abs(doc.billed_amt) < abs(doc.amount)),
            },
            "Purchase Taxes and Charges": {"doctype": "Purchase Taxes and Charges", "add_if_empty": True},
            "Purchase Team": {"doctype": "Purchase Team", "add_if_empty": True},
        },
        target_doc,
        postprocess,
    )

    # Payment terms logic for Purchase Invoices

    doclist.set_onload("ignore_price_list", True)
    doclist.submit()
    if doclist:
        # Update associated Jewellery Invoice status
        frappe.db.set_value('Jewellery Invoice', jewellery_invoice, 'purchase_invoice', doclist.name)
        if update_stock:
            frappe.db.set_value('Jewellery Invoice', jewellery_invoice, 'status', 'Received')
        else:
            frappe.db.set_value('Jewellery Invoice', jewellery_invoice, 'status', 'Invoiced')
        frappe.db.commit()
        frappe.msgprint(('Purchase Invoice created'), indicator="green", alert=1)


@frappe.whitelist()
def get_board_rate(old_item, transaction_date):
    # Fetch the boardrate from the 'Board Rate' doctype
    board_rate = frappe.db.get_value('Board Rate', {'old_item': old_item, 'valid_from': ('<=', transaction_date)},
                                     'board_rate', order_by='valid_from desc', as_dict=True)
    
    return {'board_rate': board_rate}

@frappe.whitelist()
def create_delivery_note(source_name, jewellery_invoice, target_doc=None):
	''' Method to create Delivery Note from Jewellery Invoice with Sales Invoice reference '''
	def set_missing_values(source, target):
		target.run_method("set_missing_values")
		target.run_method("set_po_nos")
		target.run_method("calculate_taxes_and_totals")

	def update_item(source_doc, target_doc, source_parent):
		target_doc.qty = flt(source_doc.qty) - flt(source_doc.delivered_qty)
		target_doc.stock_qty = target_doc.qty * flt(source_doc.conversion_factor)

		target_doc.base_amount = target_doc.qty * flt(source_doc.base_rate)
		target_doc.amount = target_doc.qty * flt(source_doc.rate)

	doclist = get_mapped_doc(
		"Sales Invoice",
		source_name,
		{
			"Sales Invoice": {"doctype": "Delivery Note", "validation": {"docstatus": ["=", 1]}},
			"Sales Invoice Item": {
				"doctype": "Delivery Note Item",
				"field_map": {
					"name": "si_detail",
					"parent": "against_sales_invoice",
					"serial_no": "serial_no",
					"sales_order": "against_sales_order",
					"so_detail": "so_detail",
					"cost_center": "cost_center",
				},
				"postprocess": update_item,
				"condition": lambda doc: doc.delivered_by_supplier != 1,
			},
			"Sales Taxes and Charges": {"doctype": "Sales Taxes and Charges", "add_if_empty": True},
			"Sales Team": {
				"doctype": "Sales Team",
				"field_map": {"incentives": "incentives"},
				"add_if_empty": True,
			},
		},
		target_doc,
		set_missing_values,
	)

	doclist.set_onload("ignore_price_list", True)
	doclist.submit()
	if doclist:
		frappe.db.set_value('Jewellery Invoice', jewellery_invoice, 'delivery_note', doclist.name)
		frappe.db.set_value('Jewellery Invoice', jewellery_invoice, 'status', 'Delivered')
		frappe.db.commit()
		frappe.msgprint(('Delivery Note created'), indicator="green", alert=1)
