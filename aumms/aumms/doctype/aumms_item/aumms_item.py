# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.model.document import Document
from frappe.utils import getdate
from aumms.aumms.doc_events.item import create_qr
from frappe.utils import strip

# Fields used to map AuMMS Item to Item
aumms_item_fields = [
    "item_code",
    "item_name",
    "item_type",
    "stock_uom",
    "disabled",
    "is_stock_item",
    "making_charge_based_on",
    "making_charge_percentage",
    "making_charge",
    "purity",
    "purity_percentage",
    "is_purity_item",
    "description",
    "weight_per_unit",
    "weight_uom",
    "is_purchase_item",
    "purchase_uom",
    "is_sales_item",
    "sales_uom",
    "gold_weight",
    "has_stone",
    "stone_weight",
    "stone_charge",
]


class AuMMSItem(Document):
    def validate(self):
        self.validate_gold_weight()
        """ Method to validate Item name and Item Code """
        """
		self.validate_stone_weight()
		self.validate_stone_charge()"""

        if self.is_new():
            self.validate_item_name()
            self.validate_item_code()
        self.validate_gross_wt_stone_wt_and_charge()

    """def validate_stone_weight(self):
		if not self.stone_weight and self.is_stone_item:
			frappe.throw(_('Please Enter Stone weight'))

	def validate_stone_charge(self):
		if not self.stone_charge and self.is_stone_item:
			frappe.throw(_('Please Enter Stone Charge'))"""

    def autoname(self):
        if frappe.db.get_default("item_naming_by") == "Naming Series":
            from frappe.model.naming import set_name_by_naming_series

            set_name_by_naming_series(self)
            self.item_code = self.name

        self.item_code = strip(self.item_code)
        self.name = self.item_code

    def before_save(self):
        create_qr(self)

    def validate_gold_weight(self):
        if not self.gold_weight and not self.is_stone_item:
            frappe.throw("Gold Weight is mandatory")

    def after_insert(self):
        """Method to create Item from AuMMS Item"""
        self.create_or_update_item()

    def on_update(self):
        """Method to update created Item on changes of AuMMS Item"""
        self.create_or_update_item(self.item)

    def validate_item_name(self):
        """Method to validate AuMMS Item Name wrt to Item Name"""
        if self.item_name:
            if frappe.db.exists("Item", {"item_name": self.item_name}):
                frappe.throw(
                    "Item already exists with Item Name `{0}`.".format(
                        frappe.bold(self.item_name)
                    )
                )

    def validate_gross_wt_stone_wt_and_charge(self):
        """Method to validate AuMMS Item calculate missing wrt to Item Name"""
        if self.has_stone and (not self.stone_weight or self.stone_charge):
            stone_charge = 0
            stone_weight = 0
            for item in self.stone_details:
                stone_charge = +stone_charge + item.stone_charge
                stone_weight = +stone_weight + item.stone_weight
            self.stone_weight = stone_weight
            self.stone_charge = stone_charge

        if not self.weight_per_unit:
            if self.has_stone and self.gold_weight and self.stone_weight:
                self.weight_per_unit = self.gold_weight + self.stone_weight
            elif not self.has_stone and self.gold_weight:
                self.weight_per_unit = self.gold_weight

    def validate_item_code(self):
        """Method to validate AuMMS Item Code wrt to Item Code"""
        if self.item_code:
            if frappe.db.exists("Item", {"item_code": self.item_code}):
                frappe.throw(
                    "Item already exists with Item Code `{0}`.".format(
                        frappe.bold(self.item_code)
                    )
                )

    def create_or_update_item(self, item=None):
        """Method to create or update Item from AuMMS Item"""
        item_group = frappe.db.get_value(
            "AuMMS Item Group", self.item_group, "item_group"
        )
        if not item:
            # Case of new Item
            if not frappe.db.exists("Item", self.name):
                # Creating new Item object
                item_doc = frappe.new_doc("Item")
            else:
                # Case of exception
                return 0
        else:
            # Case of existing Item
            if frappe.db.exists("Item", item):
                # Creating existing Item object
                item_doc = frappe.get_doc("Item", item)
            else:
                # Case of exception
                return 0

        # Check Item Group existance and set Item Group
        if item_group:
            item_doc.set("item_group", item_group)

        # Set values to Item from AuMMS Item
        for aumms_item_field in aumms_item_fields:
            item_doc.set(aumms_item_field, self.get(aumms_item_field))

        item_doc.is_aumms_item = 1
        item_doc.custom_is_raw_material = self.is_raw_material

        # Clear and Set UOMs to Item
        item_doc.uoms = []
        for uom in self.uoms:
            row = item_doc.append("uoms")
            row.uom = uom.uom
            row.conversion_factor = uom.conversion_factor

        if not item:
            # Case of new Item
            item_doc.insert(ignore_permissions=True)
            # Set Item Group link to AuMMS Item Group
            frappe.db.set_value("AuMMS Item", self.name, "item", item_doc.name)
        elif frappe.db.exists("Item", item):
            # case of updating existing Item
            item_doc.save(ignore_permissions=True)
        frappe.db.commit()


@frappe.whitelist()
def create_opening_stock_from_list(item_list_json):
    item_list = json.loads(item_list_json)
    frappe.enqueue(
        create_opening_stock,
        queue="default",
        timeout=6000,
        job_name="Opening Stock Creation",
        at_front=True,
        item_list=item_list,
    )
    return "Opening stock creation has been enqueued."



@frappe.whitelist()
def create_opening_stock(item_list, board_rate=None):
    """
    Function to create Opening Stock 
    """

    warehouse = frappe.db.exists("Warehouse", {"name": ["like", "%Stores%"]})
    account = frappe.db.exists("Account", {"name": ["like", "%Temporary Opening%"]})

    if not warehouse or not account:
        frappe.throw("Required Warehouse or Account not found.")

    current_date = getdate()
    
    aumms_item = frappe.get_doc("AuMMS Item", item_list)

    # Fetch the actual board rate value using the `board_rate` field from the selected Board Rate document
    if board_rate:
        board_rate_value = frappe.db.get_value("Board Rate", board_rate, "board_rate")
        board_rate = float(board_rate_value) if board_rate_value else 0
    else:
        board_rate = 0

    try:
        doc = frappe.new_doc("Stock Reconciliation")
        doc.purpose = "Opening Stock"
        doc.expense_account = account
        doc.date = current_date

        doc.append(
            "items",
            {
                "item_code": aumms_item.item_code,
                "warehouse": warehouse,
                "qty": 1,
                "valuation_rate": board_rate * aumms_item.gold_weight,
            },
        )
        
        
        doc.insert(ignore_permissions=True)
        return doc.name  

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Opening Stock Creation Error")
        frappe.throw("An error occurred while creating the Opening Stock: {0}").format(str(e))
