// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Jewellery Invoice', {
	setup: function(frm) {
		set_filters(frm);
	},
	transaction_date: function(frm) {
		if (frm.doc.transaction_date ) {
			frm.doc.items.forEach((child) => {
				set_item_details(frm, child);
			});
		}
	},
	customer: function(frm) {
		//method for setting the customer type
		if (frm.doc.customer) {
			frappe.call({
				method : 'aumms.aumms.doc_events.sales_order.set_customer_type',
				args : {
					customer: frm.doc.customer
				},
				callback : function(r) {
					if (r.message) {
						if(frm.doc.items){
							frm.doc.items.forEach((child) => {
								child.customer_type = r.message
							});
						}
					}
				}
			})
		}
	},

	delivery_date: function(frm){
		if(frm.doc.delivery_date){
			set_missing_delivery_dates(frm);
		}
	},
	onload: function(frm){
		set_default_taxes_template(frm);
	},
	company: function(frm){
		set_default_taxes_template(frm);
	},
	refresh: function(frm){
		hide_stone_details_add_row(frm);
		if(frm.doc.docstatus===1){
			create_custom_buttons(frm);
		}
	},
	onload_post_render: function(frm){
		remove_previous_links(frm);
	},
	transaction_type: function(frm){
		set_net_weight_and_amount(frm);
	},
	sales_taxes_and_charges_template: function(frm) {
		if (frm.doc.sales_taxes_and_charges_template) {
				frappe.call({
						method: 'aumms.aumms.doctype.jewellery_invoice.jewellery_invoice.get_sales_taxes_and_charges_details',
						args: {
								//Tax is charged on the net total, so any discount comes off before the rate
								sales_taxes_and_charges_template: frm.doc.sales_taxes_and_charges_template,
								total_gold_amount : flt(frm.doc.total_gold_amount) - flt(frm.doc.discount_amount),
								jewellery_invoice: frm.doc.name
						},
						callback: function(response) {
								if (response.message) {
										frm.clear_table("custom_sales_taxes_and_charges");
										var total_taxes_and_charges = 0
										response.message.forEach(function(tax) {
												frm.add_child("custom_sales_taxes_and_charges", {
														charge_type: tax.charge_type,
														account_head: tax.account_head,
														description: tax.description,
														rate: tax.rate,
														tax_amount: tax.tax_amount,
														included_in_print_rate: tax.included_in_print_rate,
														total : tax.total
												});
												total_taxes_and_charges += tax.tax_amount
										});
										frm.set_value('custom_total_taxes_and_charges', total_taxes_and_charges)
										frm.refresh_field('custom_total_taxes_and_charges');
										frm.refresh_field("custom_sales_taxes_and_charges");
								}
						}
				});
		}
}
});

frappe.ui.form.on('Old Jewellery Item', {
	item_code: function(frm, cdt, cdn) {
		let d = locals[cdt][cdn];
		
		if (d.item_code && d.purity && d.stock_uom) {
		
			frappe.call({
				method: 'aumms.aumms.utils.get_board_rate',
				args: {
						'item_type': d.item_type,
						'date': frm.doc.transaction_date,
						'purity': d.purity,
						'stock_uom': d.stock_uom
				},
				callback: function(r) {
					if (r.message) {
						let board_rate = r.message
						frappe.model.set_value(cdt, cdn, 'board_rate', board_rate);
						frappe.model.set_value(cdt, cdn, 'rate', board_rate)
						frm.refresh_field('old_jewellery_items');
					}
				}
			});
		}
	},
	weight: function(frm, cdt, cdn){
		let d = locals[cdt][cdn];
		let total_old_gold_weight;
		if (d.weight){
			frappe.model.set_value(cdt, cdn, 'amount', d.weight * d.rate);
			frm.refresh_field('old_jewellery_items');
			if(frm.doc.total_old_gold_weight){
				total_old_gold_weight = frm.doc.total_old_gold_weight
			}
			total_old_gold_weight = total_old_gold_weight + d.weight;
			frm.set_value('total_old_gold_weight', total_old_gold_weight);
		}
	},
	rate: function(frm, cdt, cdn){
		let d = locals[cdt][cdn];
		if (d.rate){
			//set amount with rate * weight
			frappe.model.set_value(cdt, cdn, 'amount', d.weight * d.rate);
			frm.refresh_field('old_jewellery_items');
		}
	},
	amount: function(frm){
		set_net_weight_and_amount(frm);
	},
	old_jewellery_items_add: function(frm){
		set_net_weight_and_amount(frm);
	},
	old_jewellery_items_remove: function(frm){
		set_net_weight_and_amount(frm);
	}
});


