
from odoo import fields, http, _
from odoo.http import request, route
from odoo.addons.web.controllers.main import Home


class FileUploadPortal(Home):

    @http.route(['/file/upload'], type='http', auth='user', website=True)
    def FileUploadForm(self, **kw):
        data = request.env['ir.config_parameter'].sudo()
        drive_api_key = data.get_param('file_picker.drive_api_key')
        drive_client_id = data.get_param('file_picker.drive_client_id')
        project_id = data.get_param('file_picker.project_id')
        dropbox_api_key = data.get_param('file_picker.dropbox_api_key')
        onedrive_app_id = data.get_param('file_picker.onedrive_app_id')
        
        return http.request.render("file_picker.home_file_picker",{'drive_api_key': drive_api_key, 'drive_client_id': drive_client_id,
                'project_id': project_id, 'dropbox_api_key': dropbox_api_key, 'onedrive_app_id': onedrive_app_id})

    # @http.route(['/my/detail/<int:record_id>'], type='http', auth='user', website=True)
    # def OpenBankDetail(self,record_id,**kw):
    #     partner = request.env.user.partner_id

    #     record = request.env['res.partner.bank'].sudo().search([('id','=',record_id)])

    #     bank = request.env['res.bank'].sudo().search([])

    #     return http.request.render("bank_detail.portal_my_Bank_detail",{'record':record,'banks':bank})

    # @http.route(['/my/updatedetail'], type='http', auth='user', website=True)
    # def UpdateBankDetail(self,**kw):
    #     partner = request.env.user.partner_id
    #     record = request.env['res.partner.bank'].sudo().search([('id','=',kw['record_id'])])
    #     if kw and request.httprequest.method == 'POST':
    #         record.sudo().write({
    #             'acc_number':kw['acc_number'],
    #             'bank_id':kw['bank_id'],
    #         })

    #         return request.redirect('/my/bank_details')
