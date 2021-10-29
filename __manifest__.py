# -*- coding: utf-8 -*-
{
    'name': "Freight Management System",

    'summary': """
        courier
        Management System for Carriers, Trucking and other companies
        """,

    'description': """
        courier system
    """,

    'author': "Abu Emira",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Transport',
    'version': '1.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'account',
                'fleet',
                'hr',
                'uom',
                'mail',
                'sale'
                ],
    'external_dependencies': {
        'python': [
            'sodapy',
            'num2words',

        ],
    },
    # always loaded
    'data': [
       'security/security.xml',
       'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/master_view.xml',
        'views/account_manger_view.xml',
        'views/hr_employee_view.xml',
        'views/order_view.xml',
        'views/partner.xml',
        'views/fms_settings_view.xml',
        'views/fms_product_template_view.xml',
        'views/fms_account_move_view.xml',
        'views/report_settlement_templates.xml',
        'views/sale_commission_view_structure.xml',
        'views/commission_view.xml',



        'views/sale_order_commission_view.xml',


        'reports/order_report.xml',
        'data/ir_sequence_freights.xml',
        'data/mail_data.xml',
        'data/order_portal_templates.xml',
        'wizards/fms_create_cod_account_entry_view.xml',
        'wizards/fms_wizard_invoice_view.xml',
        'wizards/generate_commission_view.xml',
        'wizards/commission_payment_view.xml',


        'OdooCustom/sale_order_view.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
        'demo/hr_employee.xml',

    ],
    'application': True,
}
