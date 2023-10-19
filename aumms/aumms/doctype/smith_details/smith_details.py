# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document
from frappe.utils import escape_html, random_string

class SmithDetails(Document):
    def before_insert(self):
        # Check if the 'email' field is set and not empty
        if self.email:
            email = self.email
        else:
            frappe.throw("Email field is required")

        # Extract other data from the Smith Details document
        first_name = self.first_name
        last_name = self.last_name

        # Create a new User document
        user = frappe.get_doc({
            "doctype": "User",
            "email": email.strip().lower(),  # Ensure email is lowercased and stripped
            "first_name": escape_html(first_name),
            "last_name": escape_html(last_name),
            "enabled": 1,
            "new_password": random_string(10),
            "send_welcome_email": 0
        })
		# Append the 'Smith' role to the User
        user.append('roles', {
            'role': 'Smith'
        })

        # Set flags to ignore permissions and password policy
        user.flags.ignore_permissions = True
        user.flags.ignore_password_policy = True

        # Insert the User document
        user.insert()