frappe.ui.form.on('Jewellery Invoice Item', {

	gold_weight: function(frm, cdt, cdn){
		let d = locals[cdt][cdn];
		let total_gold_weight;
		if (d.gold_weight){
			//set amount_with_out_making_charge while changing gold_weight
			frappe.model.set_value(d.doctype, d.name, 'amount_with_out_making_charge', d.gold_weight * d.board_rate);
			frappe.model.set_value(d.doctype, d.name, 'net_amount_with_out_making_charge', d.amount_with_out_making_charge + d.stone_charge);
			//set amount with rate * gold_weight
			frappe.model.set_value(d.doctype, d.name, 'amount', d.gold_weight * d.rate);
			frm.refresh_field('items');
			if(frm.doc.total_gold_weight){
				total_gold_weight = frm.doc.total_gold_weight
			}
			total_gold_weight = total_gold_weight + d.gold_weight;
			frm.set_value('total_gold_weight', total_gold_weight);
		}
	},
	rate: function(frm, cdt, cdn){
		let d = locals[cdt][cdn];
		if (d.rate){
			//set amount with rate * gold_weight
			frappe.model.set_value(d.doctype, d.name, 'amount', d.gold_weight * d.rate);
			frm.refresh_field('items');
		}
	},
	amount: function(frm, cdt, cdn) {
		set_net_weight_and_amount(frm);
		// set_totals(frm);
	},
	making_charge_percentage: function(frm, cdt, cdn){
		let d = locals[cdt][cdn];
		set_making_charge(d);
		frm.refresh_field('items')
	},
	amount_with_out_making_charge: function(frm, cdt, cdn){
		let d = locals[cdt][cdn];
		if (d.amount_with_out_making_charge){
			frappe.model.set_value(d.doctype, d.name, 'net_amount_with_out_making_charge', d.amount_with_out_making_charge + d.stone_charge);
			set_making_charge(d);
			let rate = (d.net_amount_with_out_making_charge + d.making_charge)/d.gold_weight
			if (rate)
			{
				//set rate by the change of amount_with_out_making_charge
				frappe.model.set_value(d.doctype, d.name, 'rate', rate);
			}
		}
		frm.refresh_field('items');
	},
	net_amount_with_out_making_charge: function(frm, cdt, cdn){
		let d = locals[cdt][cdn];
		if(d.net_amount_with_out_making_charge){
			let rate = (d.net_amount_with_out_making_charge + d.making_charge)/d.gold_weight
			if (rate)
			{
				//set rate by the change of amount_with_out_making_charge
				frappe.model.set_value(d.doctype, d.name, 'rate', rate);
			}
		}
		frm.refresh_field('items');
	},
	making_charge:function(frm, cdt, cdn) {
		let d = locals[cdt][cdn];
		if(d.making_charge) {
			let rate = (d.net_amount_with_out_making_charge + d.making_charge)/d.gold_weight
			if (rate)
			{
				//set rate by the change of making_charge
				frappe.model.set_value(d.doctype, d.name, 'rate', rate);
				frm.refresh_field('items');
			}
		}
	},
	stone_charge:function(frm, cdt,cdn){
		let d = locals[cdt][cdn];
		if(d.stone_charge){
			frappe.model.set_value(d.doctype, d.name, 'net_amount_with_out_making_charge', d.amount_with_out_making_charge + d.stone_charge);
			frm.refresh_field('items');
		}
	},
	conversion_factor:function(frm, cdt,cdn){
		let d = locals[cdt][cdn];
		if(d.conversion_factor){
			var rate = d.board_rate * d.conversion_factor;
			//set rate by the change of conversion_factor
			frappe.model.set_value(d.doctype, d.name, 'rate', rate);
			frm.refresh_field('items');
		}
	},
	items_add: function(frm, cdt, cdn) {
		let child = locals[cdt][cdn]
		if(frm.doc.customer) {
			set_board_rate_read_only(frm, cdt, cdn);
		}
		if(frm.doc.delivery_date){
			frappe.model.set_value(child.doctype, child.name, 'delivery_date', frm.doc.delivery_date);
		}
		frm.refresh_field('items');
		// set_totals(frm);
		set_net_weight_and_amount(frm);
	},
	items_remove: function(frm, cdt, cdn) {
		// set_totals(frm);
		set_net_weight_and_amount(frm);
	}
});

