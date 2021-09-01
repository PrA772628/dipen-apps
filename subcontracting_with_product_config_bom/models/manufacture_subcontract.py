
from odoo import api, fields, models, _


class BomSubcontract(models.Model):
    _inherit = 'mrp.bom'

    subcontract = fields.Boolean(string='Subcontract?')
    partner_id = fields.Many2one('res.partner', string='Supplier')
    service_product = fields.Many2one('product.product', string='Product')
    cost_per_unit = fields.Float(string='Cost per unit')
    picking_ids = fields.One2many('bom.pickings', 'picking_id')


class PickingsFromBOM(models.Model):
    _name = 'bom.pickings'
    _description = "BOM Pickings"

    picking_id = fields.Many2one('mrp.bom', 'picking_ids')
    picking_type = fields.Selection([('out', 'Delivery'), ('in', 'Reception')])
    product_id = fields.Many2one('product.product')
    product_qty = fields.Integer()


class ManufacturingSubcontract(models.Model):
    _inherit = 'mrp.production'

    p_subcontract = fields.Boolean(compute="_bom_subcontract")
    purchase_count = fields.Integer(compute='_purchase_count')
    delivery_raw_count = fields.Integer(compute='_delivery_raw_count')
    receipt_count = fields.Integer(compute='_receipt_count')
    no_update = fields.Boolean(compute='_get_pdr_status')

    def _purchase_count(self):
        for mo in self:
            pos = self.env['purchase.order'].search(
                [('manufacture_id', '=', mo.id)])
            mo.purchase_count = len(pos.ids)

    def _delivery_raw_count(self):
        for mo in self:
            dos = self.env['stock.picking'].search(
                [('manufacture_id', '=', mo.id), ('picking_type_code', '=', 'outgoing')])
            mo.delivery_raw_count = len(dos.ids)

    def _receipt_count(self):
        for mo in self:
            prs = self.env['stock.picking'].search(
                [('manufacture_id', '=', mo.id), ('picking_type_code', '=', 'incoming')])
            mo.receipt_count = len(prs.ids)

    @api.depends("bom_id")
    def _bom_subcontract(self):
        for record in self:
            if record.bom_id.subcontract:
                record.p_subcontract = True
            else:
                record.p_subcontract = False

    def action_cancel(self):
        mrp_cancel = super(ManufacturingSubcontract, self).action_cancel()
        if mrp_cancel:
            po_cancel = self.env['purchase.order'].search(
                [('manufacture_id', '=', self.id)])
            order_cancel = self.env['stock.picking'].search(
                [('manufacture_id', '=', self.id)])
            for rec in po_cancel:
                rec.button_cancel()
            for rec in order_cancel:
                rec.action_cancel()
        return mrp_cancel

    def _update_raw_move(self, bom_line, line_data):
        move = super(ManufacturingSubcontract,
                     self)._update_raw_move(bom_line, line_data)
        purchase = self.env['purchase.order'].search(
            [('manufacture_id', '=', self.id)])
        if purchase:
            for line in purchase.order_line:
                line.write({'product_qty': self.product_qty})

        picking_out = self.env['stock.picking'].search([('manufacture_id', '=', self.id),
                                                        ('picking_type_id.code', '=', 'outgoing')])

        if picking_out:
            for line in picking_out.move_lines:
                record = self.bom_id.picking_ids.filtered(
                    lambda l: l.product_id.id == line.product_id.id)
                if record:
                    line.write(
                        {'product_uom_qty': record.product_qty * self.product_qty})
        return move

    @api.depends("move_raw_ids.product_id")
    def _get_pdr_status(self):
        # get status of po, delivery and receipt
        for mrpOrder in self:
            purchase_orders = self.env['purchase.order'].search([('manufacture_id',
                                                                  '=', mrpOrder.id), ('state', 'in', ['purchase', 'done', 'cancel'])])
            pickings = self.env['stock.picking'].search([('manufacture_id',
                                                          '=', mrpOrder.id), ('state', 'in', ['done', 'cancel'])])
            if purchase_orders or pickings:
                mrpOrder.no_update = True
            else:
                mrpOrder.no_update = False


