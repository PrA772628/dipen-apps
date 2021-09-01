
from odoo import fields, http, _
from odoo.http import request , route
from odoo.addons.portal.controllers.portal import CustomerPortal

class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        record = request.env['res.partner.bank'].sudo().search([('partner_id','=',partner.id)])

        bank_detail_count = len(record)
        
        values.update({
            'bank_count': bank_detail_count,
        })
        return values

    @http.route(['/my/bank_details'], type='http', auth='user', website=True)
    def CustomerBankForm(self,**kw):
        partner = request.env.user.partner_id
        record = request.env['res.partner.bank'].sudo().search([('partner_id','=',partner.id)])
        return http.request.render("bank_detail.portal_my_bank",{
            'records' : record
        })

    @http.route(['/my/detail/<int:record_id>'], type='http', auth='user', website=True)
    def OpenBankDetail(self,record_id,**kw):
        partner = request.env.user.partner_id

        record = request.env['res.partner.bank'].sudo().search([('id','=',record_id)])

        bank = request.env['res.bank'].sudo().search([])

        return http.request.render("bank_detail.portal_my_Bank_detail",{'record':record,'banks':bank})

    @http.route(['/my/updatedetail'], type='http', auth='user', website=True)
    def UpdateBankDetail(self,**kw):
        partner = request.env.user.partner_id
        record = request.env['res.partner.bank'].sudo().search([('id','=',kw['record_id'])])
        if kw and request.httprequest.method == 'POST':
            record.sudo().write({
                'acc_number':kw['acc_number'],
                'bank_id':kw['bank_id'],
            })

            return request.redirect('/my/bank_details')