let set_item_details = function(frm, child) {
	//function to get item get_item_details
	if(child.item_type){
		frappe.call({
				method : 'aumms.aumms.utils.get_board_rate',
				args: {
					item_type: child.item_type,
					date: frm.doc.transaction_date,
					stock_uom: child.stock_uom,
					purity: child.purity
				},
				callback : function(r) {
					if (r.message) {
						frappe.model.set_value(child.doctype, child.name, 'board_rate', r.message)
						frappe.model.set_value(child.doctype, child.name, 'amount_with_out_making_charge', (child.gold_weight * r.message))
						frappe.model.set_value(child.doctype, child.name, 'net_amount_with_out_making_charge', (child.amount_with_out_making_charge + child.stone_charge))
						frappe.model.set_value(child.doctype, child.name, 'rate', (child.net_amount_with_out_making_charge + child.making_charge)/child.gold_weight)
						frm.refresh_field('items');
					}
				}
		})
	}
}

let set_board_rate_read_only = function (frm, cdt, cdn) {
	//method for setting the customer type
	let child = locals[cdt][cdn]
		frappe.call({
				method : 'aumms.aumms.doc_events.sales_order.set_customer_type',
				args : {
					customer: frm.doc.customer
				},
				callback : function(r) {
					if (r.message) {
						child.customer_type = r.message
						frm.refresh_field('items');
					}
				}
		})
}

let set_filters = function(frm){
	frm.set_query('item_code', 'items', () => {
		return {
			filters: {
				disabled: 0,
				is_stone_item: 0,
				is_sales_item: 1
			}
		}
	});
	frm.set_query('stock_uom', 'items', () => {
		return {
			filters: {
				is_purity_uom: 1,
				enabled: 1
			}
		}
	});
	frm.set_query('item_code', 'old_jewellery_items', () => {
		return {
			filters: {
				disabled: 0,
				item_group: 'AuMMS Old Gold',
				is_purchase_item: 1
			}
		}
	});
}


let hide_stone_details_add_row = function(frm){
	//Stone rows come from the item, they are never keyed in by hand
	let grid = frm.get_field('stone_details').grid;
	grid.cannot_add_rows = true;
	grid.refresh();
}

let set_default_taxes_template = function(frm){
	//Only fill in a template that has not been chosen yet, never replace one
	if(!frm.is_new() || frm.doc.sales_taxes_and_charges_template || !frm.doc.company){
		return;
	}
	frappe.db.get_value('Sales Taxes and Charges Template', {
		company: frm.doc.company,
		is_default: 1,
		disabled: 0
	}, 'name').then(r => {
		if(r.message && r.message.name){
			frm.set_value('sales_taxes_and_charges_template', r.message.name);
		}
	});
}

