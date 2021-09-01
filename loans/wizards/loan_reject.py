from odoo import api, fields, models, _


class LoanRejectReason(models.TransientModel):
    _name = 'loan.request.reject'
    _description = 'Loan Request Reject'


    reject_reason = fields.Char(string="Reason",required=True)

    def action_reject_reason_apply(self):
        reject = self.env['loan.request'].browse(self._context.get('active_ids'))
        for rec in reject:
            rec.status = self.reject_reason
            rec.states = 'reject'