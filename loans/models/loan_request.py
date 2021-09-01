from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

class AccountMoveInherit(models.Model):
    _inherit='account.move'

    @api.onchange('invoice_line_ids')
    def _onchange_invoice_line_ids(self):
        return print('------------------------call Successful')

    @api.onchange('line_ids', 'invoice_payment_term_id', 'invoice_date_due', 'invoice_cash_rounding_id', 'invoice_vendor_bill_id')
    def _onchange_recompute_dynamic_lines(self):
        print('-------------------------------I Am Here')
class LoanRequest(models.Model):
    _name = 'loan.request'
    _rec_name = 'name_seq'

    customer_id = fields.Many2one(
        'res.partner', string='Partner')
    apply_date = fields.Date(
        string="Applied Date", required=True)
    loan_type = fields.Many2one(
        'loan.types', string='Loan Type', required=True)
    loan_partner_type = fields.Selection(selection=[(
        'customer', 'Customer'), ('employee', 'Employee')], string="Partner Type", default='customer')
    company_name = fields.Char(
        string="Company", readonly=True, default="Veracious Perfect Cs Pvt. Ltd.")
    loan_amount = fields.Integer(string='Loan Amount', required=True)
    loan_term = fields.Integer(string="Duration(Month)", required=True)
    interest_rate = fields.Integer(
        string="Interest Rate", related='loan_type.loan_rate', readonly=True)
    interest_mode = fields.Selection(
        string="Interest Mode", related='loan_type.loan_interest_mode', readonly=True)
    interest_amount = fields.Integer(
        string="Interest Amount", compute='check_interest', readonly=True)
    total_amount = fields.Integer(
        string="Total Loan Amount", compute='check_total_amount', readonly=True)
    paid_amount = fields.Integer(string="Paid Amount", readonly=True)
    name_seq = fields.Char(string='Loan Request', required=True, copy=False, readonly=True,
                           index=True, default=lambda self: _('New'), track_visibility="always")
    approve_date = fields.Char(string="Approved date", readonly=True)
    installment_type = fields.Char(
        string="Installment Type", readonly=True, default="Month")
    image1 = fields.Binary(string='Aadhar Card')
    image2 = fields.Binary(string='Pan Card')
    image3 = fields.Binary(string='Election Card')
    image4 = fields.Binary(string='Light Bill')
    image5 = fields.Binary(string='Tax Bill')
    image6 = fields.Binary(string='Birth Certificate')
    installment_lines = fields.One2many(
        comodel_name='loan.installment.detail', inverse_name='loan_request_id', readonly=True)
    states = fields.Selection([('draft', 'Draft'), ('submit', 'Submit Request'), (
        'department', 'Department Approval'), ('hr', 'HR Approval'), ('done', 'Done'), ('reject', 'Reject')], string="State", readonly=True, default='draft')
    user_id = fields.Integer(string="User", readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee")
    department_id = fields.Many2one(
        'hr.department', related="employee_id.department_id", string='Department')
    department_manager_id = fields.Many2one(
        'hr.employee', related='employee_id.parent_id', string='Department_manager')
    job_position = fields.Char(
        string="Job Position", related='employee_id.job_title')
    status = fields.Char(string="Status", readonly=True)
    disburse_date = fields.Date(string="Disburse Date")
    loan_disburse_date = fields.Char(
        string="Loan Disburse Date", readonly=True)
    # loan_end_date = fields.Char(string="Loan End Date", readonly=True)
    req_proof = fields.Many2many(
        'loan.proof', related='loan_type.loan_proofs_id', string="Required Proof", readonly=True)
    disburse_journal_id = fields.Many2one(
        'account.journal', string="Disburse Journal")
    default_disburse_acnt = fields.Many2one(
        'account.account', related="disburse_journal_id.default_account_id", string="Disburse Account")
    loan_repayment_id = fields.Many2one(
        'account.journal', string="Loan Repayment Journal")
    borrower_account = fields.Many2one(
        'account.account', string="Borrower loan Account")
    interest_journal_id = fields.Many2one(
        'account.journal', string="Interest Journal")
    interest_account = fields.Many2one(
        'account.account', related="interest_journal_id.default_account_id", string="Interest Account")
    interest_receivable_account = fields.Many2one(
        'account.account', srting="Interest Receivable account")

    def action_disburse_loan(self):
        for rec1 in self:
            loan = self.disburse_date
            rec1.loan_disburse_date = loan.strftime('%d-%m-%Y')
            rec1.states = 'done'
            rec1.status = 'Congrats!! Your Loan Amount is Disburse in your Account. Thank You....'

        list_of_ids = []
        account_invoice_obj = self.env['account.move']
        bank_journal = self.env['account.journal'].search(
            [('type', '=', 'purchase')], limit=1)
        invoice_vals = {
            'move_type': 'out_invoice',
            'ref': False,
            'journal_id': self.disburse_journal_id.id,
            'partner_id': self.customer_id.id or False,
            # 'invoice_date': date.today(),
            'payment_reference': self.name_seq,
        }

        res = account_invoice_obj.create(invoice_vals)

        # invoice_line_vals = {
        #     # 'product_id':product,
        #     'name': "Loan Amount" or '',
        #     'price_unit': self.loan_amount,
        #     'quantity': 1,
        #     # 'tax_ids': tax,
        # }

        # res1 = res.write({'invoice_line_ids': [(0, 0, invoice_line_vals)]})
        ls = []
        for obj in range(1, self.loan_term+1):
            after_date = self.disburse_date + relativedelta(months=obj)
            date = after_date.strftime('%Y-%m-%d')
            data = {}
            data['account_id'] = self.interest_receivable_account.id
            data['name'] = self.customer_id.name
            after_date = self.disburse_date + relativedelta(months=obj)
            date = after_date.strftime('%Y-%m-%d')
            data['date_maturity'] = date
            # data['debit'] = self.loan_amount/self.loan_term
            ls.append(data)
            # res.write({'line_ids': [(0, 0, data)]})
        print('-----------------------', ls)
        data1 = {
            'account_id': self.default_disburse_acnt.id,
            'name': self.customer_id.name,
            # 'credit': self.loan_amount,
        }
        print('--------------------------', data1)
        res2 = res.write({'line_ids': [(0, 0,i)for i in ls]})
        print('----------------------------',res2)
        # res.write({'invoice_line_ids':[(5,0,0)]})
        res3 = res.write({'line_ids': [(0, 0, data1)]})

        list_of_ids.append(res.id)

        if list_of_ids:
            imd = self.env['ir.model.data']
            action = imd.xmlid_to_object(
                'account.action_move_out_invoice_type')
            list_view_id = imd.xmlid_to_res_id('account.view_invoice_tree')
            form_view_id = imd.xmlid_to_res_id('account.view_move_form')
            result = {
                'name': action.name,
                'help': action.help,
                'type': action.type,
                'views': [[list_view_id, 'tree'], [form_view_id, 'form']],
                'target': action.target,
                'context': action.context,
                'res_model': action.res_model,
            }
            if list_of_ids:
                result['domain'] = "[('id','=',%s)]" % list_of_ids

            return result

    @api.model
    def default_get(self, fields):
        vals = super(LoanRequest, self).default_get(fields)
        vals['user_id'] = self.env.user.id
        return vals

    def action_submit(self):
        for rec in self:
            rec.states = 'submit'
            rec.status = """Your Loan Request is Submitted.
                            Wait for Department Review.
                            Thank You..."""
            if not rec.image1:
                raise UserError(_("Please Enter Required Document"))

    def action_approve_request(self):
        for rec in self:
            rec.states = 'department'
        self.write(
            {'status': "Your Loan Request Approve BY Department Manager. Wait For Hr Review. Thank You..."})

    def action_hr_approve_request(self):
        for rec in self:
            rec.states = 'hr'
            a_date = datetime.today()
            rec.approve_date = a_date.date().strftime('%d-%m-%Y')
        self.write(
            {'status': "Congratulations!! Your Loan Request Approve BY Hr Manager.In Few Hour You Receive your Loan Details.Thank You..."})

    def action_compute_installment(self):
        for rec1 in self.installment_lines:
            self.write({'installment_lines': [(2, rec1.id)]})
        data = {}
        for rec in self:
            if rec.loan_term:
                for obj in range(1, rec.loan_term+1):
                    before_date = self.disburse_date + \
                        relativedelta(months=obj-1)
                    date1 = before_date.strftime('%d-%m-%Y')
                    data['from_date'] = date1
                    after_date = self.disburse_date + relativedelta(months=obj)
                    date = after_date.strftime('%d-%m-%Y')
                    data['to_date'] = date
                    data['principal_amount'] = rec.loan_amount
                    data['installment_amount'] = rec.loan_amount/rec.loan_term
                    data['installment_interest_amount'] = rec.interest_amount/rec.loan_term
                    data['emi_amount'] = (
                        rec.loan_amount/rec.loan_term)+(rec.interest_amount/rec.loan_term)
                    self.write({'installment_lines': [(0, 0, data)]})

    @api.model
    def create(self, vals):
        if vals.get('name_seq', _('New')) == _('New'):
            vals['name_seq'] = self.env['ir.sequence'].next_by_code(
                'loan.request.sequence')
        result = super(LoanRequest, self).create(vals)
        return result

    @api.onchange('loan_amount', 'loan_term', 'interest_rate')
    def check_interest(self):
        for rec in self:
            if rec.loan_amount:
                if rec.loan_term:
                    if rec.interest_rate:
                        interest = (rec.loan_amount * rec.interest_rate)/100
                        # print('----------------------------', interest)
                        rec.interest_amount = interest

    @api.onchange('loan_amount', 'interest_amount')
    def check_total_amount(self):
        for obj in self:
            if obj.loan_amount and obj.interest_amount:
                amount = obj.loan_amount + obj.interest_amount
                obj.total_amount = amount

    # @api.onchange('loan_type', 'loan_policy_id')
    # def check_policy_name(self):
    #     if self.loan_policy_id.loan_type.id == self.loan_type:
    #         self.req_policy_name = self.loan_policy_id.policy_name


class LoanInstallmentDetail(models.Model):
    _name = 'loan.installment.detail'
    _rec_name = 'loan_seq'

    loan_request_id = fields.Many2one('loan.request', string="Loan Request Id")
    loan_seq = fields.Char(
        related='loan_request_id.name_seq', string="Loan Number")
    installment_seq = fields.Char(string='Installment Number', required=True, copy=False, readonly=True,
                                  index=True, default=lambda self: _('New'), track_visibility="always")
    to_date = fields.Char(string="To Date")
    from_date = fields.Char(string="From Date")
    principal_amount = fields.Float(string="Principle Amount")
    installment_amount = fields.Float(string="Installment Amount")
    installment_interest_amount = fields.Float(string="Interest Amount")
    emi_amount = fields.Float(string="EMI")
    state = fields.Selection(
        [('unpaid', 'Unpaid'), ('confirm', 'Confirm'), ('paid', 'Paid')], string="State", readonly=True, default='unpaid')
    customer_id = fields.Integer(related="loan_request_id.user_id")
    partner_name = fields.Many2one(
        'res.partner', related="loan_request_id.customer_id", readonly=True)
    loan_type = fields.Many2one(
        'loan.types', related="loan_request_id.loan_type", readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('installment_seq', _('New')) == _('New'):
            vals['installment_seq'] = self.env['ir.sequence'].next_by_code(
                'loan.installment.sequence')
        result = super(LoanInstallmentDetail, self).create(vals)
        return result

    def action_installment_pay(self):
        for rec in self:
            rec.state = 'paid'

        ls = []
        list_of_ids = []
        account_invoice_obj = self.env['account.move']
        bank_journal = self.env['account.journal'].search(
            [('type', '=', 'sale')], limit=1)
        tax = self.env['account.tax'].search([('id', '=', '3')], limit=1)
        product = self.env['product.product'].search([('id', '=', '39')])
        invoice_vals = {
            'move_type': 'out_invoice',
            'ref': False,
            'journal_id': self.loan_request_id.loan_repayment_id.id,
            'partner_id': self.partner_name.id or False,
            'invoice_date': date.today(),
            'payment_reference': self.loan_seq,
        }

        res = account_invoice_obj.create(invoice_vals)
        invoice_line_vals = {
            # 'product_id':product,
            'name': "Installment Amount" or '',
            'price_unit': self.installment_amount,
            'quantity': 1,
            'tax_ids': tax,
        }

        res1 = res.write(
            {'invoice_line_ids': ([(0, 0, invoice_line_vals)])})

        list_of_ids.append(res.id)

        if list_of_ids:
            imd = self.env['ir.model.data']
            action = imd.xmlid_to_object(
                'account.action_move_out_invoice_type')
            list_view_id = imd.xmlid_to_res_id('account.view_invoice_tree')
            form_view_id = imd.xmlid_to_res_id('account.view_move_form')
            result = {
                'name': action.name,
                'help': action.help,
                'type': action.type,
                'views': [[list_view_id, 'tree'], [form_view_id, 'form']],
                'target': action.target,
                'context': action.context,
                'res_model': action.res_model,

            }
            if list_of_ids:
                result['domain'] = "[('id','=',%s)]" % list_of_ids

            return result

    def action_installment_confirm(self):
        for obj1 in self:
            obj1.state = 'confirm'