let set_net_weight_and_amount = function(frm) {
	let total_old_gold_weight = 0;
	let total_gold_weight = 0;
	let total_old_gold_amount = 0;
	let total_gold_amount = 0; 
	let balance_amount = 0;

	if (frm.doc.items) {
		frm.doc.items.forEach((child) => {
			if (child.gold_weight) {
				total_gold_weight += child.gold_weight;
			}
			if (typeof child.amount === 'number' && !isNaN(child.amount)) { // Check if amount is a valid number
				total_gold_amount += child.amount; // Calculate total_gold_amount
			}
		});
	}

	if (frm.doc.transaction_type !== 'Sales' && frm.doc.old_jewellery_items) {
		frm.doc.old_jewellery_items.forEach((child) => {
			if (child.weight) {
				total_old_gold_weight += child.weight;
			}
			if (typeof child.amount === 'number' && !isNaN(child.amount)) { // Check if amount is a valid number
				total_old_gold_amount += child.amount;
			}
		});
	}

	balance_amount = total_gold_amount - total_old_gold_amount;

	// Set values in the form
	frm.set_value('total_gold_weight', total_gold_weight);
	frm.set_value('total_gold_amount', total_gold_amount);
	frm.set_value('total_old_gold_weight', total_old_gold_weight);
	frm.set_value('total_old_gold_amount', total_old_gold_amount);
	frm.set_value('balance_amount', balance_amount);
	
	frm.refresh_fields();
}


let set_missing_delivery_dates = function(frm){
	if(frm.doc.items){
		frm.doc.items.forEach((child) => {
			if(!child.delivery_date){
				child.delivery_date = frm.doc.delivery_date;
			}
		});
	}
	frm.refresh_fields('items');
}

let create_custom_buttons = function(frm){
	let outstanding_amount = flt(frm.doc.outstanding_amount);
	if(Math.abs(outstanding_amount) > 0.005){
		//A positive outstanding is received from the customer, a negative one is paid back
		let label = outstanding_amount > 0 ? __('Receive Payment') : __('Pay Customer');
		frm.add_custom_button(label, () => {
			make_payment(frm);
		}, 'Create');
	}
	if (frm.doc.sales_order && !frm.doc.sales_invoice) {
		frm.add_custom_button('Invoice', () => {
				// Create Sales Invoice
				frappe.call('aumms.aumms.doctype.jewellery_invoice.jewellery_invoice.create_sales_invoice', {
						source_name: frm.doc.sales_order,
						jewellery_invoice: frm.doc.name,
						sales_taxes_and_charges_template : frm.doc.sales_taxes_and_charges_template,
						keep_metal_ledger : 1
				}).then(r => {
						frm.reload_doc();
				});
		}, 'Create');
	}

	if(frm.doc.sales_invoice && !frm.doc.delivery_note && !frm.doc.delivered){
		frm.add_custom_button('Delivery Note', () => {
			//Delivery Note creation method
			frappe.call('aumms.aumms.doctype.jewellery_invoice.jewellery_invoice.create_delivery_note', {
				source_name: frm.doc.sales_invoice,
				jewellery_invoice: frm.doc.name
			}).then(r => {
				frm.reload_doc();
			});;
		}, 'Create');
	}
	if(frm.doc.sales_order && !frm.doc.sales_invoice && !frm.doc.delivery_note){
		frm.add_custom_button('Invoice and Delivery', () => {
			//Invoice and Deliver
			frappe.call('aumms.aumms.doctype.jewellery_invoice.jewellery_invoice.create_sales_invoice', {
				source_name: frm.doc.sales_order,
				jewellery_invoice: frm.doc.name,
				sales_taxes_and_charges_template : frm.doc.sales_taxes_and_charges_template,
				update_stock: 1,
				keep_metal_ledger :1
			}).then(r => {
				frm.reload_doc();
			});;
		}, 'Create');
	}

	if(frm.doc.sales_order && !frm.doc.sales_invoice){
		frm.add_custom_button('Get Customer Advances', () => {
			//To get customer advances
			get_customer_advances(frm);
		});
	}
}

