# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api,_
from datetime import datetime

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    subcontract_by_wo = fields.Boolean()

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['subcontract_by_wo'] = self.env['ir.config_parameter'].sudo().get_param('subcontract_by_wo', default=False)
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('subcontract_by_wo', self.subcontract_by_wo)
        super(ResConfigSettings, self).set_values()

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    workorder_id = fields.Many2one('mrp.workorder', string="Workorder")

class BomSubcontract(models.Model):
    _inherit = 'mrp.routing.workcenter'

    subcontract = fields.Boolean()
    new_bom_id = fields.Many2one('mrp.bom', string="Bill Of Material")
    partner_id = fields.Many2one('res.partner',string='Supplier')
    service_product = fields.Many2one('product.product',string='Product')
    cost_per_unit = fields.Float(string='Cost per unit')
    show_wo_subcontract = fields.Boolean(compute="_show_wo_subcontract")

    # @api.multi
    @api.depends("subcontract")
    def _show_wo_subcontract(self):
        sw_con = self.env['ir.config_parameter'].sudo().get_param('subcontract_by_wo')
        for rec in self:
            rec.show_wo_subcontract = sw_con


class BomSubcontract(models.Model):
    _inherit = 'mrp.bom'
    
    show_bom_subcontract = fields.Boolean(compute="_show_bom_subcontract")

    @api.depends("subcontract")
    def _show_bom_subcontract(self):
        self.show_bom_subcontract = self.env['ir.config_parameter'].sudo().get_param('subcontract_by_wo')
    

class SubcontractWorkOrder(models.Model):
    _inherit = 'mrp.workorder'

    bom_id = fields.Many2one(related='operation_id.new_bom_id',string='Bill Of Material')
    subcontract_wo = fields.Boolean(compute='_subcontract_wo')
    purchase_count = fields.Integer(compute='_purchase_count')
    delivery_count = fields.Integer(compute='_delivery_count')
    receipt_count = fields.Integer(compute='_receipt_count')
    got_subcontracted_product = fields.Boolean(compute='_compute_receipt_done')

    @api.depends('receipt_count')
    def _compute_receipt_done(self):
        for order in self:
            done_receipts = self.env['stock.picking'].search([('workorder_id', '=', order.id), 
                ('picking_type_code','=', 'incoming'), ('state', '=', 'done')])
            if done_receipts:
                order.got_subcontracted_product = True
            else:
                order.got_subcontracted_product = False

    def _purchase_count(self):
        for order in self:
            pos = self.env['purchase.order'].search([('workorder_id', '=', order.id)])
            order.purchase_count = len(pos.ids)

    def _delivery_count(self):
        for order in self:
            dos = self.env['stock.picking'].search([('workorder_id', '=', order.id),('picking_type_code','=', 'outgoing')])
            order.delivery_count = len(dos.ids)

    def _receipt_count(self):
        for order in self:
            prs = self.env['stock.picking'].search([('workorder_id', '=', order.id),('picking_type_code','=', 'incoming')])
            order.receipt_count = len(prs.ids)

    @api.depends("operation_id")
    def _subcontract_wo(self):
        
        for subcontract in self:
            
            if subcontract.name == subcontract.operation_id.name and subcontract.operation_id.subcontract and subcontract.operation_id.show_wo_subcontract:
                subcontract.subcontract_wo = True
            else:
               subcontract.subcontract_wo = False
    
    def btn_start_subcontract(self):
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
            # order.write({'state': 'progress'})

    def btn_done_subcontract(self):
        for order in self:
            order.record_production()
            # order.write({'state': 'done'})
            # if order.next_work_order_id:
            #     order.next_work_order_id.write({'state': 'ready'})


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    workorder_id = fields.Many2one('mrp.workorder', string="Workorder")
    subcontract_product_id = fields.Many2one('product.product')
    subcontract_product_qty = fields.Float()


    def _validate_subcontracting_picking(self):
        picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'incoming')], limit=1)
        for picking in self:
            if picking.workorder_id and picking.subcontract_product_id:
                move_line = [
                    (0, 0, {
                            'product_id': picking.subcontract_product_id.id,
                            'name': 'Stock Move',
                            'product_uom': picking.subcontract_product_id.uom_id.id,
                            'product_uom_qty': picking.subcontract_product_qty * picking.workorder_id.production_id.product_qty,
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

    # def button_validate(self):
    #     super_picking = super(StockPicking, self).button_validate()
    #     if self.picking_type_id.code == "outgoing":
    #         self._validate_subcontracting_picking()
    #     return super_picking

    def _action_done(self):
        super_picking = super(StockPicking, self)._action_done()
        if self.picking_type_id.code == "outgoing":
            self._validate_subcontracting_picking()
        return super_picking