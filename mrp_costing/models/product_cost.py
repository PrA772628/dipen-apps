
from logging import exception
from odoo import fields, models, _, api
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

class MrpProductionInherit(models.Model):
    _inherit = 'mrp.production'

    material_detail = fields.One2many(
        comodel_name='material.cost.detail', inverse_name='mrp_id')
    labour_cost_detail = fields.One2many(
        comodel_name='labour.cost.detail', inverse_name='mrp_id')
    cost_status = fields.Float(
        string="Work in Progress Cost", compute='_used_cost')
    overhead_cost = fields.Float('Overhead Cost')

    @api.model
    def create(self, values):
        res = super(MrpProductionInherit, self).create(values)
        data = {}
        for i in res.move_raw_ids:
            data['product_id'] = i.product_id.id
            data['quantity'] = i.product_uom_qty
            data['material_cost'] = (
                i.product_id.standard_price*i.product_uom_qty)
            res.write({'material_detail': [(0, 0, data)]})
        return res

    def material_cost_action(self):

        return {
            'name': 'Material Cost',
            'domain': [('mrp_id', '=', self.id)],
            'res_model': 'material.cost.detail',
            'view_id': False,
            'view_mode': 'tree',
            'type': 'ir.actions.act_window',
        }

    def labour_cost_action(self):
        data = self.env['labour.cost'].search(
            [('product_id', '=', self.product_id.id)])
        for i in data:
            if i.cost_type == 'standard':
                return {
                    'name': 'Labour Cost',
                    'domain': [('mrp_id', '=', self.id)],
                    'res_model': 'labour.cost.detail',
                    'view_id': False,
                    'view_mode': 'tree,form',
                    'type': 'ir.actions.act_window',
                }
            else:
                return {
                    'name': 'Labour Cost',
                    'domain': [('product_id', '=', self.product_id.id)],
                    'res_model': 'labour.cost',
                    'view_id': False,
                    'view_mode': 'tree,form',
                    'type': 'ir.actions.act_window',
                }

    def overhead_cost_action(self):

        return {
            'name': 'Overhead Cost',
            'domain': [('workcenter_id', '=', self.workorder_ids.workcenter_id.id)],
            'res_model': 'overhead.cost.detail',
            'view_id': False,
            'view_mode': 'tree',
            'type': 'ir.actions.act_window',
        }

    def journal_entry_action(self):
        AccountMove = self.env['account.move'].search([('mo_reference', '=', self.id)])
        entry_list = [x.id for x in AccountMove]
        return {
            'name': 'Account Move Line',
            'domain': [('move_id','in',entry_list)],
            'res_model': 'account.move.line',
            'view_id': False,
            'view_mode': 'tree',
            'type': 'ir.actions.act_window',
        }

    def _used_cost(self):
        labour_data = self.env['labour.cost'].search(
            [('product_id', '=', self.product_id.id)])
        overhead_data = self.env['overhead.cost.detail'].search(
            [('workcenter_id', '=', self.workorder_ids.workcenter_id.id)])
        for rec in self:
            if rec.state in ('draft', 'confirmed', 'progress'):
                rec.cost_status = sum(
                    rec.material_detail.mapped('material_cost'))
            else:
                for i in labour_data:
                    if i.cost_type == 'average':
                        rec.cost_status = (sum(rec.material_detail.mapped(
                            'material_cost'))+i.average_cost+sum(overhead_data.mapped('overhead_cost')))*self.product_qty
                        rec.overhead_cost = sum(
                            overhead_data.mapped('overhead_cost'))
                    else:
                        rec.cost_status = (sum(rec.material_detail.mapped('material_cost'))+sum(
                            rec.labour_cost_detail.mapped('labour_cost'))+sum(overhead_data.mapped('overhead_cost')))*self.product_qty
                        rec.overhead_cost = sum(
                            overhead_data.mapped('overhead_cost'))

    def button_mark_done(self):
        res = super(MrpProductionInherit, self).button_mark_done()
        labour_data = self.env['labour.cost'].search(
            [('product_id', '=', self.product_id.id)])
        overhead_data = self.env['overhead.cost.detail'].search(
            [('workcenter_id', '=', self.workorder_ids.workcenter_id.id)])

        for rec in labour_data:
            if rec.cost_type == 'standard':
                for i in self.workorder_ids:
                    for j in i.time_ids:
                        new_data = {
                            'employee_id': j.user_id.employee_id.id,
                            'workorder_id': i.id,
                            'duration': j.duration,
                            'product_id': self.product_id.id,
                            'quantity': self.product_qty,
                            'labour_cost': (j.user_id.employee_id.timesheet_cost*i.duration)/60,
                        }
                        self.write({'labour_cost_detail': [(0, 0, new_data)]})
                        debit_value = self.company_id.currency_id.round((j.user_id.employee_id.timesheet_cost*i.duration)/60)
                        credit_value = debit_value
                        debit_line_vals = {
                            'name': self.name,
                            'ref': '%s - Direct Labour'%self.name,
                            'debit': debit_value if debit_value > 0 else 0,
                            'credit': -debit_value if debit_value < 0 else 0,
                            'account_id': rec.labour_output_account.id,
                        }

                        credit_line_vals = {
                            'name': self.name,
                            'ref': '%s - Direct Labour'%self.name,
                            'credit': credit_value if credit_value > 0 else 0,
                            'debit': -credit_value if credit_value < 0 else 0,
                            'account_id': rec.labour_valuation_account.id,
                        }
                        rslt = {'credit_line_vals': credit_line_vals,
                                'debit_line_vals': debit_line_vals}

                        move_lines = [(0, 0, line)for line in rslt.values()]

                        AccountMove = self.env['account.move'].with_context(
                            default_journal_id=rec.labour_journal.id)

                        date = self._context.get(
                            'force_period_date', fields.Date.context_today(self))

                        new_account_move = AccountMove.create({
                            'journal_id': rec.labour_journal.id,
                            'line_ids': move_lines,
                            'date': date,
                            'ref': '%s - Labour'%self.name,
                            'mo_reference':self.id,
                            'move_type':'entry',
                        })
                        new_account_move._post()

            else:
                for i in self.workorder_ids:
                    rec.update({
                        'product_id': self.product_id.id,
                        'quantity': self.product_qty,
                    })
                debit_value = self.company_id.currency_id.round(rec.average_cost)
                credit_value = debit_value
                debit_line_vals = {
                    'name': self.name,
                    'ref':'%s - Direct Labour'%self.name,
                    'debit': debit_value if debit_value > 0 else 0,
                    'credit': -debit_value if debit_value < 0 else 0,
                    'account_id': rec.labour_output_account.id,
                }

                credit_line_vals = {
                    'name': self.name,
                    'ref': '%s - Direct Labour'%self.name,
                    'credit': credit_value if credit_value > 0 else 0,
                    'debit': -credit_value if credit_value < 0 else 0,
                    'account_id': rec.labour_valuation_account.id,
                }
                rslt = {'credit_line_vals': credit_line_vals,
                        'debit_line_vals': debit_line_vals}

                move_lines = [(0, 0, line)for line in rslt.values()]

                AccountMove = self.env['account.move'].with_context(
                    default_journal_id=rec.labour_journal.id)

                date = self._context.get(
                    'force_period_date', fields.Date.context_today(self))
                    
                new_account_move = AccountMove.create({
                    'journal_id': rec.labour_journal.id,
                    'line_ids': move_lines,
                    'date': date,
                    'ref': 'Labour Cost',
                    'mo_reference':self.id,
                    'move_type':'entry',
                })
                new_account_move._post()

        for rec in overhead_data:
            debit_value = self.company_id.currency_id.round(rec.overhead_cost)
            credit_value = debit_value
            debit_line_vals = {
                'name': self.name,
                'ref': '%s - Direct Overhead'%self.name,
                'debit': debit_value if debit_value > 0 else 0,
                'credit': -debit_value if debit_value < 0 else 0,
                'account_id': rec.overhead_output_account.id,
            }

            credit_line_vals = {
                'name': self.name,
                'ref': '%s - Direct Overhead'%self.name,
                'credit': credit_value if credit_value > 0 else 0,
                'debit': -credit_value if credit_value < 0 else 0,
                'account_id': rec.overhead_valuation_account.id,
            }
            rslt = {'credit_line_vals': credit_line_vals,
                    'debit_line_vals': debit_line_vals}

            move_lines = [(0, 0, line)for line in rslt.values()]

            AccountMove = self.env['account.move'].with_context(
                default_journal_id=rec.overhead_journal.id)

            date = self._context.get(
                'force_period_date', fields.Date.context_today(self))
                
            new_account_move = AccountMove.create({
                'journal_id': rec.overhead_journal.id,
                'line_ids': move_lines,
                'date': date,
                'ref': 'Overhead Cost',
                'mo_reference':self.id,
                'move_type':'entry',
            })
            new_account_move._post()

        acc_move = self.env['account.move'].search([])

        final_product_move = acc_move.filtered(lambda x : x.mo_reference.id == self.id and x.line_ids.product_id.id == self.product_id.id)
        final_product_move.button_draft()
        to_write = []
        for i in final_product_move.line_ids:
            if i.credit:
                to_write.append((1,i.id,{
                    'credit':self.cost_status
                }))
            else:
                to_write.append((1,i.id,{
                    'debit':self.cost_status
                }))
        final_product_move.write({'line_ids':to_write})
        final_product_move._post() 

        try:
            for rec in self:
                rec.product_id.update({
                    'final_cost': rec.cost_status
                })
        except:
            raise UserError(_("There are no configuration for product final cost"))
        return res

    def button_unbuild(self):
        res = super(MrpProductionInherit, self).button_unbuild()
        acc_move = self.env['account.move'].search([('mo_reference','=',self.id)])
        for i in acc_move:
            i.action_reverse() 
        return res

