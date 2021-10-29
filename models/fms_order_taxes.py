
from odoo import fields, models


class FmsOrderTaxes(models.Model):
    _name = "fms.order.taxes"
    _description = "orders Taxes"
    _order = "tax_amount desc"

    order_id = fields.Many2one('orders', 'order', readonly=True)
    tax_id = fields.Many2one('account.tax', 'Tax', readonly=False)
    account_id = fields.Many2one(
        'account.account', 'Tax Account', required=False,
    )
    account_analytic_id = fields.Many2one(
        'account.analytic.account', 'Analytic account')
    tax_amount = fields.Float(digits='Account', readonly=True , store=True)
