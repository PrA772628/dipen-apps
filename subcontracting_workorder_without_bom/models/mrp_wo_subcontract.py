# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api,_
from datetime import datetime


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    subcontract_without_bom = fields.Boolean()
    picking_ids = fields.One2many('workorder.pickings','picking_id')

class PickingsFromWorkorder(models.Model):
    _name = 'workorder.pickings'
    _description = "Workorder Pickings"
    
    picking_id = fields.Many2one('mrp.routing.workcenter','picking_ids')
    picking_type = fields.Selection([('out', 'Delivery'),('in', 'Reception')])
    product_id = fields.Many2one('product.product')
    product_qty = fields.Integer()

class SubcontractWorkOrder(models.Model):
    _inherit = 'mrp.workorder'

    is_subcontract_without_bom = fields.Boolean(compute="_subcontract_wo")

    @api.depends('receipt_count')
    def _compute_receipt_done(self):
        result = super(SubcontractWorkOrder, self)._compute_receipt_done()
        for order in self:
            if order.operation_id and order.operation_id.subcontract and order.operation_id.subcontract_without_bom:
                PO_objs = self.env['purchase.order'].search([('workorder_id', '=', order.id), ('state', 'in', ['purchase','done'])])
                if PO_objs: 
                    order.got_subcontracted_product = True
                else:
                    order.got_subcontracted_product = False          
        return result   


    @api.depends("operation_id")
    def _subcontract_wo(self):
        result = super(SubcontractWorkOrder, self)._subcontract_wo()

        if self.name == self.operation_id.name and self.operation_id.subcontract and self.operation_id.show_wo_subcontract and self.operation_id.subcontract_without_bom:            
            self.is_subcontract_without_bom = True
        else:
            self.is_subcontract_without_bom = False
        return result

    def btn_start_subcontract(self):
        # Replace Actual module calling from subcontract workorder
        bom_product = None
        bom_product_qty = 0
        move_raw_id = False
        for order in self:
            order.button_start()
            stock_lines = []
            if order.production_id.state != 'progress':
                order.production_id.write({'state': 'progress'})
            purchase_order = self.env['purchase.order']
            order_line = self.env['purchase.order.line']

            po_id = purchase_order.create({
                'partner_id': order.operation_id.partner_id.id,
                'workorder_id': order.id,
                'manufacture_id': order.production_id.id
                })
            order_line_id = order_line.create({
                'product_id': order.operation_id.service_product.id,
                'name': order.operation_id.service_product.name,
                'date_planned': datetime.now(),
                'product_qty': 1.0,
                'product_uom': order.operation_id.service_product.uom_id.id,
                'price_unit': order.operation_id.cost_per_unit,
                'order_id': po_id.id
                })

            if order.operation_id and order.operation_id.subcontract_without_bom:
                if order.operation_id.picking_ids.filtered(lambda l:l.picking_type == 'out') :
                    
                    picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)                
                    move = order.production_id
                    bom_product = move.product_id
                    bom_product_qty = move.product_qty
                   
                    order_line_id.write({'product_qty': move.product_qty})
                    for wo_pickings in order.operation_id.picking_ids.filtered(lambda l: l.picking_type == 'out'):
                        stock_lines.append((0, 0, {
                            'product_id': wo_pickings.product_id.id,
                            'name': 'Stock Move',
                            'product_uom': wo_pickings.product_id.uom_id.id,
                            'product_uom_qty': wo_pickings.product_qty,
                            'location_id': picking_type_id.default_location_src_id.id,
                            'location_dest_id': order.operation_id.partner_id.property_stock_customer.id,
                            }))

                    self.env['stock.picking'].create({
                        'partner_id': order.operation_id.partner_id.id,
                        'picking_type_id': picking_type_id.id,
                        'location_id': picking_type_id.default_location_src_id.id,
                        'location_dest_id': order.operation_id.partner_id.property_stock_customer.id,
                        'move_lines': stock_lines,
                        'workorder_id': order.id,
                        'manufacture_id': order.production_id.id
                        })

            else:
                picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)                
                for move in order.production_id.move_raw_ids:
                    if move.product_id.bom_ids.filtered(lambda l:l.id == order.bom_id.id):
                        bom_product = move.product_id
                        bom_product_qty = move.product_uom_qty
                        move_raw_id = move
                        move.write({'subcontract_po_line_id': order_line_id.id})
                        order_line_id.write({'product_qty': move.product_uom_qty})
                        for bom_line in order.bom_id.bom_line_ids:
                            stock_lines.append((0, 0, {
                                'product_id': bom_line.product_id.id,
                                'name': 'Stock Move',
                                'product_uom': bom_line.product_id.uom_id.id,
                                'product_uom_qty': bom_line.product_qty * move.product_uom_qty,
                                'location_id': picking_type_id.default_location_src_id.id,
                                'location_dest_id': order.operation_id.partner_id.property_stock_customer.id,
                                'subcontract_bom_line_id': bom_line.id
                                }))

                self.env['stock.picking'].create({
                    'partner_id': order.operation_id.partner_id.id,
                    'picking_type_id': picking_type_id.id,
                    'location_id': picking_type_id.default_location_src_id.id,
                    'location_dest_id': order.operation_id.partner_id.property_stock_customer.id,
                    'move_lines': stock_lines,
                    'workorder_id': order.id,
                    'subcontract_product_id': bom_product.id,
                    'subcontract_product_qty': bom_product_qty,
                    'move_raw_id': move_raw_id.id,
                    'manufacture_id': order.production_id.id
                    })


