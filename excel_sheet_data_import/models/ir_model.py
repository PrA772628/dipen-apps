from odoo import models, fields, api, _


class InheritIrModel(models.Model):
    _inherit = 'ir.model'

    change_data = fields.Boolean(string='Allow Change Data/Fields Through Excel Sheet')
