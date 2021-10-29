from __future__ import division

import logging

from odoo import _, api, exceptions, fields, models, SUPERUSER_ID


from werkzeug.urls import url_encode

_logger = logging.getLogger(__name__)
try:
    from num2words import num2words
except ImportError:
    _logger.debug('Cannot `import num2words`.')


class Commission(models.Model):
    _name = 'commission'
    _description = 'commission drivers '
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _order = ' id desc'
    _rec_name='name'
    name = fields.Char(string=' Number', required=True, copy=False, readonly=True, index=True,
                                 default=lambda self: _('New'), tracking=True,
                                 )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Review'),
        ('confirm', ' Confirm '),
        ('cancel', 'Cancel'), ],
        string='Order Status', readonly=True, copy=False, default='draft', tracking=True, )
    def action_review(self):
        order_dreft = self.filtered(lambda s: s.state in ['draft'])
        return order_dreft.write({
            'state': 'review',
        })

    def action_confirm(self):
        confirm = self.filtered(lambda s: s.state in ['review'])
        return confirm.write({
            'state': 'confirm',
        })

    def action_cancel(self):
        return self.write({'state': 'cancel'})

    def action_draft(self):
        courses = self.filtered(lambda s: s.state in ['cancel', 'draft'])
        return courses.write({
            'state': 'draft',
        })

    notes = fields.Html()
    employee_id = fields.Many2many(
        'hr.employee',  required=True,
        domain=[('driver', '=', True)])
    analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('commission.freights.sequence') or _('New')
            commission = super(Commission, self).create(vals)
            return commission
    sales = fields.Char()

class CommissionSale(models.Model):
    _name = 'sale.commission'
    _rec_name='name'
    name = fields.Char(string=' Number', required=True, copy=False, readonly=True)
