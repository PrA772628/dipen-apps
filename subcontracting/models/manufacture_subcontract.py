from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round

class BomSubcontract(models.Model):
    _inherit = 'mrp.bom'

    subcontract = fields.Boolean(string='Subcontract?')
    partner_id = fields.Many2one('res.partner',string='Supplier')
    service_product = fields.Many2one('product.product',string='Product')
    cost_per_unit = fields.Float(string='Cost per unit')
    
class ManufacturingSubcontract(models.Model):
    _inherit = 'mrp.production'

    p_subcontract = fields.Boolean(compute="_bom_subcontract", default=False, store=True)
    purchase_count = fields.Integer(compute='_purchase_count')
    delivery_raw_count = fields.Integer(compute='_delivery_raw_count')
    receipt_count = fields.Integer(compute='_receipt_count')
    no_update = fields.Boolean(compute='_get_pdr_status')

    def _purchase_count(self):
        for mo in self:
            pos = self.env['purchase.order'].search([('manufacture_id', '=', mo.id)])
            mo.purchase_count = len(pos.ids)
    def _delivery_raw_count(self):
        for mo in self:
            dos = self.env['stock.picking'].search([('manufacture_id', '=', mo.id),('picking_type_code','=', 'outgoing')])
            mo.delivery_raw_count = len(dos.ids)
    def _receipt_count(self):
        for mo in self:
            prs = self.env['stock.picking'].search([('manufacture_id', '=', mo.id),('picking_type_code','=', 'incoming')])
            mo.receipt_count = len(prs.ids)

    @api.depends("move_raw_ids.product_id")
    def _bom_subcontract(self):
        for record in self:
            if record.move_raw_ids:
                for rec in record.move_raw_ids:
                    boms = self.env['mrp.bom']._bom_find(product=rec.product_id, bom_type='normal')
                    for bom in boms:
                        if bom.subcontract:
                            record.p_subcontract = True
                        else:
                            record.p_subcontract = False
            else:
                record.p_subcontract = False

    def action_cancel(self):
        mrp_cancel=super(ManufacturingSubcontract, self).action_cancel()
        if mrp_cancel:
            po_cancel=self.env['purchase.order'].search([('manufacture_id','=',self.id)])
            order_cancel=self.env['stock.picking'].search([('manufacture_id','=',self.id)])
            for rec in po_cancel:
                rec.button_cancel()
            for rec in order_cancel:
                rec.action_cancel()     
        return mrp_cancel

    def _update_raw_move(self, bom_line, line_data):
        move = super(ManufacturingSubcontract, self)._update_raw_move(bom_line, line_data)

        if move[0].subcontract_po_line_id:
            move[0].subcontract_po_line_id.write({'product_qty':line_data['qty']})
        
        picking = self.env['stock.picking'].search([('manufacture_id', '=', self.id),
         ('picking_type_id.code', '=', 'outgoing'), ('move_raw_id', '=', move[0].id)])

        if picking:
            for line in picking.move_lines:
                bom_qty = line.subcontract_bom_line_id.product_qty
                line.write({'product_uom_qty':bom_qty * line_data['qty']})
        return move
    
    @api.depends("move_raw_ids.product_id")
    def _get_pdr_status(self):
        # get status of po, delivery and receipt
        for mrpOrder in self:
            purchase_orders = self.env['purchase.order'].search([('manufacture_id', 
                '=', mrpOrder.id), ('state', 'in', ['purchase','done','cancel'])])
            pickings = self.env['stock.picking'].search([('manufacture_id', 
                '=', mrpOrder.id), ('state', 'in', ['done','cancel'])])
            if purchase_orders or pickings:
                mrpOrder.no_update = True
            else:
                mrpOrder.no_update = False


class PurchaseOrderSubcontract(models.Model):
    _inherit='purchase.order'

    manufacture_id=fields.Many2one('mrp.production')

    def action_subcontract_manufacture(self):
        self.ensure_one()
        return {
            'res_model': 'mrp.production',
            'res_id':self.manufacture_id.id,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'context':  self._context
        }

