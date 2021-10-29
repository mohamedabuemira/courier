from odoo import models, fields, api, _
from odoo.exceptions import Warning,ValidationError


class SaleOrderCommission(models.Model):
    _name = 'sale.order.commission'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'salesperson'
    _order = "id desc"

    name = fields.Char(string=' Number', required=True, copy=False, readonly=True, index=True,
                       default=lambda self: _('New'), tracking=True, )
    product_id = fields.Many2one('product.product', 'Product')

    commission_structure_id = fields.Many2one('commission.structure.ecotech', 'Commission Structure')
    salesperson = fields.Many2one('hr.employee',string="Driver")
    net_amount = fields.Float(string="Net Amount",
    widget ='monetary'
                              )
    net_commission = fields.Float(string="Net Commission",widget ='monetary')
    sale_order_ids = fields.Many2many('account.move', string="Invoice Orders")
    general_amount = fields.Float(string='General Amount')
    deduct_amount = fields.Char(string='Deduction Amount')
    general_cal = fields.Char('Commission Calculated')
    general_commission = fields.Float(string='General Commission')
    special_amount = fields.Float(string='Special Amount')
    special_commission = fields.Float(string='Special Commission')
    fixed_commission = fields.Float(string='Fixed Commission')
    general_amount_fixed = fields.Float(string='Fixed Amount')

    special_commission_line_ids = fields.One2many('special.commission.line', 'sales_commission_id', 'Special Commission Calculation'
                                                  ,widget='one2many_list'
                                                  )
    analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')

    fixed_commission_line_ids = fields.One2many('fixed.commission.line', 'sales_commission_id_fixed', 'Fixed Commission Calculation')
    company_id = fields.Many2one(
        'res.company', required=True,
        default=lambda self: self.env.user.company_id)
    date = fields.Datetime(
        'Date', required=True,
        help="date order for current Waybill.",
        default=fields.Datetime.now)
    currency_id = fields.Many2one(
        'res.currency', required=True,
        default=lambda self: self.env.user.company_id.currency_id)

    move_id = fields.Many2one('account.move', 'Payment Entry', readonly=True,
        help="Link to the automatically generated Journal Items.",
        ondelete='restrict', )

    move_line_ids= fields.One2many('account.move.line', 'payment_id', readonly=True, copy=False, ondelete='restrict')

    state = fields.Selection([
        ('draft','Draft'),
        ('confirm', 'Confirm'),
        ('locked','Locked')
    ],'State',default='draft' ,tracking=True)
    debit_account = fields.Many2one(
        string="Expenses Account", comodel_name="account.account", required=True
    )

    invoice_paid = fields.Boolean(
        compute="_compute_paid", readonly=True)
    payment_move_id = fields.Many2one(
        'account.move', string='Payment Entry', copy=False,
        readonly=True, )

    @api.depends('payment_move_id')
    def _compute_paid(self):
        for rec in self:
            posted = (rec.payment_move_id.state == 'posted')
            rec.invoice_paid = posted

    def action_confirm_commission(self):
        for rec in self:
            if rec.state == 'draft':
                rec.write({'state': 'confirm'})

    def action_lock_commission(self):
        for rec in self:
            if rec.state == 'confirm':
                rec.write({'state':'locked'})

    def action_reset_commission(self):
        if len(self) > 1:
            for user in self.mapped('salesperson'):
                last = self.search([('salesperson','=',user.id)],order='create_date desc')[0]
                last.write({'state':'draft'})
        else:
            other_draft = self.search([('state','=','draft'),('salesperson','=',self.salesperson.id)])
            if other_draft:
                raise Warning('Please lock other draft state commission record of this particular User.')
            else:
                self.write({'state':'draft'})

    def unlink(self):
        for rec in self:
            [order.write({'is_commission_created':False}) for order in rec.sale_order_ids]
        return super(SaleOrderCommission, self).unlink()


    def action_view_sales(self):
        action = self.env.ref('account.action_move_in_invoice_type').read()[0]

        sale_orders = self.sale_order_ids
        if len(sale_orders) > 1:
            action['domain'] = [('id', 'in', sale_orders.ids)]
        elif sale_orders:
            action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
            action['res_id'] = sale_orders.id
        return action

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('commission.captain.sequence') or _('New')
            commission = super(SaleOrderCommission, self).create(vals)
            return commission





class SpecialCommissionLine(models.Model):
    _name = 'special.commission.line'

    sales_commission_id = fields.Many2one('sale.order.commission')
    product_id = fields.Many2one('product.product', 'Product')
    qty_sold = fields.Integer('Units')
    amount = fields.Float('Total Amount')
    cal = fields.Char('Commission Calculated Per unit')
    commission = fields.Float('Commission Amount')

class Fixedcommissionline(models.Model):
     _name= 'fixed.commission.line'
     sales_commission_id_fixed = fields.Many2one('sale.order.commission')
     general_fixed = fields.Char('Commission Calculated')
     general_amount_fixed = fields.Float(string='Fixed Amount')
     deduct_amount_fixed = fields.Char(string='Deduction Amount')
     fixed_commission = fields.Float(string='Fixed Commission')