let make_payment = function(frm){
	let outstanding_amount = flt(frm.doc.outstanding_amount);
	let due = Math.abs(outstanding_amount);
	let direction = outstanding_amount > 0
		? __('Receivable from customer: {0}', [format_currency(due, frm.doc.currency)])
		: __('Refund due to customer: {0}', [format_currency(due, frm.doc.currency)]);
	let d = new frappe.ui.Dialog({
		title: outstanding_amount > 0 ? __('Receive Payment') : __('Pay Customer'),
		fields: [
			{
				fieldname: 'direction',
				fieldtype: 'HTML',
				options: `<p class="text-muted">${direction}</p>`
			},
			{
					label: 'Mode of Payment',
					fieldname: 'mode_of_payment',
					fieldtype: 'Link',
					options: 'Mode of Payment',
					reqd: 1
			},
			{
					label:"Cheque/Reference No",
					fieldname: 'reference_no',
					fieldtype: 'Data',
					mandatory_depends_on: 'eval:doc.mode_of_payment!==\'Cash\'',
					depends_on: 'eval:doc.mode_of_payment!==\'Cash\''
			},
			{
					label:"Cheque/Reference Date",
					fieldname: 'reference_date',
					fieldtype: 'Date',
					mandatory_depends_on: 'eval:doc.mode_of_payment!==\'Cash\'',
					depends_on: 'eval:doc.mode_of_payment!==\'Cash\''
			},
			{
				label: 'Posting Date',
				fieldname: 'posting_date',
				fieldtype: 'Date'
			},
			{
				label: 'Payment Amount',
				fieldname: 'amount',
				fieldtype: 'Currency',
				default: due,
				reqd: 1,
				onchange: function(){
					d.set_value('balance', due - flt(d.get_value('amount')));
				}
			},
			{
				label: 'Balance Amount',
				fieldname: 'balance',
				fieldtype: 'Currency',
				default: 0,
				read_only: 1
			}
		],
		primary_action_label: 'Submit',
		primary_action(values) {//Create Payment Entry
			let amount = flt(values.amount);
			if (!amount || amount <= 0) {
				frappe.msgprint(__('Enter a payment amount.'));
				return;
			}
			if (amount > due + 0.005) {
				frappe.msgprint(__('Amount of payment cannot exceed {0}', [format_currency(due, frm.doc.currency)]));
				return;
			}
			frappe.call({
				method: 'aumms.aumms.doctype.jewellery_invoice.jewellery_invoice.create_payment_entry',
				args: {
					'mode_of_payment':values.mode_of_payment,
					'amount': amount,
					'docname': frm.doc.name,
					'reference_no': values.reference_no,
					'reference_date': values.reference_date,
					'posting_date': values.posting_date
				},
				btn: $('.primary-action'),
				freeze: true,
				callback: function(r) {
					//Keep the dialog open when the server rejected the amount
					if (r.message){
						d.hide();
						frm.reload_doc()
					}
				}
			})
		}
	});
	d.show();
}

let remove_previous_links = function(frm){
	if(frm.is_new()){
		frm.set_value('sales_order', );
		frm.set_value('sales_invoice', );
		frm.set_value('delivery_note', );
		frm.set_value('purchase_receipt', );
		frm.refresh_fields();
	}
}

