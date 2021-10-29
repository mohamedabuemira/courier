from odoo import models, fields, api, _



class CommissionStructure(models.Model):
    _name = 'commission.structure.ecotech'

    def _get_default_deduction_amount(self):
        for rec in self:
            if rec.deduction_type == 'fixed':
                return 0.0
            else:
                return 1.0

    name = fields.Char(string="Name")
    commission_type = fields.Selection(
        selection=[("fixed", "Fixed percentage"), ("section", "By sections")],
        string="Type",
        required=True,
        default="fixed",
    )

    active = fields.Boolean(default=True)
    invoice_state = fields.Selection(
        [("open", "Invoice Based"), ("paid", "Payment Based")],
        string="Invoice Status",
        required=True,
        default="open",
    )
    amount_base_type = fields.Selection(
        selection=[("gross_amount", "Gross Amount"), ("net_amount", "Net Amount")],
        string="Base",
        required=True,
        default="gross_amount",
    )

    deduction_amount = fields.Float(string="Deduction Amount",default=_get_default_deduction_amount)
    deduction_type = fields.Selection([('fixed', 'Fixed Amount'), ('percentage', 'Percentage')],
                                      'Deduction Type To Compute', default='fixed')
    commission_line_ids = fields.One2many('commission.structure.line', 'commission_id',
                                         string="Commission Structure Ranges")
    exclude_line_ids = fields.One2many('exclude.structure.line', 'commission_id', string="Exclude From Computation")
    fixed_line_ids = fields.One2many('fixed.structure.line', 'commission_id', string="Fixed From Computation")

    def action_view_users(self):
        action = self.env.ref('fms.tms_open_view_employee_list').read()[0]

        users = self.env['hr.employee'].search([('commission_structure_id', '=', self.id),
                                              ('commission_structure_id','!=',False)])
        if not users:
            return {'effect':{'fadeout':'slow',
                              'message':"Ohh %s, None of the Users associated with this Commission Structure." %
                                        self.env.user.name,
                              'img_url':'/web/static/src/img/warning.png', 'type':'rainbow_man'}}

        if len(users) > 1:
            action['domain'] = [('id', 'in', users.ids)]
        elif users:
            action['views'] = [(self.env.ref('fms.view_employee_form_tms').id, 'form')]
            action['res_id'] = users.id
        return action


class CommissionStructureLine(models.Model):
    _name = 'commission.structure.line'

    commission_id = fields.Many2one("commission.structure.ecotech")
    amount_above = fields.Float(
        string='From',
        help="Price Total More or Equal")
    amount_less_than = fields.Float(
        string='To',
        help="Price Total Less Than")
    commission_percent = fields.Float(string="Commission Percentage (%)")



class CommissionExcludeLine(models.Model):
    _name= 'exclude.structure.line'

    commission_id = fields.Many2one("commission.structure.ecotech")
    product_id = fields.Many2one('product.product', 'Product To Be Excluded')
    commission_per_drum = fields.Float(string='Commission Per unit')
    compute_type = fields.Selection([('fixed', 'Per Unit'), ('percentage', 'Percentage')],
                                      'Type To Compute',default='fixed')

class FixedStructureline(models.Model):
    _name= 'fixed.structure.line'

    commission_id = fields.Many2one("commission.structure.ecotech")
    fix_qty = fields.Float(string="Fixed percentage")

