from __future__ import division

import logging

from odoo import _, api, exceptions, fields, models, SUPERUSER_ID


from werkzeug.urls import url_encode

_logger = logging.getLogger(__name__)
try:
    from num2words import num2words
except ImportError:
    _logger.debug('Cannot `import num2words`.')


class Orders(models.Model):
    _name = 'orders'
    _description = 'Orders '
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _order = 'date desc, id desc'
    _rec_name='name'
    
    name = fields.Char(string='waybill Number', required=True, copy=False, readonly=True, index=True,
                                 default=lambda self: _('New'), tracking=True,
                                 )
    company_id = fields.Many2one(
        'res.company', required=True,
        default=lambda self: self.env.user.company_id)


    reference = fields.Char(string="Reference ")
    description = fields.Text(string="Description")
    date = fields.Datetime(
        'Date', required=True,
        help="date order for current Waybill.",
        default=fields.Datetime.now)
    employee_id = fields.Many2one(
        'hr.employee', 'Driver', required=True,
        domain=[('driver', '=', True)])
    employee_phone = fields.Char("Phone", required=True, change_default=True, readonly=True, copy=True)
    account_manger = fields.Many2one(
        'hr.employee', 'Account Manager', required=True,
        domain=[('account_manger', '=', True)])
    notes = fields.Html()
    partner_id = fields.Many2one(
        'res.partner', 'customer', required=True,
        domain=[('customer', '=', True)])
    currency_id = fields.Many2one(
        'res.currency', required=True,
        default=lambda self: self.env.user.company_id.currency_id)
    partner_order_id = fields.Many2one(
        'res.partner', 'Shipper', required=True,
        help="The name and address of the contact who requested the "
             "order or quotation.")
    sender_phone = fields.Char("Phone", required=True, change_default=True, readonly=True, copy=True)
    recevier_name = fields.Many2one(
        'res.partner', 'Recevier', required=True,
        help="Departure address for current Waybill.", change_default=True)
    recevier_phone = fields.Char(string="Phone", required=True, readonly=True, copy=True)
    upload_point = fields.Char(change_default=True)
    download_point = fields.Char(change_default=True)
    history = fields.Text()
    invoice_id = fields.Many2one(
        'account.move', readonly=True, copy=False)
    invoice_paid = fields.Boolean(
        compute="_compute_invoice_paid", readonly=True)

    responsible_id = fields.Many2one('res.users',
                                     ondelete='set null', string="Data Entry", index=True,
                                     default=lambda self: self.env.user
                                        , tracking = 2,
                                     )
    user_id = fields.Many2one(
        'res.users', string='Salesperson', index=True, tracking=2, default=lambda self: self.env.user)
    def _get_default_require_signature(self):
        return self.env.company.portal_confirmation_sign

    def _get_default_require_payment(self):
        return self.env.company.portal_confirmation_pay

    signature = fields.Image('Signature', help='Signature received through the portal.', copy=False, attachment=True,
                             max_width=1024, max_height=1024)
    signed_by = fields.Char('Signed By', help='Name of the person that signed the SO.', copy=False)
    signed_on = fields.Datetime('Signed On', help='Date of the signature.', copy=False)
    require_signature = fields.Boolean('Online Signature', default=_get_default_require_signature, readonly=True,
                                       states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    move_id = fields.Many2one('account.move', 'Journal Entry', readonly=True,
        help="Link to the automatically generated Journal Items.",
        ondelete='restrict', )
    payment_move_id = fields.Many2one(
        'account.move', string='Payment Entry',copy=False,
        readonly=True, )
    move_line_ids = fields.One2many('account.move.line', 'payment_id', readonly=True, copy=False, ondelete='restrict')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Review'),
        ('in_stock', 'In Stock'),
        ('confirm', ' Confirm '),
        ('pending', ' Pending '),
        ('with_captain', ' with captain '),
        ('delivered', ' Delivered '),
        ('not_found', ' Not Found '),
        ('return', ' Return '),
        ('recived_money', 'Recived Money '),
        ('invoiced', 'Invoiced'),
        ('sent', 'Sent'),
        ('cancel', 'Cancel'), ],
        string='Order Status', readonly=True, copy=False, default='draft', tracking=True, )
    order_line_ids = fields.One2many(
        'fms.order.line', 'order_id',
        string='Order Lines')
    tax_line_ids = fields.One2many(
        'fms.order.taxes', 'order_id', string='Tax Lines', store=True,
    )
    delivery_charges = fields.Float(
        compute='_compute_delivery_charges',
        string='Delivery Charges')
    cod_charges = fields.Float(
        compute='_compute_cod_charges',
        string='COD Charges',
    )
    other = fields.Float(
        compute='_compute_other',
        string='Other',
    )

    amount = fields.Monetary(
        string='COD Amount',copy=False)

    petty_cash = fields.Many2one(
        'account.journal', 'petty cash', required=True, copy=True, )

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('order.freights.sequence') or _('New')
            order = super(Orders, self).create(vals)
            return order

    @api.depends('payment_move_id')
    def _compute_paid(self):
        for rec in self:
            paid = False
            if rec.payment_move_id:
                paid = True
            rec.paid = paid
    @api.depends('invoice_id')
    def _compute_invoice_paid(self):
        for rec in self:
            paid = (rec.invoice_id and rec.invoice_id.invoice_payment_state == 'paid')
            rec.invoice_paid = paid

    def has_to_be_signed(self, include_draft=False):
        return (self.state == 'sent' or (
                self.state == 'draft' and include_draft)) and not self.is_expired and self.require_signature and not self.signature

    @api.onchange('partner_id', )
    def onchange_sender_partner_id(self):
        self.sender_phone = self.partner_id.phone

    @api.onchange('partner_order_id',)
    def onchange_partner_order_id(self):
        self.sender_phone = self.partner_order_id.phone

    @api.onchange('recevier_name')
    def onchange_recevier_name(self):
        self.recevier_phone = self.recevier_name.phone

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        self.employee_phone = self.employee_id.work_phone

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.partner_order_id = self.partner_id.address_get(
                ['invoice', 'contact']).get('contact', False)

    def action_review(self):
        order_dreft = self.filtered(lambda s: s.state in ['draft'])
        return order_dreft.write({
            'state': 'review',
        })

    def action_in_stock(self):
        in_stock = self.filtered(lambda s: s.state in ['review','sent'])
        return in_stock.write({
            'state': 'in_stock',
        })

    def action_confirm(self):
        confirm = self.filtered(lambda s: s.state in ['in_stock','sent'])
        return confirm.write({
            'state': 'confirm',
        })

    def action_pending(self):
        pending = self.filtered(lambda s: s.state in ['in_stock','sent'])
        return pending.write({
            'state': 'pending',
        })

    def action_new_date(self):
        new_date = self.filtered(lambda s: s.state in ['pending', 'not_found', 'return'])
        return new_date.write({
            'state': 'confirm',
        })

    def action_with_captain(self):
        with_captain = self.filtered(lambda s: s.state in ['confirm'])
        return with_captain.write({
            'state': 'with_captain',
        })

    def action_with_captain(self):
        with_captain = self.filtered(lambda s: s.state in ['confirm'])
        return with_captain.write({
            'state': 'with_captain',
        })

    def action_delivered(self):
        delivered = self.filtered(lambda s: s.state in ['with_captain'])
        return delivered.write({
            'state': 'delivered',
        })

    def action_not_found(self):
        not_found = self.filtered(lambda s: s.state in ['with_captain'])
        return not_found.write({
            'state': 'not_found',
        })

    def action_return(self):
        return_ = self.filtered(lambda s: s.state in ['with_captain'])
        return return_.write({
            'state': 'return',
        })

    def action_back(self):
        ordeer_back = self.filtered(lambda s: s.state in ['return'])
        return ordeer_back.write({
            'state': 'in_stock',
        })

    def action_recived_money(self):
        recived_money = self.filtered(lambda s: s.state in ['delivered'])
        return recived_money.write({
            'state': 'recived_money',
        })

    def action_invoiced(self):
        invoiced = self.filtered(lambda s: s.state in ['recived_money'])
        return invoiced.write({
            'state': 'invoiced',
        })

    def action_cancel(self):
        return self.write({'state': 'cancel'})

    def action_draft(self):
        courses = self.filtered(lambda s: s.state in ['cancel', 'draft'])
        return courses.write({
            'state': 'draft',
        })

    type_name = fields.Char('Type Name', compute='_compute_type_name')


    @api.depends('state')
    def _compute_type_name(self):
        for record in self:
            record.type_name = _('Order') if record.state in ('draft', 'sent', 'cancel') else _('Order')

    def _find_mail_template(self, force_confirmation_template=False):
        template_id = False
        if force_confirmation_template or (self.state != 'draft' and not self.env.context.get('proforma', False)):
            template_id = int(self.env['ir.config_parameter'].sudo().get_param('fms.email_template_edi_order'))
            template_id = self.env['mail.template'].search([('id', '=', template_id)]).id
            if not template_id:
                template_id = self.env['ir.model.data'].xmlid_to_res_id('fms.email_template_edi_order',
                                                                        raise_if_not_found=False)
            if not template_id:
                template_id = self.env['ir.model.data'].xmlid_to_res_id('fms.email_template_edi_order',
                                                                        raise_if_not_found=False)
        return template_id

    def action_send_email(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        self.ensure_one()
        template_id = self._find_mail_template()
        lang = self.env.context.get('lang')
        template = self.env['mail.template'].browse(template_id)
        if template.lang:
            lang = template._render_template(template.lang, 'orders', self.ids[0])
        ctx = {
            'default_model': 'orders',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            'model_description': self.with_context(lang=lang).type_name,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_so_as_sent'):
            self.filtered(lambda o: o.state != 'draft').with_context(tracking_disable=False).write({'state': 'sent'})
            self.env.company.sudo().set_onboarding_step_done('sale_onboarding_sample_quotation_state')
        return super(Orders, self.with_context(mail_post_autofollow=True)).message_post(**kwargs)

    #SEND EMAIL to responsible_id
    def _send_order_confirmation_mail(self ):
        if self.env.su:
            self.sudo().write({'responsible_id': [(6, 0, [responsible_id])]})
        template_id = self._find_mail_template(force_confirmation_template=True)
        if template_id:
            for order in self:
                order.with_context(force_send=True).message_post_with_template(template_id, composition_mode='comment',
                          email_layout_xmlid="mail.mail_notification_paynow")
    def _send_order_confirmation_mail(self):
        if self.env.su:
            # sending mail in sudo was meant for it being sent from superuser
            self = self.with_user(SUPERUSER_ID)
        template_id = self._find_mail_template(force_confirmation_template=True)
        if template_id:
            for order in self:
                order.with_context(force_send=True).message_post_with_template(template_id, composition_mode='comment', email_layout_xmlid="mail.mail_notification_paynow")
    def _get_share_url(self, redirect=False, signup_partner=False, pid=None):
        self.ensure_one()
        if self.state  in []:
            auth_param = url_encode(self.partner_id.signup_get_auth_param()[self.partner_id.id])
            return self.get_portal_url(query_string='&%s' % auth_param)
        return super(Orders, self)._get_share_url(redirect, signup_partner, pid)

    def _get_payment_type(self, tokenize=False):
        self.ensure_one()
        return 'form_save' if tokenize else 'form'

    def _get_portal_return_action(self):
        """ Return the action used to display orders when returning from customer portal. """
        self.ensure_one()
        return self.env.ref('sale.action_quotations_with_onboarding')

    def action_order_sent(self):
        if self.filtered(lambda so: so.state == 'draft'):
            raise UserError(_('Only draft orders can be marked as sent directly.'))
        for order in self:
            order.message_subscribe(partner_ids=order.partner_id.ids)
        self.write({'state': 'sent'})


    @api.onchange('employee_id')
    def onchange_employee__id(self):
        self.petty_cash = self.employee_id.fms_petty_cash_account_id

    def button_journal_entries(self):
        return {
            'name': _('Journal Items'),
            'view_mode': 'tree,form',
            'res_model': 'account.move.line',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('payment_id', '=', self.ids)],
             'context': {'create': False},
        }
    def button_invoices(self):
        return {
            'name': _(' Invoices'),
            'view_mode': 'tree,form',
            'res_model': 'account.move','orders'
            'view_id': False,
            'views': [(self.env.ref('account.view_move_tree').id, 'tree'), (self.env.ref('account.view_move_form').id, 'form')],
            'type': 'ir.actions.act_window',
            'domain': [('waybill_ids', 'in', self.ids)],
            'context': {'create': False},
        }
    amount_untaxed = fields.Float(
        compute='_compute_amount_untaxed',
        string='SubTotal', store=True)
    amount_tax = fields.Float(
        compute='_compute_amount_tax',
        string='Taxes')
    amount_total = fields.Float(
        compute='_compute_amount_total',
        string='Total', store=True)

    def _compute_amount_all(self, category):
        for order in self:
            field = 0.0
            for line in order.order_line_ids:
                if (line.product_id.fms_product_category ==
                        category):
                    field += line.price_subtotal
            return field
    @api.depends('order_line_ids')
    def _compute_amount_untaxed(self):
        for order in self:
            amount_untaxed = 0
            for line in order.order_line_ids:
                amount_untaxed += line.price_subtotal
                order.amount_untaxed = amount_untaxed

    @api.onchange('order_line_ids')
    def onchange_order_line_ids(self):
        for order in self:
            tax_grouped = {}
            for line in order.order_line_ids:
                unit_price = (
                        line.unit_price * (1 - (line.discount or 0.0) / 100.0))
                taxes = line.tax_ids.compute_all(
                    unit_price, order.currency_id, line.product_qty,
                    line.product_id, order.partner_id)
                for tax in taxes['taxes']:
                    val = {
                        'tax_id': tax['id'],
                        'tax_amount': tax['amount']
                    }
                    if tax['id'] not in tax_grouped:
                        tax_grouped[tax['id']] = val
                    else:
                        tax_grouped[
                            tax['id']]['tax_amount'] += val['tax_amount']
            tax_lines = order.tax_line_ids.browse([])
            for tax in tax_grouped.values():
                tax_lines += tax_lines.new(tax)
            order.tax_line_ids = tax_lines

    @api.depends('order_line_ids')
    def _compute_delivery_charges(self):
        for rec in self:
            rec.delivery_charges = rec._compute_amount_all('delivery')

    @api.depends('order_line_ids')
    def _compute_cod_charges(self):
        for rec in self:
            rec.cod_charges = rec._compute_amount_all('cod_charges')

    @api.depends('order_line_ids')
    def _compute_other(self):
        for rec in self:
            rec.other = rec._compute_amount_all('other')

    @api.depends('order_line_ids')
    def _compute_amount_tax(self):
        for rec in self:
            amount_tax = 0
            for line in rec.order_line_ids:
                amount_tax += line.tax_amount
            rec.amount_tax = amount_tax

    @api.depends('amount_untaxed', 'amount_tax')
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = rec.amount_untaxed + rec.amount_tax

    def preview_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': self.get_portal_url(),
        }

