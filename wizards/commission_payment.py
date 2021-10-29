from odoo import _, api, exceptions, models,fields
from odoo.exceptions import UserError, ValidationError



class FmsWizardInvoice(models.TransientModel):
    _name = 'fms.wizard.commission.payment'
    _description = 'Wizard to create payment to commission'


    def _default_journal_id(self):
        return self.env["account.journal"].search([("type", "=", "Cash")])[:1]

    journal_id = fields.Many2one(
        comodel_name="account.journal",
        required=True,
        domain="[('type', 'in', ('bank', 'cash'))]",
        default=_default_journal_id,
    )
    debit_account = fields.Many2one(
        string="Expenses Account", comodel_name="account.account", required=True ,
        domain="[('internal_group', '=', 'expense'), ('deprecated', '=', False)]",
    )
    analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    date = fields.Date(default=fields.Date.context_today)
    amount_total = fields.Float(string="Commission Amount",compute='_compute_amount_total')
    notes = fields.Text(string="Notes")
    name = fields.Char(string=' Number', required=True, copy=False, readonly=True, index=True,
                       )
    salesperson = fields.Many2one('hr.employee', string="Capitan",readonly=True,
    default=lambda self: self._get_salesperson())
    move_id = fields.Many2one('account.move', string=' Entry',copy=False)
    def _get_salesperson(self):
        ctx = self._context
        if ctx.get('active_model') == 'sale.order.commission':
            return self.env['sale.order.commission'].browse(ctx.get('active_ids')[0]).salesperson.id

    @api.depends('salesperson')
    def _compute_amount_total(self):
        model = self._context.get('active_model')
        for rec in self:
            amount_total = 0
            currency = rec.journal_id.currency_id or self.env.user.currency_id
            active_ids = self.env[model].browse(
                self._context.get('active_ids'))
            total = 0
            for obj in active_ids:
                if model in ['sale.order.commission']:
                    total += obj.net_commission
                amount_total = currency._convert(
                    total, self.env.user.currency_id,obj.company_id,
                    obj.date)
            rec.amount_total = amount_total

    def _prepare_move(self):
        active_ids = self.env[self._context.get('active_model')].browse(
                 self._context.get('active_ids'))
        for obj in active_ids:
            name = 'Payment of'
            name = name + ' / ' + obj.name +' / ' + str(obj.salesperson.name)
            if obj.state not in ['confirm'] or obj.invoice_paid == True :
                raise ValidationError(
                    _('The document %s must be confirmed  or posted'
                      ) % obj.name)
            model_amount = obj.net_commission
        for line in self:
            expense_move_line = {
                'name': obj.name,
                'account_id': line.debit_account.id,
                'debit': float(model_amount),
                'credit': 0.0,
                'journal_id': line.journal_id.id,
                'analytic_account_id': line.analytic_id.id,
                'analytic_line_ids':[(6, 0, line.analytic_tag_ids.ids)],
            }
        bank_line = {
            'name': obj.name,
            'account_id': line.journal_id.default_debit_account_id.id,
            'debit': 0.0,
            'credit': float(model_amount),
            'journal_id': line.journal_id.id,
        }
        move_vals = {
            'date': line.date,
            'journal_id': line.journal_id.id,
            'ref': name,
            'line_ids': [(0, 0, bank_line), (0, 0, expense_move_line)],
            'narration': line.notes,
        }
        return move_vals

    def make_payment(self ):
        move = self.env['account.move'].create(self._prepare_move())
        self.write({'move_id': move.id})

        active_model = self._context.get('active_model')
        records = self.env[active_model].browse(
            self._context.get('active_ids'))
        records.write({'payment_move_id': move.id})