class StockPickingSubcontract(models.Model):
    _inherit = 'stock.picking'

    manufacture_id = fields.Many2one('mrp.production')
    move_raw_id = fields.Many2one('stock.move')

    def button_validate(self):
        picking = super(StockPickingSubcontract, self).button_validate()
        if self.manufacture_id:
            if self.move_raw_id:
                bom = self.env['mrp.bom']._bom_find(product=self.move_raw_id.product_id)
                picking_type_in = self.env['stock.picking.type'].search([('code', '=', 'incoming')], limit=1)
                if bom:
                    move_lines = [
                        (0, 0, {
                            'name': self.move_raw_id.product_id.display_name,
                            'product_id': self.move_raw_id.product_id.id,
                            'location_id': self.partner_id.property_stock_supplier.id,
                            'location_dest_id': picking_type_in.default_location_dest_id.id,
                            'product_uom_qty': self.move_raw_id.product_uom_qty,
                            'product_uom': self.move_raw_id.product_id.uom_id.id,
                        })]

                    self.env['stock.picking'].create({
                            'location_id': self.partner_id.property_stock_supplier.id,
                            'picking_type_id': picking_type_in.id,
                            'partner_id': bom.partner_id.id,
                            'location_dest_id': picking_type_in.default_location_dest_id.id,
                            'manufacture_id': self.move_raw_id.raw_material_production_id.id,
                            'move_lines': move_lines
                        })

        return picking



class StockMoveSubcontract(models.Model):
    _inherit = 'stock.move'

    subcontract_orders = fields.Boolean(compute="_orders_subcontract")
    subcontract_bom_line_id = fields.Many2one('mrp.bom.line')
    subcontract_po_line_id = fields.Many2one('purchase.order.line')

    @api.depends("product_id")
    def _orders_subcontract(self):
        for record in self:
            bom = self.env['mrp.bom']._bom_find(product=record.product_id)
            if bom.subcontract:
                record.subcontract_orders = True
            else:
                record.subcontract_orders = False
            
    @api.model
    def create(self, values):
        stock_move = super(StockMoveSubcontract, self).create(values)
        config_settings = self.env['res.config.settings'].sudo().search([], order="id desc", limit=1)
        if stock_move.subcontract_orders :
            bom = self.env['mrp.bom']._bom_find(product=stock_move.product_id)
            po_line = [
                (0, 0,
                    {
                        'name': bom.service_product.display_name,
                        'product_id': bom.service_product.id,
                        'product_qty': stock_move.product_uom_qty,
                        'date_planned': fields.Datetime.now(),
                        'product_uom': bom.service_product.uom_id.id,
                        'price_unit': bom.cost_per_unit,
                    }
                 )
            ]
            
            po = self.env['purchase.order'].create({
                'partner_id':bom.partner_id.id,
                'order_line': po_line,
                'manufacture_id' : stock_move.raw_material_production_id.id
                })

            stock_move.write({'subcontract_po_line_id': po.order_line.id})

            move_lines = []
            picking_type_out = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)
                
            for bom_line in bom.bom_line_ids:
                move_lines.append(
                    (0, 0,
                        {
                            'name': bom_line.product_id.display_name,
                            'product_id': bom_line.product_id.id,
                            'location_id': picking_type_out.default_location_src_id.id,
                            'location_dest_id': bom.partner_id.property_stock_customer.id,
                            'product_uom_qty': bom_line.product_qty * stock_move.product_uom_qty,
                            'product_uom': bom_line.product_id.uom_id.id,
                            'subcontract_bom_line_id': bom_line.id
                        }
                    ))
                
            picking_id = self.env['stock.picking'].create({
                'partner_id': bom.partner_id.id,
                'location_id': picking_type_out.default_location_src_id.id,
                'picking_type_id': picking_type_out.id,
                'location_dest_id': bom.partner_id.property_stock_customer.id,
                'manufacture_id': stock_move.raw_material_production_id.id,
                'move_raw_id': stock_move.id,
                'move_lines': move_lines,
                })

        return stock_move


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    subcontract_by_wo = fields.Boolean()

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        Param = self.env['ir.config_parameter'].sudo()
        Param.set_param("subcontract_by_wo", self.subcontract_by_wo)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            subcontract_by_wo=self.env['ir.config_parameter'].sudo().get_param('subcontract_by_wo'),
        )
        return res