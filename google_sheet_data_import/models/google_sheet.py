import base64
import json
import gspread
from datetime import date
from datetime import datetime
from httplib2 import ServerNotFoundError
from gspread.exceptions import NoValidUrlKeyFound, SpreadsheetNotFound
from oauth2client.service_account import ServiceAccountCredentials
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import config

import logging
_logger = logging.getLogger(__name__)

SHEET_APP = ("Google Spreadsheet Import Issue\n"
             "--------------------------------------------------")
SCOPE = ['https://spreadsheets.google.com/feeds']
TYPE_LISTS = ['integer', 'float', 'char',
              'text', 'date', 'datetime', 'boolean']


class GoogleSpreadsheetImport(models.Model):
    _name = 'google.spreadsheet.import'
    _description = 'Google Spreadsheet Import'

    name = fields.Char('Name', required=True)
    document_url = fields.Char('URL', required=True)
    document_sheet = fields.Char('WorkSheet Name', required=True)

    def open_document(self, email, p12_json_key):
        # Auhentification
        self.ensure_one()
        try:
            p12_key_file_data = json.loads(base64.b64decode(p12_json_key))
        except:
            raise UserError(
                _("The Google private json key is might not added or improper. Please go to configuration and check properly."))

        creds = ServiceAccountCredentials._from_parsed_json_keyfile(
            p12_key_file_data, SCOPE)

        try:
            gc = gspread.authorize(creds)
        except ServerNotFoundError:
            if config.get('debug_mode'):
                raise
            raise ValidationError(_(SHEET_APP + "\nCheck your internet connection.\n"
                                    "Impossible to establish a connection "
                                    "with Google Services"))
        try:
            document = gc.open_by_url(self.document_url)
        except NoValidUrlKeyFound:
            if config.get('debug_mode'):
                raise
            raise ValidationError(
                _(SHEET_APP + '\nGoogle Drive: No valid key found in URL'))
        except SpreadsheetNotFound:
            if config.get('debug_mode'):
                raise
            raise ValidationError(
                _(SHEET_APP + "\nSpreadsheet Not Found"
                  "\n\nResolution\n----------------\n"
                  "Check URL file & sharing options with it "
                  "with this google user:\n\n%s" % email))
        except Exception as e:
            if config.get('debug_mode'):
                raise
            raise ValidationError(_("Google Drive: %s" % e.message))
        return document

    def create_product_field(self, model, field):
        IrModelFields = self.env['ir.model.fields']

        field_list = field.split(':')
        if not field_list:
            raise UserError(_("Google Sheet Header is not define."))

        field_name = field_list[0]
        product_vals = {
            'name': field_name,
            'field_description': field_name,
            'store': True,
            'model_id': model.id,
            'state': 'manual',
        }
        if len(field_list) == 2 and field_list[1].lower() in TYPE_LISTS:
            product_vals.update({
                'ttype': field_list[1].lower(),
            })
            return IrModelFields.create(product_vals)

        return False

    def check_field_exits(self, row):
        self.ensure_one()
        IrModelFields = self.env['ir.model.fields']
        IrModel = self.env['ir.model']
        product_model = IrModel.search([
            ('model', '=', self.document_sheet)
        ], limit=1)

        if product_model:
            for field_name in row:
                field_name_and_type = field_name.split(':')
                if field_name_and_type:
                    product_find_field = IrModelFields.search([
                        ('model_id', '=', product_model.id),
                        ('name', '=', field_name_and_type[0])
                    ])

                if not product_find_field and field_name_and_type[0].startswith('x_'):
                    self.create_product_field(product_model, field_name)

        return False

    def import_data(self, data, master_row_field):
        self.ensure_one()

        IrModelFields = self.env['ir.model.fields']
        IrModel = self.env['ir.model']

        IrGoogleDefineModel = IrModel.search([
            ('model', '=', self.document_sheet)
        ], limit=1)

        vals = {}
        if IrGoogleDefineModel:
            sheetModel = self.env[self.document_sheet]
            for d in data:
                field_list = d.split(':')
                if field_list:
                    field_name = field_list[0]

                    product_find_field = IrModelFields.search([
                        ('model_id', '=', IrGoogleDefineModel.id),
                        ('name', '=', field_name)
                    ])
                    if product_find_field and isinstance(product_find_field.ttype, type(data[d])):
                        vals.update({
                            field_name: data[d],
                        })
                        if product_find_field.ttype != 'boolean' and data[d] == 'FALSE':
                            vals.update({
                                field_name: False
                            })
                        elif product_find_field.ttype == 'date':
                            vals.update({
                                field_name: data[d].replace('/', '-'),
                                field_name: data[d]
                            })
                        elif product_find_field.ttype == 'datetime':
                            vals.update({
                                field_name: data[d].replace('/', '-'),
                                field_name: datetime.strptime(
                                    data[d], '%Y-%m-%d %H:%M:%S')
                            })
                        elif product_find_field.ttype == 'many2one':

                            rec = IrModel.search([
                                ('model', '=', product_find_field.relation)
                            ])
                            new_product_find_field = self.env[rec.model].search([
                                ('name', '=ilike', data[d])
                            ])
                            vals.update({
                                field_name: new_product_find_field.id,
                            })
                    else:
                        vals.update({
                            field_name: data[d],
                        })
            prod_obj = None
            if master_row_field in vals.keys():
                prod_obj = sheetModel.search([
                    (master_row_field, '=', vals.get(master_row_field))
                ])
            if prod_obj:
                try:
                    prod_obj.write(vals)
                except Exception as e:
                    _logger.info(
                        _("Can not write Value of this Data: %s\n Route: %s" % (vals, e)))
                    raise UserError(
                        _("Error while import data \n %s\n\n Hint: Please check field name and it's TYPE if you create new." % e))
            else:
                try:
                    sheetModel.create(vals)
                except Exception as e:
                    _logger.info(
                        _("Can not create Value of this Data: %s\n Route: %s" % (vals, e)))
                    raise UserError(
                        _("Error while import data \n %s\n\n Hint: Please check field name and it's TYPE if you create new." % e))
        return True

    def show_notification(self):
        self.env.user.notify_info(
            message=_('Google sheet data is successfully imported to Odoo.'),
            title=_('Imported Successfully'))

    def run_single_record(self):
        self.ensure_one()
        data = self.env['ir.config_parameter'].sudo()
        email = data.get_param('google_sheet_data_import.email')
        p12_json_key = data.get_param('google_sheet_data_import.p12_json_key')

        document = self.open_document(email, p12_json_key)
        sheet = document.worksheet(self.document_sheet)
        header_row = 1
        row = [c or '' for c in sheet.row_values(header_row)]
        if not row:
            raise ValidationError(SHEET_APP, _(
                'Header cells seems empty!'))
        master_row_field = row[0]

        GoogleModel = self.env['ir.model'].search([
            ('model', '=', self.document_sheet)
        ], limit=1)
        if not GoogleModel:
            raise UserError(
                _("There is no model define as '%s'" % self.document_sheet))

        if not GoogleModel.change_data == True:
            raise UserError(
                _("You are not allowed to change data of '%s' model. Please contact your system Administrator" % self.document_sheet))

        list_of_lists = sheet.get_all_records()
        for i in list_of_lists:
            self.check_field_exits(i)
            self.import_data(i, master_row_field)
        return self.show_notification()

    @api.model
    def run(self):
        obj = self.env[self._name].search([])
        for rec in obj:
            rec.run_single_record()
        return True


class InheritIrModel(models.Model):
    _inherit = 'ir.model'

    change_data = fields.Boolean(
        string='Allow Change Data/Fields Through Google Sheet API')
