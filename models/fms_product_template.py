# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, exceptions, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    fms_product_category = fields.Selection([
        ('delivery', 'Delivery Charges'),
        ('cod_charges', 'COD Charges'),
        ('expenses', 'Expenses'),
        ('other', 'Other'),],

        string='FMS Product Category')
    apply_for_salary = fields.Boolean()


    @api.constrains('fms_product_category')
    def unique_product_per_category(self):
        for rec in self:
            categorys = [
                ['move', 'Moves'],
                ['salary', 'Salary'],
                ['negative_balance', 'Negative Balance'],
                ['indirect_expense', 'Indirect Expense']
            ]
            for category in categorys:
                product = rec.search([
                    ('fms_product_category', '=', category[0])])
                if len(product) > 1:
                    raise exceptions.ValidationError(
                        _('Only there must be a product with category "' +
                            category[1] + '"'))


