frappe.listview_settings['Design Request'] = {
    add_fields: ["id", "status", "mobile_no", "delivery_date"],
    has_indicator_for_draft:1,
    get_indicator: function(doc) {
        const status_colors = {
            "Request For Verification": "grey",
            "Request For Approval": "orange",
            "Approved": "purple",
            "Rejected": "red",
            "Hold": "red",
            "BOM Created": "green",
            "Workorder Created": "blue"
        };
        return [__(doc.status), status_colors[doc.status], "status,=,"+doc.status];
    },
};