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


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.depends("create_date")
    def _compute_channel_names(self):
        for record in self:
            res_id = record.id
            record.notify_info_channel_name = "notify_info_%s" % res_id

    notify_info_channel_name = fields.Char(compute="_compute_channel_names")

    def notify_info(self, message="Default message", title=None, sticky=False):
        title = title or _("Information")
        self._notify_channel("info", message, title, sticky)

    def _notify_channel(
        self,
        type_message="default",
        message="Default message",
        title=None,
        sticky=False,
    ):
        # pylint: disable=protected-access
        if not self.env.user._is_admin() and any(
            user.id != self.env.uid for user in self
        ):
            raise exceptions.UserError(
                _("Sending a notification to another user is forbidden.")
            )
        channel_name_field = "notify_{}_channel_name".format(type_message)
        bus_message = {
            "type": type_message,
            "message": message,
            "title": title,
            "sticky": sticky,
        }
        notifications = [
            (record[channel_name_field], bus_message) for record in self
        ]
        self.env["bus.bus"].sendmany(notifications)