let get_customer_advances= function(frm){
	frm.doc.items.forEach((child) => {
		frappe.call('aumms.aumms.utils.get_advances_payments_against_so_in_gold', {
			sales_order: frm.doc.sales_order,
			item_type: child.item_type,
			purity: child.purity,
			stock_uom: child.stock_uom
		}).then(r => {
			if(r.message){
				frm.clear_table('customer_advances');
				let total_advance_received = 0;
				let total_qty_obtained = 0;
				let purity = '';
				let uom = '';
				r.message.forEach((advance) => {
					frm.add_child('customer_advances', {
						'reference': advance.payment_entry,
						'posting_date': advance.posting_date,
						'item_type': advance.item_type,
						'purity': advance.purity,
						'amount': advance.amount,
						'board_rate': advance.board_rate,
						'stock_uom': advance.stock_uom,
						'qty_obtained': advance.qty_obtained
					});
					purity = advance.purity;
					uom = advance.stock_uom;
					total_advance_received = total_advance_received + (advance.amount);
					total_qty_obtained = total_qty_obtained + (advance.qty_obtained);
				});
				frm.set_value('total_advance_received', total_advance_received);
				frm.set_value('total_qty_obtained', total_qty_obtained);
				frm.set_value('uom', uom);
				frm.set_value('purity', purity);
				frm.save_or_update();
			}
		});
	});
}



// code to fetch the Item details

frappe.ui.form.on('Jewellery Invoice Item', {
	item_code: function(frm, cdt, cdn) {
		let d = locals[cdt][cdn];

		if (d.item_code) {
			
			if (frm.doc.delivery_date) {
				frappe.model.set_value(d.doctype, d.name, 'delivery_date', frm.doc.delivery_date);
			}

			// Step 1: Fetch making_charge
			fetch_and_set_making_charge(frm, d);

			// Step 2: Fetch item details for purity items
			if (d.is_purity_item) {
				frappe.call({
					method: 'aumms.aumms.doc_events.sales_order.get_item_details',
					args: {
						'item_code': d.item_code,
						'item_type': d.item_type,
						'date': frm.doc.transaction_date,
						'purity': d.purity,
						'stock_uom': d.stock_uom
					},
					callback: function(r) {
						if (r.message) {
							frappe.model.set_value(d.doctype, d.name, 'gold_weight', r.message['gold_weight']);
							frappe.model.set_value(d.doctype, d.name, 'stone_weight', r.message['stone_weight']);
							frappe.model.set_value(d.doctype, d.name, 'net_weight', r.message['net_weight']);
							frappe.model.set_value(d.doctype, d.name, 'stone_charge', r.message['stone_charge']);
							frappe.model.set_value(d.doctype, d.name, 'making_charge_percentage', r.message['making_charge_percentage']);
							frappe.model.set_value(d.doctype, d.name, 'board_rate', r.message['board_rate']);
							frappe.model.set_value(d.doctype, d.name, 'making_charge_based_on', r.message['making_charge_based_on']);

							// Calculate amount without making charge
							let amount_without_making_charge = r.message['gold_weight'] * r.message['board_rate'];
							frappe.model.set_value(d.doctype, d.name, 'amount_with_out_making_charge', amount_without_making_charge);

							// Calculate net amount without making charge
							let net_amount_without_making_charge = amount_without_making_charge + r.message['stone_charge'];
							frappe.model.set_value(d.doctype, d.name, 'net_amount_with_out_making_charge', net_amount_without_making_charge);

							// Set rate using the making_charge already fetched earlier
							let making_charge = d.making_charge || 0;
							let total_rate = (net_amount_without_making_charge + making_charge) / r.message['gold_weight'];
							frappe.model.set_value(d.doctype, d.name, 'rate', total_rate);

							frm.refresh_field('items');
						}
					}
				});
			}

			// Step 3: Fetch board_rate
			if (d.purity && d.stock_uom) {
				frappe.call({
					method: 'aumms.aumms.utils.get_board_rate',
					args: {
						'item_type': d.item_type,
						'date': frm.doc.transaction_date,
						'purity': d.purity,
						'stock_uom': d.stock_uom
					},
					callback: function(r) {
						if (r.message) {
							let board_rate = r.message;
							frappe.model.set_value(d.doctype, d.name, 'board_rate', board_rate);
							frm.refresh_field('items');
						}
					}
				});
			}
		}
	}
});

