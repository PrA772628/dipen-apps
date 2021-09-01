import base64
import json
import gspread
import datetime
from datetime import date
import pandas as pd
from httplib2 import ServerNotFoundError
from gspread import exceptions as GExcept 
from gspread.exceptions import NoValidUrlKeyFound, SpreadsheetNotFound
from oauth2client.service_account import ServiceAccountCredentials
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import config
from odoo.tools.safe_eval import safe_eval

SHEET_APP = ("Google Spreadsheet Import Issue\n"
             "--------------------------------------------------")
SCOPE = ['https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive']


class GoogleSpreadsheetFieldIExport(models.Model):
    _name = 'gsheet.ir.model.field'
    _description = 'Google Spreadsheet ir Fields'
    _order = 'sequence'

    sequence = fields.Integer("Sequence")
    g_id = fields.Many2one("google.spreadsheet.export")
    ir_model_id = fields.Selection(related="g_id.ir_model_id",string="Model Name",required=True)
    ir_model_field = fields.Many2one('ir.model.fields',
        string='Field Name',
        domain="[('model_id','=',ir_model_id), ('ttype', 'in', ['boolean', 'char', 'date', 'datetime', 'float', 'html', 'integer', 'many2one', 'monetary', 'selection', 'text'])]",
        required=True,
        ondelete = 'cascade')


class GoogleSpreadsheetIExport(models.Model):
    _name = 'google.spreadsheet.export'
    _description = 'Google Spreadsheet Export'

    name = fields.Char('Name', required=True)
    ir_model_id = fields.Selection(selection='_list_all_models',string="Model Name",required=True)
    ir_model_fields = fields.One2many('gsheet.ir.model.field', 'g_id', string="Fields")
    domain = fields.Text(default='[]',required=True)
    worksheet_name = fields.Char('Worksheet Name')
    select = fields.Selection(string='Select', selection=[
        ('sheet', 'Create Sheet'), 
        ('worksheet', 'Create Worksheet'),
        ('update','Update Worksheet')], default="sheet")
    document_url = fields.Char('Sheet URL')
    spreadsheet_name = fields.Char('Spreadsheet Name')

    @api.onchange('ir_model_id')
    def _onchange_ir_model_id(self):
        self.ir_model_fields = [(6,0,[])]


    @api.model
    def _list_all_models(self):
        self._cr.execute("SELECT model, name FROM ir_model WHERE change_data = 't' ORDER BY name")
        return self._cr.fetchall()

    def open_document(self,email,p12_json_key):
        # Auhentification
        self.ensure_one()

        try:
            p12_key_file_data = json.loads(base64.b64decode(p12_json_key))
        except:
            raise UserError(_("The Google private json key is might not added or improper. Please go to configuration and check properly."))
 
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
            raise ValidationError(_("Google Drive: %s" % e))
        return document
    
    def create_spreadsheet(self,email,p12_json_key):
        self.ensure_one()

        try:
            p12_key_file_data = json.loads(base64.b64decode(p12_json_key))
        except:
            raise UserError(_("The Google private json key is might not added or improper. Please go to configuration and check properly."))
 
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
            new_document = gc.create(self.spreadsheet_name)
            new_document.share(email, perm_type='user', role='writer')
        except GExcept.APIError as e:
            raise UserError(_("Google Sheet Error: \n%s" %e))
        except Exception as e:
            raise UserError(_("Error: \n%s" %e))

        return new_document
        
    def import_data(self,worksheet,document):
        for rec in self:
            rec.select = 'update'
            rec.document_url = "https://docs.google.com/spreadsheets/d/%s" % document.id

        IrModel = self.env['ir.model']
     
        IrGoogleDefineModel = IrModel.search([
            ('model', '=', self.ir_model_id)
        ], limit=1)

        domain = safe_eval(self.domain)
        field_list = []

        for field in self.ir_model_fields:
            field_list.append(field.ir_model_field.name)
        old_record = worksheet.get_all_records()

        get_record = self.env[IrGoogleDefineModel.model].search_read(domain)
        get_new_record = list(map(lambda data: {key:value for key, value in data.items() if key in field_list}, get_record))

        for data in get_new_record:
            for key,value in data.items():
                if type(value) == tuple:
                    data.update({
                        key : value[1]
                    })
                elif type(value) == datetime.datetime:
                    data.update({
                        key : str(value)
                    })


        old_records1 = []
        first_field = self.ir_model_fields and self.ir_model_fields[0].ir_model_field.name or False
        new_record_all_vals = [first_field and r.get(first_field) or list(r.values())[0] for r in get_new_record]

        for o_data in old_record:
            if list(o_data.values())[0] not in new_record_all_vals:
                old_records1.append(o_data)


        merge_record = old_records1 + get_new_record
        final_record = []
        for data in merge_record:
            rec = {}
            rec.clear()
            k = list(data.keys())
            v = list(data.values())
            for key in field_list:
                db = k.index(key)
                rec.update({k[db]:v[db]})
            final_record.append(rec)

        for data in final_record:
            for key,value in data.items():
                if isinstance(value,datetime.date):
                    data.update({
                        key : pd.to_datetime(value),
                        key : value.strftime("%Y-%m-%d %H:%M:%S.%f")
                    })

        record = pd.DataFrame.from_dict(final_record)

        try:
            worksheet.update([record.columns.values.tolist()]+record.values.tolist(),value_input_option='USER_ENTERED')
        except GExcept.APIError as e:
            raise UserError(_("Error: \n%s" %e))
        except:
            raise UserError(_("Something went wrong. Please try after some time or contact your System Administrator"))

        return self.show_notification()
    
    def show_notification(self):
        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Exported Successfully'),
                'message': _('Odoo data is successfully exported to Google sheet.'),
                'type':'success',  #types: success,warning,danger,info
                'sticky': False,  #True/False will display for few seconds if false
            },
        }
        return notification

    def run_single_sheet(self):
        self.ensure_one()

        data = self.env['ir.config_parameter'].sudo()
        email = data.get_param('google_sheet_data_import.email')
        p12_json_key = data.get_param('google_sheet_data_import.p12_json_key')

        if not self.select == 'sheet':
            document = self.open_document(email,p12_json_key)
            if self.select == 'worksheet':
                try:
                    worksheet = document.add_worksheet(title=self.worksheet_name, rows="1000", cols="26")
                except Exception as e:
                    raise ValidationError(_("Name Of This Worksheet Is Already Created In Sheet\n Please Create With Diffrent Name "))
                return self.import_data(worksheet,document)
            else:
                try:
                    sheet = document.worksheet(self.worksheet_name)
                except Exception as e:
                    raise UserError(_(" There is no Worksheet Find in Your Spreadsheet \n Hint: please select proper worksheet name or Select 'Create worksheet' option in Select Field"))

                return self.import_data(sheet,document)
        else:
            try:
                new_document = self.create_spreadsheet(email,p12_json_key)
                new_sheet = new_document.add_worksheet(title=self.worksheet_name,rows='1000',cols='26')
                worksheet = new_document.get_worksheet(0)
                delete_sheet = new_document.del_worksheet(worksheet)
                return self.import_data(new_sheet,new_document)
            except GExcept.APIError as e:
                raise UserError(_("Google Sheet Error: \n%s" %e))
            except Exception as e:
                raise UserError(_("Error: \n%s" %e))

        return True

    @api.model
    def run(self):
        obj = self.env[self._name].search([])
        for rec in obj:
            rec.run_single_sheet()
        return True
