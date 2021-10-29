# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class FmsSettings(models.Model):
    _inherit = 'res.company'

    advance_journal_id = fields.Many2one(
        'account.journal', string='Advance Journal')
    expense_journal_id = fields.Many2one(
        'account.journal', string='Expense Journal')
    loan_journal_id = fields.Many2one(
        'account.journal', string='Expense Loan Journal')
    sale_journal_id = fields.Many2one(
        'account.journal', string='Sale Journal')
    purchase_journal_id = fields.Many2one(
        'account.journal', string='Purchase Journal')
    ieps_product_id = fields.Many2one(
        'product.product', string='IEPS Product')
    credit_limit = fields.Float()
