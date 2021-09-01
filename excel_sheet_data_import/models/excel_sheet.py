import base64
import xlrd
import os
import io
from io import StringIO
from xlrd import open_workbook
import tempfile
import binascii
import csv
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

import logging
_logger = logging.getLogger(__name__)


TYPE_LISTS = ['integer', 'float', 'char',
    'text', 'date', 'datetime', 'boolean']

class ExcelSpreadsheetImport(models.Model):
    _name = 'excel.spreadsheet.import'
    _description = 'Excel Spreadsheet Import'

    name = fields.Char(
        'Name', help="Record name to just identify sheets", required=True)
    file_select = fields.Binary('Select File', required=True, attachment=True)
    file_fname = fields.Char(string='File name')
    document_sheet = fields.Char('Sheet Name', required=True)
    option = fields.Selection([
        ('csv', 'CSV'),
        ('excel', 'Excel')],
        string="Select Format", required=True, default="csv",
        help="""Selection of the file type is as follows
1) The csv file can have .csv as file extension,
2) The Excel option can have .xls or .xlsx
        """)
    domain_selection = fields.Selection([
        ('1', '1 Column'),
        ('2', '2 Column'),
        ('3', '3 Column'),
        ('4', '4 Column'),
        ('5', '5 Column')],
        string="domain selection", required=True, default="1")
    operation = fields.Selection([
        ('update', 'Create / Update'),
        ('create', 'Create Only')],
        string="Select Operation", required=True, default='update')

    def open_document(self):
        ExcelModel = self.env['ir.model'].search([
                    ('model', '=', self.document_sheet)
                    ], limit=1)

        if not ExcelModel:
            raise UserError(_("There is no model define as '%s'" % self.document_sheet))

        if not ExcelModel.change_data == True:
            raise UserError(_("You are not allowed to change data of '%s' model. Please contact your system Administrator" % self.document_sheet))

        if self.option == "csv" and self.file_select:
            filename,filetype = os.path.splitext(self.file_fname)
            if filetype == '.csv':
                file = base64.b64decode(self.file_select)
                data = io.StringIO(file.decode("utf-8"))
                data.seek(0)
                file_reader = []
                csv_reader = csv.reader(data,delimiter=',')
                row = [{k: v for k, v in row1.items()}
                    for row1 in csv.DictReader(data, skipinitialspace=True)]

                for i in row:
                    old_list = list(i.keys())
                    break

                if not row:
                    raise ValidationError(_(
                        'Header cells seems empty!'))
                
                master_row_field = old_list[0:int(self.domain_selection)]
            
                for i in row:
                    self.check_field_exits(i)
                    self.import_data(i, master_row_field)

                return True    
            else:
                raise UserError(_('Invalid file type!!!\n Select Proper File Format.'))

        elif self.option == "excel" and self.file_select:
            filename,filetype = os.path.splitext(self.file_fname)

            if filetype == '.xlsx' or filetype == '.xls':
                fp = tempfile.NamedTemporaryFile(delete= False, suffix=filetype)
                fp.write(binascii.a2b_base64(self.file_select))
                workbook = xlrd.open_workbook(fp.name)

                try:
                    sheet = workbook.sheet_by_name(self.document_sheet)
                except Exception as e:
                    raise UserError(_("There is no sheet name '%s' in File. Please check properly." %self.document_sheet))
                
                header_row = 0
                try:
                    row = [c or '' for c in sheet.row_values(header_row)]
                except Exception as e:
                    raise ValidationError(_(
                        'Header cells seems empty!'))

                master_row_field = row[0:int(self.domain_selection)]          
                

                first_row = [] 
                for col in range(sheet.ncols):
                    first_row.append(sheet.cell_value(0,col) )

                archive_lines = []
                for row in range(1, sheet.nrows):
                    elm = {}
                    for col in range(sheet.ncols):
                        elm[first_row[col]]=sheet.cell_value(row,col)
                    archive_lines.append(elm)

                for i in archive_lines:
                    self.check_field_exits(i)
                    self.import_data(i,master_row_field)

                return True
            else:
                raise UserError(_('Invalid File Type!!!\n Select Proper File Format.'))


    def show_notification(self):
        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Imported Successfully'),
                'message': _('Sheet data is successfully imported to Odoo.'),
                'type':'success',  #types: success,warning,danger,info
                'sticky': False,  #True/False will display for few seconds if false
            },
        }
        return notification

    def create_product_field(self, model, field):
        IrModelFields = self.env['ir.model.fields']
        field_list = field.split(':')
        if not field_list:
            raise UserError(_("Sheet Header is not define."))

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

        IrExcelDefineModel = IrModel.search([
            ('model', '=', self.document_sheet)
        ], limit=1)
        vals = {}
        new_list = []
        if IrExcelDefineModel:
            sheetModel = self.env[self.document_sheet]
            for d in data:

                field_list = d.split(':')
                if field_list:
                    field_name = field_list[0]
                    ls = [r.startswith(field_name) for r in master_row_field]
                    if any(ls):
                        new_list.append((field_name,'=',data[d]))

                    product_find_field = IrModelFields.search([
                        ('model_id', '=', IrExcelDefineModel.id),
                        ('name', '=', field_name)
                    ])
                    if product_find_field and isinstance(product_find_field.ttype, type(data[d])):
                        vals.update({
                            field_name: data[d],
                        })
                        if product_find_field.ttype == 'date': 
                            vals.update({
                                field_name: data[d].replace('/','-'),
                            })
                        if product_find_field.ttype == 'datetime': 
                            vals.update({
                                field_name: data[d].replace('/','-'),
                            })
                        elif product_find_field.ttype == 'many2one':
                            
                            rec = IrModel.search([
                                ('model','=',product_find_field.relation)
                            ])
                            new_product_find_field =self.env[rec.model].search([
                                    ('name', '=',data[d])
                            ])                               
                            vals.update({
                                field_name: new_product_find_field.id,
                            })                                
                    else:
                        vals.update({
                            field_name: data[d],
                        })

            prod_obj = None
            prod_obj = sheetModel.search(new_list)
            if self.operation == 'update':
                if prod_obj:
                    try:
                        prod_obj.write(vals)
                    except Exception as e:
                        _logger.info(_("Can not write Value of this Data: %s\n Route: %s" %(vals, e)))
                        raise UserError(_("Error while import data \n %s\n\n Hint: Please check field name and it's TYPE if you create new."%e))                
                else:
                    try:
                        sheetModel.create(vals)
                    except Exception as e:
                        _logger.info(_("Can not create Value of this Data: %s\n Route: %s" %(vals, e)))
                        raise UserError(_("Error while import data \n %s\n\n Hint: Please check field name and it's TYPE if you create new."%e))
            else:
                if not prod_obj:
                    try:
                        sheetModel.create(vals)
                    except Exception as e:
                        _logger.info(_("Can not create Value of this Data: %s\n Route: %s" %(vals, e)))
                        raise UserError(_("Error while import data \n %s\n\n Hint: Please check field name and it's TYPE if you create new."%e))
                else:
                    pass

        return True
           

    def run_single_record(self):
        self.ensure_one()
        self.open_document()
        return self.show_notification()
