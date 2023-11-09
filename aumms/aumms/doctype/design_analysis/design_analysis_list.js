frappe.listview_settings['Design Analysis'] = {
    add_fields: ["id", "status", "mobile_no", "delivery_date"],
    has_indicator_for_draft:1,
    get_indicator: function(doc) {
        const status_colors = {
            "Request For Verification": "grey",
            "Request For Approval": "orange",
            "Approved": "green",
            "Rejected": "red",
            "Hold": "yellow",
            "BOM Created": "green",
            "Workorder Created": "green"
        };
        return [__(doc.status), status_colors[doc.status], "status,=,"+doc.status];
    },
};