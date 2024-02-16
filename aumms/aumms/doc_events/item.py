import os
import io
import json
import frappe
from frappe import _
from datetime import date
from pyqrcode import create
from base64 import b64encode
from pyqrcode import create as qr_create
from frappe.utils.data import get_url_to_form
from aumms.aumms.utils import get_conversion_factor
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

@frappe.whitelist()
def validate_item(doc, method):
    """
        method used to validate item doc
        args:
            doc: object of item document
            method: validate of item
    """
    # check stock uom is a purity uom
    if doc.stock_uom and doc.is_purity_item:
        uom_is_a_purity_uom(doc.stock_uom)
    # check sales uom is a purity uom
    if doc.sales_uom and doc.is_purity_item:
        uom_is_a_purity_uom(doc.sales_uom)
    # check purchase uom is a purity uom
    if doc.purchase_uom and doc.is_purity_item:
        uom_is_a_purity_uom(doc.purchase_uom)
     # validate purity field is Mandatory
    if doc.is_purity_item and not doc.purity:
        frappe.throw(_('Purity is Mandatory'))



def uom_is_a_purity_uom(uom):
    """
        function to check uom is a purity uom
        args:
            uom: name of uom document
        output: a message iff uom is not a purity uom
    """
    if not frappe.db.exists('UOM', {'name': uom, 'is_purity_uom': 1}):
        frappe.throw(_('{} is not a purity uom'.format(uom)))

@frappe.whitelist()
def get_purity_uom():
    """ method to get all uoms with is purity checked"""
    return frappe.db.get_all('UOM', {'is_purity_uom': 1})

@frappe.whitelist()
def check_conversion_factor_for_uom(doc, method):
    """
        method using for checking and warning the user that the coversion factor is 0
        args:
            doc: object of item document
            method: before save of item document
    """
    for uom in doc.uoms:
        if not uom.conversion_factor:
            # alert message to user
            frappe.msgprint(
                msg = _(
                    'The conversion factor between {} and {} is zero.'.format(uom.uom, doc.stock_uom)
                    ),
                title = 'Alert'
            )

@frappe.whitelist()
def making_charge_to_item(item_group, charge_based_on, type):
    '''set making_charge_percentage, is_purchase_item and is_sales_item from item group'''
    item_group_details = {'making_charge_percentage': 0, 'is_purchase_item':0, 'is_sales_item':0}
    if charge_based_on == 'Percentage':
        if frappe.db.exists('Item Group', {'name':item_group , 'item_type':type}):
            item_group_doc = frappe.get_last_doc('Item Group', filters = {'name':item_group , 'item_type':type})
            item_group_details['making_charge_percentage'] = item_group_doc.percentage
    if frappe.db.exists('Item Group', {'name':item_group , 'item_type':type}):
        item_group_doc = frappe.get_last_doc('Item Group', filters = {'name':item_group , 'item_type':type})
        item_group_details['is_purchase_item'] = item_group_doc.is_purchase_item
        item_group_details['is_sales_item'] = item_group_doc.is_sales_item
    return item_group_details

@frappe.whitelist()
def fetch_making_charge_from_item_group_to_item(item_group, charge_based_on, type):
    '''set making_charge_percentage and currency while the change of making_charge_based_on'''
    item_group_details = {'percentage': 0, 'currency':0}
    if charge_based_on == 'Percentage':
        if frappe.db.exists('Item Group', {'name':item_group , 'item_type':type}):
            item_group_doc = frappe.get_last_doc('Item Group', filters = {'name':item_group , 'item_type':type})
            item_group_details['percentage'] = item_group_doc.percentage
    if charge_based_on == 'Fixed':
        if frappe.db.exists('Item Group', {'name':item_group , 'item_type':type}):
            item_group_doc = frappe.get_last_doc('Item Group', filters = {'name':item_group , 'item_type':type})
            item_group_details['currency'] = item_group_doc.currency
    return item_group_details



@frappe.whitelist()
def update_uoms_table(doc, method=None):
    """
        method to update uoms table on update of item doc
        args:
            doc: item doc
    """
    # get list of existing uom
    existing_uoms = get_existing_uoms(doc.uoms)
    # get purity uoms to append
    purity_uoms = get_purity_uom()

    for uom in purity_uoms:

        # check uom is not in existing uoms
        if uom.name not in existing_uoms:

            # get conversion factor of appending uom to stock uom
            conversion_factor = get_conversion_factor(uom.name, doc.stock_uom)

            # if appending uom is equal to stock uom consider conversion factor as 1
            if uom.name == doc.stock_uom:
                 conversion_factor = 1

            # append uoms table
            doc.append('uoms', {
                'uom': uom.name,
                'conversion_factor': conversion_factor if conversion_factor else 0
            })

def get_existing_uoms(uoms):
    """
        function to get existing uoms list
        uoms: object of uoms in item
        output: list of existing uom's
    """
    uoms_list = []
    for uom in uoms:
        uoms_list.append(uom.uom)
    return uoms_list

def create_qr(doc, method=None):
    # Creating a fied for QR code if it doesn't exist
    if not hasattr(doc, "item_qr"):
        create_custom_fields(
            {
                doc.doctype: [
                    dict(
                        fieldname="item_qr",
                        label="Item QR",
                        fieldtype="Attach Image",
                        read_only=1,
                        no_copy=1,
                        # hidden=1,
                    )
                ]
            }
        )

    # Checking if a qr code is already generated
    qr_code = doc.get("item_qr")
    if qr_code and frappe.db.exists({"doctype": "File", "file_url": qr_code}):
        return


    doc_url = get_si_json(doc)

    # Generating QR image
    qr_image = io.BytesIO()
    url = create(doc_url, error="L")
    url.png(qr_image, scale = 2, quiet_zone=1)

    name = frappe.generate_hash(doc.name, 5)

    # Uploading the QR and attaching it to the document
    filename = f"QRCode-{name}.png".replace(os.path.sep, "__")
    _file = frappe.get_doc(
        {
            "doctype": "File",
            "file_name": filename,
            "is_private": 0,
            "content": qr_image.getvalue(),
            "attached_to_doctype": doc.get("doctype"),
            "attached_to_name": doc.get("name"),
            "attached_to_field": "item_qr",
        }
    )

    _file.save()

    # assigning to document
    doc.db_set("item_qr", _file.file_url)
    doc.notify_update()

def get_si_json(doc):
    # Define the list of essential fields
    essential_fields = [
        "item_code",
        "item_name",
        "item_group",
        "custom_company",
        "custom_item_class",
        "custom_parent_item_group",
    ]

    # Create a dictionary to store the field values
    item_data = {}

    # Extract the field values from the document object
    for field in essential_fields:
        value = doc.get(field)

        # Convert datetime.date objects to string representation
        if isinstance(value, date):
            value = value.strftime("%Y-%m-%d")

        item_data[field] = value

    # Convert the dictionary to JSON
    json_data = json.dumps(item_data, indent=4)

    return json_data
