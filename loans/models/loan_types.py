from odoo import api, fields, models, _
from odoo.exceptions import UserError


class LoanTypes(models.Model):
    _name = 'loan.types'
    _description = 'Loan Types'
    _rec_name = 'loan_name'

    loan_name = fields.Char(string="Name", required=True)
    loan_code = fields.Char(string="Code", required=True)
    is_interest = fields.Boolean(string="Is Interest Payable", default=True)
    loan_interest_mode = fields.Selection(
        [('reducing', 'Reducing'), ('flat', 'Flat')], required=True, default='flat')
    loan_rate = fields.Integer(string='Rate', required=True)
    loan_interest_account = fields.Many2one(
        'res.bank', string='Interest Account', required=True, default=4)
    loan_repayment = fields.Selection(
        [('', ''), ('cash', 'Direct Cash/Check')], string="Repayment Method")
    loan_disburse = fields.Selection(
        [('', ''), ('cash', 'Direct Cash/Check')], string="Disburse Method")
    company_name = fields.Char(
        string="Company", readonly=True, default="Veracious Perfect Cs Pvt. Ltd.")
    loan_proofs_id = fields.Many2many('loan.proof')

    @api.constrains('loan_repayment')
    def check_repayment(self):
        for obj in self:
            if not obj.loan_repayment:
                raise UserError('Please Enter Repayment Method')

    @api.constrains('loan_disburse')
    def check_repayment(self):
        for obj in self:
            if not obj.loan_disburse:
                raise UserError('Please Enter Disburse Method')
