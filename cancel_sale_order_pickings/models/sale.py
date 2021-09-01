# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.tools import float_is_zero, pycompat
from odoo.tools.float_utils import float_round
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection(selection_add=[('cancel_shipment', 'Cancelled Shipments')])

    def action_draft(self):
        orders = self.filtered(lambda s: s.state in ['cancel', 'sent','cancel_shipment'])
        return orders.write({
            'state': 'draft',
        })

    def action_cancel_forced(self):
        for order in self:
            pickings = []
            for picking in order.picking_ids.filtered(lambda l:l.state not in ['done', 'cancel']):
                picking.action_cancel()

            done_state_pickings = order.picking_ids.filtered(lambda l:l.state == 'done').sorted(key=lambda x: x.id, reverse=True)
            for picking in done_state_pickings:
                product_return_moves = []
                srp = self.env['stock.return.picking'].create({'picking_id':picking.id,
                    'location_id': picking.location_id.id})
                for move in picking.move_lines:
                    if move.scrapped:
                        continue
                    # if move.move_dest_ids:
                    #     move_dest_exists = True
                    quantity = move.product_qty - sum(move.move_dest_ids.filtered(lambda m: m.state in ['partially_available', 'assigned', 'done']).\
                                                      mapped('move_line_ids').mapped('product_qty'))
                    quantity = float_round(quantity, precision_rounding=move.product_uom.rounding)
                    product_return_moves.append((0, 0, {'product_id': move.product_id.id, 'quantity': quantity, 'move_id': move.id, 'uom_id': move.product_id.uom_id.id}))
                
                srp.write({'product_return_moves': product_return_moves})
                new_picking = srp.create_returns()
                to_be_done = self.env['stock.picking'].browse(new_picking['res_id'])
                if to_be_done.carrier_id:
                    to_be_done.write({'carrier_id': False})
                for line in to_be_done.move_line_ids:
                    line.write({'qty_done': line.product_uom_qty})

                for move in to_be_done.move_lines:
                    lots = move.origin_returned_move_id.mapped('move_line_ids').mapped('lot_id')
                    for line_id in move.move_line_ids:
                        
                        if lots:
                            count = 0
                            for line_id in move.move_line_ids:
                                if len(lots) >= count+1:
                                    line_id.write({'lot_id': lots[count].id})
                                    count += 1
                to_be_done._action_done()
            if order.invoice_ids:
                for invoice in order.invoice_ids:
                    if invoice.state == 'draft':
                        invoice.button_cancel()
                    elif invoice.state == 'posted' and invoice.invoice_payment_state != 'paid':
                        if invoice.amount_total != invoice.amount_residual:
                            raise UserError(_('You cannot cancel an invoice which is partially paid. You need to unreconcile related payment entries first.'))
                    elif invoice.state == 'posted' and invoice.invoice_payment_state == 'paid':
                        raise UserError(_('You need to first unreconcile paid invoice : %s and cancel this out.'% (invoice.name, )))
            order.write({'state': 'cancel_shipment'})