# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _

class sale(models.Model):
    _inherit = 'sale.order'
    partner_id = fields.Many2one(
        'res.partner', 'customer', required=True,
            domain = [('customer', '=', True)])

class invices(models.Model):
    _inherit = 'account.move'

    def _get_default_driver(self):
        ctx = self._context
        if ctx.get('active_model') == 'orders':
            return self.env['orders'].browse(ctx.get('active_ids')[0]).employee_id.id

    driver = fields.Many2one(
        'hr.employee', 'Driver', required=False,
        domain=[('driver', '=', True)],
    change_default = True, default = _get_default_driver,
    )
    is_commission_created = fields.Boolean('Commission is created or not',copy=False)



