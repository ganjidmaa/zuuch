# -*- coding: utf-8 -*-
{
    'name': "broker_base",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr'],

    # always loaded
    'data': [
        'security/broker_base_menu.xml',
        'security/ir.model.access.csv',
        'views/company_views.xml',
        'views/user_views.xml',
        'views/insurance_views.xml',
        'views/customer_views.xml',
        'views/country_zone_views.xml',
        'views/hr_employee_views.xml',
        'views/menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
}