// // discount

frappe.ui.form.on('Stone Details - 2', {
	discount: function(frm, cdt, cdn) {
			calculate_discount_and_total(frm, cdt, cdn);
	},
	stone_weight: function(frm, cdt, cdn) {
		calculate_discount_and_total(frm, cdt, cdn);
	}

});

function calculate_discount_and_total(frm, cdt, cdn) {
	let row = locals[cdt][cdn];
	let final_amount;
	
	if (row.discount && flt(row.discount) !== 0) {
			final_amount = flt(row.stone_charge) * (1 - flt(row.discount) / 100);
	} else {
			final_amount = flt(row.stone_charge);
	}

	// Update the row's final amount
	frappe.model.set_value(cdt, cdn, 'custom_discount_final', final_amount);

	// Calculate total by checking each row
	let total = frm.doc.stone_details.reduce((sum, r) => {
			if (r.discount && flt(r.discount) !== 0) {
					return sum + flt(r.stone_charge) * (1 - flt(r.discount) / 100);
			} else {
					return sum + flt(r.stone_charge);
			}
	}, 0);

	frm.set_value('custom_discount_final', total);
	frm.refresh_fields(['stone_details', 'custom_discount_final']);
}




// code to set Grand Total 

frappe.ui.form.on('Jewellery Invoice', {
	items: {
		board_rate: calculate_total,
		gold_weight: calculate_total,
		making_charge: calculate_total,
		items_add: calculate_total,
		items_remove: calculate_total
	},
	custom_discount_final: function(frm) {
			calculate_total(frm);
	},
	discount_amount: function(frm) {
		calculate_total(frm);
	},
	custom_total_taxes_and_charges: function(frm) {
		calculate_total(frm);
	},
	disable_rounded_total: function(frm) {
		calculate_total(frm);
	},
	total_gold_amount: function(frm) {
		calculate_total(frm);
	}
});

function calculate_total(frm) {
	//Mirrors set_total_amount on the server. item.amount already carries the board rate,
	//the stone charge and the making charge, so it is the one figure to total.
	let total_amount = 0;
	let total_making_charge = 0;

	(frm.doc.items || []).forEach(function(item) {
			total_amount += flt(item.amount);
			total_making_charge += flt(item.making_charge);
	});

	let net_total = total_amount - flt(frm.doc.discount_amount);
	let grand_total = net_total + flt(frm.doc.custom_total_taxes_and_charges);

	frm.set_value('total_making_charge', total_making_charge);
	frm.set_value('grand_total', grand_total);
	if (frm.doc.disable_rounded_total) {
		frm.set_value('rounded_total', grand_total);
		frm.set_value('rounding_adjustment', 0);
	} else {
		let rounded_total = Math.round(grand_total);
		frm.set_value('rounded_total', rounded_total);
		//Only the difference made by rounding belongs here
		frm.set_value('rounding_adjustment', flt(rounded_total - grand_total, precision('rounding_adjustment')));
	}
}

//  code for stone details and discount
frappe.ui.form.on('Jewellery Invoice Item', {
	item_code: function(frm, cdt, cdn) {
			let row = locals[cdt][cdn];
			if (!row.item_code) return;
			
			fetch_and_add_stone_details(frm, row);
	}
});

// Fetch stone details from AuMMS Item
function fetch_and_add_stone_details(frm, row) {
	frappe.call({
			method: "frappe.client.get",
			args: {
					doctype: "AuMMS Item",
					name: row.item_code  
			},
			callback: function(r) {
					if (!r.message) {
							frappe.msgprint('No item details found');
							return;
					}

					let stone_details = r.message.stone_details || [];
					add_stone_details_to_table(frm, row.item_code, stone_details);
					
					if (frm.doc.customer) {
							apply_pricing_rules(frm);
					}
			}
	});
}