class PurchaseOrderSubcontract(models.Model):
    _inherit = 'purchase.order'

    manufacture_id = fields.Many2one('mrp.production')

    def action_subcontract_manufacture(self):
        self.ensure_one()
        return {
            'res_model': 'mrp.production',
            'res_id': self.manufacture_id.id,
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
            bom = self.manufacture_id.bom_id
            picking_type_in = self.env['stock.picking.type'].search(
                [('code', '=', 'incoming')], limit=1)
            if bom.subcontract and bom.picking_ids.filtered(lambda l: l.picking_type == 'in'):
                for rec in bom.picking_ids.filtered(lambda l: l.picking_type == 'in'):
                    move_lines = [
                        (0, 0, {
                            'name': 'Stock Move',
                            'product_id': rec.product_id.id,
                            'location_id': bom.partner_id.property_stock_supplier.id,
                            'location_dest_id': picking_type_in and picking_type_in.default_location_dest_id and picking_type_in.default_location_dest_id.id or False,
                            'product_uom_qty': rec.product_qty * self.manufacture_id.product_qty,
                            'product_uom': rec.product_id.uom_id.id,
                        })]

                    self.env['stock.picking'].create({
                        'location_id': bom.partner_id.property_stock_supplier.id,
                        'picking_type_id': picking_type_in and picking_type_in.id or False,
                        'partner_id': bom.partner_id.id,
                        'location_dest_id': picking_type_in and picking_type_in.default_location_dest_id and picking_type_in.default_location_dest_id.id or False,
                        'manufacture_id': self.manufacture_id.id,
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
            bom = record.production_id.bom_id
            if bom and bom.subcontract:
                record.subcontract_orders = True
            else:
                record.subcontract_orders = False

    @api.model
    def create(self, values):
        stock_move = super(StockMoveSubcontract, self).create(values)

        if stock_move.subcontract_orders:
            bom = stock_move.production_id.bom_id
            po_line = [
                (0, 0, {
                    'name': bom.service_product.display_name,
                    'product_id': bom.service_product.id,
                    'product_qty': stock_move.product_uom_qty,
                    'date_planned': fields.Datetime.now(),
                    'product_uom': bom.service_product.uom_id.id,
                    'price_unit': bom.cost_per_unit,
                })
            ]

            po = self.env['purchase.order'].create({
                'partner_id': bom.partner_id.id,
                'order_line': po_line,
                'manufacture_id': stock_move.production_id.id
            })

            stock_move.write(
                {'subcontract_po_line_id': po.order_line and po.order_line[0].id or False})

            move_lines = []
            picking_type_out = self.env['stock.picking.type'].search(
                [('code', '=', 'outgoing')], limit=1)
            if bom.subcontract and bom.picking_ids.filtered(lambda l: l.picking_type == 'out'):
                for rec in bom.picking_ids.filtered(lambda l: l.picking_type == 'out'):
                    move_lines.append(
                        (0, 0, {
                            'name': 'Stock Move',
                            'product_id': rec.product_id.id,
                            'location_id': picking_type_out.default_location_src_id.id,
                            'location_dest_id': bom.partner_id.property_stock_customer.id,
                            'product_uom_qty': rec.product_qty,
                            'product_uom': rec.product_id.uom_id.id,
                        }))

                picking_id = self.env['stock.picking'].create({
                    'partner_id': bom.partner_id.id,
                    'location_id': picking_type_out.default_location_src_id.id,
                    'picking_type_id': picking_type_out.id,
                    'location_dest_id': bom.partner_id.property_stock_customer.id,
                    'manufacture_id': stock_move.production_id.id,
                    'move_raw_id': stock_move.id,
                    'move_lines': move_lines,
                })

        return stock_move
