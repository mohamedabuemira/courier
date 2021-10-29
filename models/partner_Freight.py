from odoo import fields, models

class partner_Freight(models.Model):
    _inherit = 'res.partner'

    customer = fields.Boolean(default=False,  help='Used to define if this person will be used as a customer')
    shipper = fields.Boolean(default=False,help='Used to define if this person will be used as a customer')
    recevier = fields.Boolean(default=False,help='Used to define if this person will be used as a Recevier')