// Add stone details to child table
function add_stone_details_to_table(frm, item_code, stone_details) {
	
	stone_details.forEach(function(row) {
			let child = frm.add_child('stone_details');
			child.item_code = item_code;
			child.item_name = row.item_name;
			child.stone_type = row.stone_type;
			child.stone_weight = row.stone_weight;
			child.stone_charge = row.stone_charge;
	});

	frm.refresh_field('stone_details');
}

// Apply pricing rules based on customer

function apply_pricing_rules(frm) {
	frappe.call({
			method: "aumms.aumms.doctype.jewellery_invoice.jewellery_invoice.get_pricing_rule_and_items",
			args: {
					customer: frm.doc.customer
			},
			callback: function(r) {
					let discount_percentage = 0;
					let rule_items = [];

					if (r.message) {
							discount_percentage = r.message.discount_percentage || 0;
							rule_items = r.message.rule_items || [];
					}

					update_stone_discounts(frm, discount_percentage, rule_items);
			}
	});
}

// Update discounts 
function update_stone_discounts(frm, discount_percentage, rule_items) {
	frm.doc.stone_details.forEach(function(stone) {

			let matched_item = rule_items.find(function(item) {
					return item.item_code === stone.item_name;
			});
			
			// Apply discount if matched; otherwise, set discount to 0
			frappe.model.set_value(
					stone.doctype, 
					stone.name, 
					'discount', 
					matched_item ? discount_percentage : 0
			);
	});

	frm.refresh_field('stone_details');
}

//  fetch making charge
frappe.ui.form.on('Jewellery Invoice Item', {
	item_code: function(frm, cdt, cdn) {
			let row = locals[cdt][cdn];
			if (!row.item_code) {
					frappe.msgprint('Please select an Item Code');
					return;
			}
			
			fetch_and_set_making_charge(frm, row);
	}
});

function fetch_and_set_making_charge(frm, row) {
	frappe.call({
			method: "aumms.aumms.doctype.jewellery_invoice.jewellery_invoice.get_making_charge",
			args: {
					item_code: row.item_code
			},
			callback: function(r) {
					if (!r.message) {
							return;
					}

					update_making_charge(frm, row, r.message);
			},
	});
}

// Update the making charge in the row
function update_making_charge(frm, row, making_charge) {
	//Keep the fetched amount, it is what a Fixed making charge is read from
	frappe.model.set_value(row.doctype, row.name, 'is_fixed_making_charge', making_charge);
	set_making_charge(row);
	frm.refresh_field('items');
}

// Set the making charge of a row from whichever basis the item uses
function set_making_charge(row) {
	//A Fixed making charge is an amount on the item, a Percentage one is worked out per row.
	//Applying the percentage formula to a Fixed item multiplies by a zero percentage and
	//silently wipes the charge, which then goes missing from the totals.
	let making_charge = row.making_charge_based_on === 'Fixed'
		? flt(row.is_fixed_making_charge)
		: flt(row.amount_with_out_making_charge) * flt(row.making_charge_percentage) * 0.01;
	frappe.model.set_value(row.doctype, row.name, 'making_charge', making_charge);
}

// code for discounted amount
frappe.ui.form.on("Stone Details - 2", {
	stone_charge: function(frm, cdt, cdn) {
		calculate_discounted_stone_charge_and_print(frm);
	},
	stone_details_add: function(frm) {
		calculate_discounted_stone_charge_and_print(frm);
	},
	custom_discount_final: function(frm) {
		calculate_discounted_stone_charge_and_print(frm);
	}
});

function calculate_discounted_stone_charge_and_print(frm) {
	let total_stone_charge = 0;

	if (frm.doc.stone_details && frm.doc.stone_details.length) {
		frm.doc.stone_details.forEach(row => {
			let stone_charge = row.stone_charge || 0;
			total_stone_charge += stone_charge ;
		});
	}
	let discount = total_stone_charge - frm.doc.custom_discount_final || 0;

	frm.set_value("discount_amount", discount);
}
