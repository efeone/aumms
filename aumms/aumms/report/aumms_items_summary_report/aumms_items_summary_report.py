# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    if not filters:
        filters = {}

    if "item_code" not in filters:
        filters["item_code"] = None

    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    columns = [

        {
            "label": _("Item Group"),
            "fieldname": "item_group",
            "fieldtype": "Link",
            "options": "AuMMS Item Group",
            "width": 180
        },
        {
            "label": _("Item Code"),
            "fieldname": "item_code",
            "fieldtype": "Data",
            "width": 250
        },
        {
            "label": _("Item Count"),
            "fieldname": "item_count",
            "fieldtype": "Int",
            "width": 120
        },
        {
            "label": _("Item Group Count"),
            "fieldname": "item_group_count",
            "fieldtype": "Int",
            "width": 150
        },
    ]
    return columns

def get_data(filters):
    # query = """
    #     SELECT
    #         ai.item_group,
    #         ai.item_code,
    #         item_counts.item_count
    #     FROM
    #         `tabAuMMS Item` ai
    #     JOIN
    #         (SELECT item_group, COUNT(*) AS item_count
    #          FROM `tabAuMMS Item`
    #          GROUP BY item_group) AS item_counts
    #     ON ai.item_group = item_counts.item_group
    #     WHERE 1=1
    # """
    query = """
        SELECT
            CASE WHEN ROW_NUMBER() OVER (PARTITION BY grouped_items.item_group ORDER BY ai.item_code) = 1
                 THEN grouped_items.item_group
                 ELSE ''
            END AS item_group,
            CASE WHEN ROW_NUMBER() OVER (PARTITION BY grouped_items.item_group ORDER BY ai.item_code) = 1
                 THEN grouped_items.item_group_count
                 ELSE NULL
            END AS item_group_count,
            ai.item_code,
            COUNT(*) AS item_count
        FROM
            (SELECT
                 item_group,
                 COUNT(*) AS item_group_count
             FROM
                 `tabAuMMS Item`
             GROUP BY
                 item_group) AS grouped_items
        JOIN
            `tabAuMMS Item` AS ai
        ON
            grouped_items.item_group = ai.item_group
    """

    combine_where = 0
    if filters.get("item_code"):
        query += " WHERE ai.item_code like '%{0}%'".format(filters.get("item_code"))
        combine_where = 1

    if filters.get("item_group"):
        if combine_where:
            query += " AND ai.item_group = '{0}'".format(filters.get("item_group"))
        else:
            query += " WHERE ai.item_group = '{0}'".format(filters.get("item_group"))

    query += " GROUP BY ai.item_code"
    # query += " ORDER BY ai.item_group, ai.item_code, item_counts.item_count;"

    # Execute the query and fetch data
    data = frappe.db.sql(query, as_dict=True)

    return data
