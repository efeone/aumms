// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on("Customer Jewellery Order", {
	on_submit(frm) {
		if (!frm.is_new()){
			// frm.add_custom_button('Jewellery Order', () => {
				frappe.call('aumms.aumms.doctype.customer_jewellery_order.customer_jewellery_order.create_jewellery_order', {
					customer_jewellery_order : frm.doc.name
				}).then(r =>{
						frm.reload_doc();
				});
			// },'Create');
		}
	},
	if (purity) {
		frappe.call({
			method: 'aumms.aumms.utils.get_board_rate',
			args: {
					'purity': d.purity,
			},
			callback: function(r) {
				if (r.message) {
					let board_rate = r.message
					frappe.model.set_value(cdt, cdn, 'board_rate', board_rate);
					frm.refresh_field('old_jewellery_items');
				}
			}
		})
	}
});

frappe.ui.form.on("Customer Jewellery Order Details",{
  expected_weight_per_quantity: function(frm, cdt, cdn){
   let d = locals[cdt][cdn];
   var total_weightage = 0
   frm.doc.order_item.forEach(function(d){
     total_weightage += d.expected_weight_per_quantity * d.item_quantity;
   })
   frm.set_value('total_expected_weight_per_quantity',total_weightage)
 },
 order_item_remove:function(frm){
     var total_weightage = 0
     frm.doc.order_item.forEach(function(d){
       total_weightage += d.expected_weight_per_quantity;
     })
     frm.set_value("total_expected_weight_per_quantity",total_weightage)
   }
})