class MaterialCost(models.Model):
    _name = 'material.cost.detail'
    _description = 'Material Cost'

    mrp_id = fields.Many2one('mrp.production', string='Manufacturing Order')
    product_id = fields.Many2one('product.product', string='Used Material')
    material_cost = fields.Float(string='Total Material Cost')
    quantity = fields.Integer(string='Quantity')


class LabourCostDetail(models.Model):
    _name = 'labour.cost.detail'
    _descrition = 'Labour Cost Detail'

    mrp_id = fields.Many2one('mrp.production', string='Manufacturing Order')
    employee_id = fields.Many2one('hr.employee', string='labour')
    product_id = fields.Many2one('product.product', string='Product')
    labour_cost = fields.Float(string='Total Labour Cost')
    duration = fields.Float(string='Working Time',
                            help="Expected duration (in minutes)")
    quantity = fields.Integer(string='Quantity')
    workorder_id = fields.Many2one('mrp.workorder', string='Workorder')


class OverheadCost(models.Model):
    _name = 'overhead.cost.detail'
    _description = 'Overhead Cost'

    mrp_id = fields.Many2one('mrp.production', string='Manufacturing Order')
    overhead_cost = fields.Float(
        string='Total Overhead Cost', compute='calculate_cost')
    workcenter_id = fields.Many2one('mrp.workcenter', string='Workcenter')
    cost_type = fields.Selection(string='Cost Method', selection=[(
        'standard', 'Standard'), ('average', 'Average Cost')], default='standard')
    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')
    orders = fields.Many2many(
        comodel_name='mrp.production', string='Orders', compute='mrp_orders')
    overheads = fields.Many2many(
        comodel_name='overhead', string='Select Overhead', domain="[('workcenter_id','=',workcenter_id)]")
    income_account = fields.Many2one(
        'account.account', string='Income Account')
    expense_account = fields.Many2one(
        comodel_name='account.account', string='Expense Account')
    overhead_valuation_account = fields.Many2one(
        'account.account', string='Overhead valuation Account')
    overhead_journal = fields.Many2one(
        comodel_name='account.journal', string='Overhead Journal')
    overhead_input_account = fields.Many2one(
        'account.account', string='Overhead Input Account')
    overhead_output_account = fields.Many2one(
        'account.account', string='Overhead Output Account')


    _sql_constraints = [
        ('workcenter_uniq', 'unique (workcenter_id)',
         'The workcenter id is uniq for all cost method !')
    ]

    @api.onchange('start_date', 'end_date', 'workcenter_id')
    def mrp_orders(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                if rec.start_date < rec.end_date:
                    new_end_date = rec.end_date + relativedelta(months=1)
                    now = datetime.now()
                    if now > new_end_date:
                        new_MO_data = self.env['mrp.production'].search([('date_planned_start', '>=', rec.end_date), (
                            'date_planned_start', '<=', new_end_date), ('state', '=', 'done')])
                        new_WO_data = self.env['mrp.workorder'].search([('production_date', '>=', rec.end_date), (
                            'production_date', '<=', new_end_date), ('state', '=', 'done'), ('workcenter_id', '=', rec.workcenter_id.id)])
                        final_data = new_MO_data.filtered(
                            lambda x: x in list(new_WO_data.production_id))
                        rec.update({
                            'start_date': rec.end_date,
                            'end_date': new_end_date,
                            'orders': final_data,
                        })

                    else:
                        new_WO_data = self.env['mrp.workorder'].search([('production_date', '>=', rec.start_date), (
                            'production_date', '<=', rec.end_date), ('state', '=', 'done'), ('workcenter_id', '=', rec.workcenter_id.id)])

                        data = self.env['mrp.production'].search([('date_planned_start', '>=', rec.start_date), (
                            'date_planned_start', '<=', rec.end_date), ('state', '=', 'done')])

                        rec.orders = data.filtered(
                            lambda x: x in list(new_WO_data.production_id))

                else:
                    raise UserError(
                        _("Please Enter Valid Start Date and End Date"))

            else:
                rec.orders = False

    def calculate_cost(self):
        for rec in self:
            if rec.cost_type == 'average':
                if rec.orders:
                    rec.update({
                        'cost_type':'average',
                        'overhead_cost':sum(rec.orders.mapped('overhead_cost'))/sum(rec.orders.mapped('product_qty'))
                    })
                else:
                    overs = self.env['overhead'].search([('workcenter_id','=',self.workcenter_id.id)])
                    rec.update({
                        'cost_type':'standard',
                        'overheads':overs,
                        'overhead_cost':sum(overs.mapped('overhead_cost'))
                    })
            else:
                if rec.orders:
                    rec.update({
                        'cost_type':'average',
                        'overhead_cost':sum(rec.orders.mapped('overhead_cost'))/sum(rec.orders.mapped('product_qty'))
                    })
                else:
                    rec.update({
                        'overhead_cost':sum(rec.overheads.mapped('overhead_cost'))
                    })

class OverHead(models.Model):
    _name = 'overhead'

    overhead_name = fields.Char(string='Overhead Name')
    overhead_cost = fields.Float(string='Cost/Product')
    workcenter_id = fields.Many2one('mrp.workcenter', string='Workcenter')


class LabourCost(models.Model):
    _name = 'labour.cost'
    _description = 'Labour Cost'

    cost_type = fields.Selection(string='Cost Method', selection=[(
        'standard', 'Standard'), ('average', 'Average Cost')], default='standard')
    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')
    orders = fields.Many2many(
        comodel_name='mrp.production', string='Orders', compute='mrp_orders')
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Integer(string='Quantity')
    average_cost = fields.Float(
        string='Average Total Cost', compute='calculate_price')
    income_account = fields.Many2one(
        'account.account', string='Income Account')
    expense_account = fields.Many2one(
        comodel_name='account.account', string='Expense Account')
    labour_valuation_account = fields.Many2one(
        'account.account', string='Labour valuation Account')
    labour_journal = fields.Many2one(
        comodel_name='account.journal', string='Labour Journal')
    labour_input_account = fields.Many2one(
        'account.account', string='Labour Input Account')
    labour_output_account = fields.Many2one(
        'account.account', string='Labour Output Account')

    _sql_constraints = [
        ('product_uniq', 'unique (product_id)',
         'The product id is uniq for all cost method !')
    ]

    @api.onchange('start_date', 'end_date', 'product_id')
    def mrp_orders(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.cost_type == 'average':
                if rec.start_date < rec.end_date:
                    new_end_date = rec.end_date + relativedelta(months=1)
                    now = datetime.now()
                    if now > new_end_date:
                        new_data = self.env['mrp.production'].search([('date_planned_start', '>=', rec.end_date), (
                            'date_planned_start', '<=', new_end_date), ('state', '=', 'done'), ('product_id', '=', rec.product_id.id)])

                        rec.update({
                            'start_date': rec.end_date,
                            'end_date': new_end_date,
                            'orders': new_data,
                        })

                    else:
                        data = self.env['mrp.production'].search([('date_planned_start', '>=', rec.start_date), (
                            'date_planned_start', '<=', rec.end_date), ('state', '=', 'done'), ('product_id', '=', rec.product_id.id)])

                        rec.orders = data
                else:
                    raise UserError(
                        _("Please Enter Valid Start Date and End Date"))

            else:
                rec.orders = False

    @api.onchange('orders')
    def calculate_price(self):
        for rec in self:
            if rec.orders:
                average_costing = []
                for test in rec.orders:
                    for i in test.workorder_ids:
                        for j in i.time_ids:
                            average_costing.append(
                                (j.user_id.employee_id.timesheet_cost*i.duration)/60)

                rec.average_cost = sum(average_costing) / \
                    sum(rec.orders.mapped('product_qty'))
            else:
                rec.average_cost = 0


class ProductProductInherit(models.Model):
    _inherit = 'product.product'

    final_cost = fields.Float(string='Final Cost Based On MO')


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    mo_reference = fields.Many2one('mrp.production',string='Manufacture Order')

class StockMoveInherit(models.Model):
    _inherit = 'stock.move'

    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
        AccountMove = self.env['account.move'].with_context(default_journal_id=journal_id)

        move_lines = self._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)
        if move_lines:
            date = self._context.get('force_period_date', fields.Date.context_today(self))
            new_account_move = AccountMove.sudo().create({
                'journal_id': journal_id,
                'line_ids': move_lines,
                'date': date,
                'ref': description,
                'stock_move_id': self.id,
                'stock_valuation_layer_ids': [(6, None, [svl_id])],
                'move_type': 'entry',
                'mo_reference':self.production_id.id or self.raw_material_production_id.id,
            })
            new_account_move._post()