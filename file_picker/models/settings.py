from odoo import models, fields, api, _

class ImportDataSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    drive_api_key = fields.Char('Google Drive API Key',config_parameter="file_picker.drive_api_key")
    drive_client_id = fields.Char('Oauth Client Id',config_parameter="file_picker.drive_client_id")
    project_id = fields.Char('Project Id',config_parameter="file_picker.project_id")
    dropbox_api_key = fields.Char('Dropbox API Key',config_parameter="file_picker.dropbox_api_key")
    onedrive_app_id = fields.Char('OneDrive Application Id',config_parameter="file_picker.onedrive_app_id")
    