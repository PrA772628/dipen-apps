# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ProductCategoryUpdateWizard(models.TransientModel):
    _name = "product.category.update.wizard"
    _description = "Product Category Update Wizard"

    @api.model
    def default_get(self, default_fields):
        res = super(ProductCategoryUpdateWizard,
                    self).default_get(default_fields)
        ids = self.env.context.get('active_ids', [])
        products = self.env['product.template'].browse(ids)
        res.update({'product_ids': [(6, 0, ids)]})
        return res

    internal_category_id = fields.Many2one(
        'product.category', string="Internal Category")
    product_ids = fields.Many2many('product.template', string="Products Name")
    all_categ = fields.Boolean("Select All Product")

    def update_category(self):
        self.ensure_one()
        ids = self.env.context.get('active_ids', [])
        products = self.env['product.template'].browse(ids)
        if self.internal_category_id:
            products.write({'categ_id': self.internal_category_id.id})
