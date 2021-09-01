from odoo import api, fields, models, _
from odoo.exceptions import UserError


class LoanProof(models.Model):
    _name = 'loan.proof'
    _description = 'Loan Proofs'
    _rec_name = 'proof_name'

    proof_name = fields.Char(string="Proof Name", required=True)
    mandatory = fields.Boolean(string="Mandatory")
