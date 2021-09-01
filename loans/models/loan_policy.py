from odoo import api, fields, models, _
from odoo.exceptions import UserError


class LoanPolicy(models.Model):
    _name = 'loan.policy'
    _description = 'Loan Policies'
    _rec_name = 'policy_name'

    policy_name = fields.Char(string="Name", required=True)
    policy_code = fields.Char(string="Code", required=True)
    policy_type = fields.Selection([('max_amount', 'Max Loan Amount'), (
        'gap', 'Gap Between Two Loan')], string='Policy Type', required=True)
    policy_basis = fields.Selection(
        [('fix_amount', 'Fix Amount')], string='Basis')
    policy_value = fields.Integer(string='Value')
    company_name = fields.Char(
        string="Company", readonly=True, default="Veracious Perfect Cs Pvt. Ltd.")
    loan_type = fields.Many2one(
        'loan.types', string="Loan type", required=True)
