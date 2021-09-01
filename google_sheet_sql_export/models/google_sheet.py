import base64
import json
import gspread
import re
from tabulate import tabulate
import datetime
import pandas as pd
from httplib2 import ServerNotFoundError
from gspread import exceptions as GExcept
from gspread.exceptions import NoValidUrlKeyFound, SpreadsheetNotFound
from oauth2client.service_account import ServiceAccountCredentials
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import config

SHEET_APP = (
    "Google Spreadsheet Import Issue\n"
    "--------------------------------------------------"
)
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


class GoogleSpreadsheetIExport(models.Model):
    _name = "google.spreadsheet.export"
    _description = "Google Spreadsheet Export"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    PROHIBITED_WORDS = [
        "delete",
        "drop",
        "insert",
        "alter",
        "truncate",
        "execute",
        "create",
        "update",
        "ir_config_parameter",
    ]
    name = fields.Char("Name", required=True)
    worksheet_name = fields.Char("Worksheet Name")
    select = fields.Selection(
        string="Select",
        selection=[
            ("sheet", "Create Sheet"),
            ("worksheet", "Create Worksheet"),
            ("update", "Update Worksheet"),
        ],
        default="sheet",
    )
    document_url = fields.Char("Sheet URL")
    spreadsheet_name = fields.Char("Spreadsheet Name")
    query_write = fields.Text(
        "Query",
        help="You can't use the following words"
        ": DELETE, DROP, CREATE, INSERT, ALTER, TRUNCATE, EXECUTE, UPDATE.",
        track_visibility="always",
    )
    data = fields.Text("data")
    active = fields.Boolean("Active", default=True)

    def open_document(self, email, p12_json_key):
        # Auhentification
        self.ensure_one()

        try:
            p12_key_file_data = json.loads(base64.b64decode(p12_json_key))
        except:
            raise UserError(
                _(
                    "The Google private json key is might not added or improper. Please go to configuration and check properly."
                )
            )

        creds = ServiceAccountCredentials._from_parsed_json_keyfile(
            p12_key_file_data, SCOPE
        )

        try:
            gc = gspread.authorize(creds)
        except ServerNotFoundError:
            if config.get("debug_mode"):
                raise
            raise ValidationError(
                _(
                    SHEET_APP + "\nCheck your internet connection.\n"
                    "Impossible to establish a connection "
                    "with Google Services"
                )
            )
        try:
            document = gc.open_by_url(self.document_url)
        except NoValidUrlKeyFound:
            if config.get("debug_mode"):
                raise
            raise ValidationError(
                _(SHEET_APP + "\nGoogle Drive: No valid key found in URL")
            )
        except SpreadsheetNotFound:
            if config.get("debug_mode"):
                raise
            raise ValidationError(
                _(
                    SHEET_APP + "\nSpreadsheet Not Found"
                    "\n\nResolution\n----------------\n"
                    "Check URL file & sharing options with it "
                    "with this google user:\n\n%s" % email
                )
            )
        except Exception as e:
            if config.get("debug_mode"):
                raise
            raise ValidationError(_("Google Drive: %s" % e))
        return document

    def create_spreadsheet(self, email, p12_json_key):
        self.ensure_one()

        try:
            p12_key_file_data = json.loads(base64.b64decode(p12_json_key))
        except:
            raise UserError(
                _(
                    "The Google private json key is might not added or improper. Please go to configuration and check properly."
                )
            )

        creds = ServiceAccountCredentials._from_parsed_json_keyfile(
            p12_key_file_data, SCOPE
        )

        try:
            gc = gspread.authorize(creds)
        except ServerNotFoundError:
            if config.get("debug_mode"):
                raise
            raise ValidationError(
                _(
                    SHEET_APP + "\nCheck your internet connection.\n"
                    "Impossible to establish a connection "
                    "with Google Services"
                )
            )
        try:
            new_document = gc.create(self.spreadsheet_name)
            new_document.share(email, perm_type="user", role="writer")
        except GExcept.APIError as e:
            raise UserError(_("Google Sheet Error: \n%s" % e))
        except Exception as e:
            raise UserError(_("Error: \n%s" % e))

        return new_document

    def test_query_data(self):
        """Check if the query contains prohibited words, to avoid maliscious
        SQL requests"""
        self.ensure_one()
        query_write = self.query_write.strip()
        while query_write[-1] == ";":
            query_write = query_write[:-1]
        self.query_write = query_write

        query_write = self.query_write.lower()
        for word in self.PROHIBITED_WORDS:
            expr = r"\b%s\b" % word
            is_not_safe = re.search(expr, query_write)
            if is_not_safe:
                raise UserError(
                    _(
                        "The query is not allowed because it contains unsafe word"
                        " '%s'"
                    )
                    % (word)
                )
            else:
                self.env.cr.execute(str(self.query_write))
                get_new_record = self.env.cr.dictfetchall()

                for data in get_new_record:
                    for key, value in data.items():
                        if isinstance(value, datetime.datetime):
                            data.update(
                                {
                                    # key: pd.to_datetime(value),
                                    key: value.strftime("%Y-%m-%d %H:%M:%S.%f"),
                                }
                            )
                pd.set_option("display.max_columns", None)
                record = pd.DataFrame.from_records(get_new_record)
                record.fillna("", inplace=True)
                new_data = tabulate(record, headers="keys", tablefmt="psql")
                self.data = new_data

        return True

    def import_data(self, worksheet, document):
        for rec in self:
            rec.select = "update"
            rec.document_url = "https://docs.google.com/spreadsheets/d/%s" % document.id

        self.env.cr.execute(str(self.query_write))
        get_new_record = self.env.cr.dictfetchall()

        for data in get_new_record:
            for key, value in data.items():
                if isinstance(value, datetime.date):
                    data.update(
                        {
                            # key: pd.to_datetime(value),
                            key: value.strftime("%Y-%m-%d"),
                        }
                    )

        record = pd.DataFrame.from_dict(get_new_record)
        record.fillna("", inplace=True)

        try:
            worksheet.update([record.columns.values.tolist()] + record.values.tolist())
        except GExcept.APIError as e:
            raise UserError(_("Error: \n%s" % e))
        except:
            raise UserError(
                _(
                    "Something went wrong. Please try after some time or contact your System Administrator"
                )
            )

        return self.show_notification()

    def show_notification(self):
        notification = {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Exported Successfully"),
                "message": _("Odoo data is successfully exported to Google sheet."),
                "type": "success",  # types: success,warning,danger,info
                "sticky": False,  # True/False will display for few seconds if false
            },
        }
        return notification

    def run_single_sheet(self):
        self.ensure_one()

        data = self.env["ir.config_parameter"].sudo()
        email = data.get_param("google_sheet_sql_export.email")
        p12_json_key = data.get_param("google_sheet_sql_export.p12_json_key")

        if not self.select == "sheet":
            document = self.open_document(email, p12_json_key)
            if self.select == "worksheet":
                try:
                    worksheet = document.add_worksheet(
                        title=self.worksheet_name, rows="1000", cols="26"
                    )
                except Exception as e:
                    raise ValidationError(
                        _(
                            "Name Of This Worksheet Is Already Created In Sheet\n Please Create With Diffrent Name "
                        )
                    )
                return self.import_data(worksheet, document)
            else:
                try:
                    sheet = document.worksheet(self.worksheet_name)
                except Exception as e:
                    raise UserError(
                        _(
                            " There is no Worksheet Find in Your Spreadsheet \n Hint: please select proper worksheet name or Select 'Create worksheet' option in Select Field"
                        )
                    )
                return self.import_data(sheet, document)
        else:
            try:
                new_document = self.create_spreadsheet(email, p12_json_key)
                new_sheet = new_document.add_worksheet(
                    title=self.worksheet_name, rows="1000", cols="26"
                )
                worksheet = new_document.get_worksheet(0)
                delete_sheet = new_document.del_worksheet(worksheet)
                return self.import_data(new_sheet, new_document)
            except GExcept.APIError as e:
                raise UserError(_("Google Sheet Error: \n%s" % e))
            except Exception as e:
                raise UserError(_("Error: \n%s" % e))

        return True

    @api.model
    def run(self):
        obj = self.env[self._name].search([])
        for rec in obj:
            rec.run_single_sheet()
        return True
