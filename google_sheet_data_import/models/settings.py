from odoo import models, fields, api, _

class ImportDataSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    email = fields.Char('Email')
    p12_json_key = fields.Binary('Google API JSON key', attachment=True)

    def set_values(self):
        res = super(ImportDataSettings,self).set_values()
        set_value = self.env['ir.config_parameter'].sudo()
        set_value.set_param('google_sheet_data_import.email',self.email)
        set_value.set_param('google_sheet_data_import.p12_json_key',self.p12_json_key)
        return res

    @api.model
    def get_values(self):
        res = super(ImportDataSettings,self).get_values()
        set_value = self.env['ir.config_parameter'].sudo()
        email = set_value.get_param('google_sheet_data_import.email')
        p12_json_key = set_value.get_param('google_sheet_data_import.p12_json_key')
        res.update(
            email = email,
            p12_json_key = p12_json_key,
        )
        return res