class StockPicking(models.Model):
    _inherit = 'stock.picking'


    def _validate_subcontracting_picking(self):
        picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'incoming')], limit=1)
        for picking in self:
            if picking.workorder_id and not picking.subcontract_product_id:
                if picking.workorder_id.operation_id and picking.workorder_id.operation_id.subcontract_without_bom and picking.workorder_id.operation_id.picking_ids.filtered(lambda l:l.picking_type == 'in'):    
                    move_line = []
                    for rec in picking.workorder_id.operation_id.picking_ids.filtered(lambda l: l.picking_type == 'in'):
                        move_line += [
                            (0, 0, {
                                    'product_id': rec.product_id.id,
                                    'name': 'Stock Move',
                                    'product_uom': rec.product_id.uom_id.id,
                                    'product_uom_qty': rec.product_qty,
                                    'location_dest_id': picking_type_id.default_location_dest_id.id,
                                    'location_id': picking.workorder_id.operation_id.partner_id.property_stock_supplier.id
                            })
                        ]

                    move_line and self.env['stock.picking'].create({
                        'partner_id': picking.workorder_id.operation_id.partner_id.id,
                        'picking_type_id': picking_type_id.id,
                        'location_id': picking.workorder_id.operation_id.partner_id.property_stock_supplier.id,
                        'location_dest_id': picking_type_id.default_location_dest_id.id,
                        'move_lines': move_line,
                        'workorder_id': picking.workorder_id.id
                        })
                elif picking.workorder_id and picking.subcontract_product_id and picking.workorder_id.operation_id.subcontract and not picking.workorder_id.operation_id.subcontract_without_bom:
                    move_line = [
                        (0, 0, {
                                'product_id': picking.subcontract_product_id.id,
                                'name': 'Stock Move',
                                'product_uom': picking.subcontract_product_id.uom_id.id,
                                'product_uom_qty': picking.subcontract_product_qty,
                                'location_dest_id': picking_type_id.default_location_dest_id.id,
                                'location_id': picking.workorder_id.operation_id.partner_id.property_stock_supplier.id
                        })
                    ]
                    self.env['stock.picking'].create({
                        'partner_id': picking.workorder_id.operation_id.partner_id.id,
                        'picking_type_id': picking_type_id.id,
                        'location_id': picking.workorder_id.operation_id.partner_id.property_stock_supplier.id,
                        'location_dest_id': picking_type_id.default_location_dest_id.id,
                        'move_lines': move_line,
                        'workorder_id': picking.workorder_id.id
                    })