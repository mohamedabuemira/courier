from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError



class FmsWizardCOD(models.Model):

    _name = 'fms.create.cod.account.entry'
    _description = 'Wizard to create COD entry from Waybills'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Payments"
    _order = "payment_date desc, name desc"

    invoice_ids = fields.One2many(
        'orders', 'invoice_id', string="Waybills", readonly=False)
    journal_id = fields.Many2one(
        'account.journal', string='Cash Account',
        domain="[('type', 'in', ('bank', 'cash'))]"
    ,default = lambda self: self._get_default_cash())
    company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company', readonly=True)
    amount_total = fields.Float(compute='_compute_amount_total')
    date = fields.Date(required=True, default=fields.Date.context_today)
    notes = fields.Text()
    partner_id = fields.Many2one(
        'res.partner', 'customer', required=True,readonly=False,
        domain=[('customer', '=', True)],
    default=lambda self: self._get_default_partner())
    def _get_default_partner(self):
        ctx = self._context
        if ctx.get('active_model') == 'orders':
            return self.env['orders'].browse(ctx.get('active_ids')[0]).partner_id.id
    def _get_default_cash(self):
        ctx = self._context
        if ctx.get('active_model') == 'orders':
            return self.env['orders'].browse(ctx.get('active_ids')[0]).petty_cash.id

    @api.depends('journal_id')
    def _compute_amount_total(self):
        model = self._context.get('active_model')
        for rec in self:
            amount_total = 0
            currency = rec.journal_id.currency_id or self.env.user.currency_id
            active_ids = self.env[model].browse(
                self._context.get('active_ids'))
            total = 0
            for obj in active_ids:
                if model in [ 'orders']:
                    total += obj.amount
                amount_total = currency._convert(
                    total, self.env.user.currency_id, obj.company_id,
                    obj.date)
            rec.amount_total = amount_total

    def make_payment(self):
        active_ids = self.env[self._context.get('active_model')].browse(
            self._context.get('active_ids'))
        active_model = self._context['active_model']
        for rec in self:
            bank_account_id = rec.journal_id.default_debit_account_id.id
            currency = rec.journal_id.currency_id or self.env.user.currency_id
            currency_id = active_ids.mapped('currency_id').ids
            if len(currency_id) > 1:
                raise ValidationError(
                 _('You cannot pay documents for different currency'))
            if currency.id != list(currency_id)[0]:
                raise ValidationError(
                    _('You cannot pay documents in different currency of the '
                      'bank (%s)') % rec.journal_id.currency_id.name)
            move_lines = []
            amount_bank = 0.0
            amount_currency = 0.0
            name = 'Payment of'
            bank_line = {}
            for obj in active_ids:
                name = name + ' / ' + obj.name
                if obj.state not in ['confirm', 'closed'] :
                    raise ValidationError(
                        _('The document %s must be confirmed and '
                          'unpaid.') % obj.name)
                counterpart_move_line = {
                    'name': obj.name,
                    'account_id': (
                        obj.partner_id.property_account_receivable_id.id),
                    'credit': 0.0,
                    'journal_id': rec.journal_id.id,
                    'partner_id': obj.partner_id.id,
                }
                model_amount = {
                    'orders': obj.amount
                    if hasattr(obj, 'amount') and
                       active_model == 'orders' else 0.0,
                    }
                # Creating counterpart move lines method explained above
                counterpart_move_line, amount_bank = self.create_counterpart(
                    model_amount, currency, obj,
                    amount_currency, amount_bank, counterpart_move_line)
                self._create_payment(counterpart_move_line, rec)
                move_lines.append((0, 0, counterpart_move_line))
                if amount_currency > 0.0:
                    bank_line['amount_currency'] = amount_currency
                    bank_line['currency_id'] = currency.id
                    # Todo Separate the bank line for each Operating Unit

            bank_line = {
                'name': name,
                'account_id': bank_account_id,
                'debit': 0.0,
                'credit': amount_bank,
                'journal_id': rec.journal_id.id,
            }
            move_lines.append((0, 0, bank_line))
            move = {
                'date': rec.date,
                'journal_id': rec.journal_id.id,
                'ref': name,
                'line_ids': move_lines,
                'narration': rec.notes,
            }
            # Creating moves and reconciles method explained above
            rec.create_moves_and_reconciles(move, active_ids)

    def _create_payment(self, counterpart_move_line, record):
        obj_payment = self.env['account.payment']
        payment_id = obj_payment.create({
            'partner_type': 'customer',
            'journal_id': counterpart_move_line['journal_id'],
            'partner_id': counterpart_move_line['partner_id'],
            'amount': counterpart_move_line['debit'],
            'payment_date': record.date,
            'communication': counterpart_move_line['name'],
            'payment_type': 'outbound',
            'payment_method_id': 1,
            'state': 'posted',
        })
        counterpart_move_line['payment_id'] = payment_id.id

    def create_counterpart(self, model_amount, currency, obj,
                           amount_currency, amount_bank,
                           counterpart_move_line):
        for key, value in model_amount.items():
            #if key != self._context.get('active_model'):
              #  continue
            #if key == 'tms.expense' and value < 0.0:
              #  raise ValidationError(
                 #   _('You cannot pay the expense %s because the '
                  #    'balance is negative') % obj.name)
            if currency.id != obj.currency_id.id:
                amount_currency += value * -1
                amount_bank += currency._convert(
                    value, self.env.user.currency_id, obj.company_id,
                    obj.date)
                counterpart_move_line['amount_currency'] = (
                    value)
                counterpart_move_line['currency_id'] = (
                    currency.id)
                counterpart_move_line['debit'] = (
                    currency._convert(
                        value, self.env.user.currency_id, obj.company_id,
                        obj.date))
            else:
                amount_bank += value
                counterpart_move_line['debit'] = value
        return counterpart_move_line, amount_bank

    def create_moves_and_reconciles(self, move, active_ids):
        payments = {}
        for line in move.get('line_ids'):
            if line[2].get('payment_id'):
                payments.update({line[2].get('name'): line[2].get('payment_id')})  # noqa
                line[2].update({'payment_id': False})
        move_id = self.env['account.move'].create(move)
        for payment in payments:
            move_id.filtered(
                lambda line: line.name == payment).payment_id = payments[payment]  # noqa
        move_id.post()
        journal_id = active_ids.mapped('move_id.journal_id')
        for move_line in move_id.line_ids.filtered(
                lambda l: l.account_id.internal_type == 'payable'):
            move_ids = []
            line = self.env['account.move.line'].search([
                ('name', '=', move_line.name),
                ('account_id.internal_type', '=', 'payable'),
                ('move_id', '!=', move_id.id),
                ('journal_id', '=', journal_id.id)])
            if len(line) > 1:
                raise ValidationError(_(
                    'The driver advance account is defined as '
                    'payable. %s ') % line[0].name)
            move_ids.append(line.id)
            move_ids.append(move_line.id)
            reconcile_ids = self.env['account.move.line'].browse(
                move_ids)
            reconcile_ids.reconcile()
        active_ids.write({'payment_move_id': move_id.id})
