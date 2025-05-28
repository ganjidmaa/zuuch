# -*- coding: utf-8 -*-
{
    'name': "broker_contract",

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
    'depends': ['base', 'broker_product', 'broker_base', 'mail'],

    # always loaded
    'data': [
        'security/broker_contract_security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/car_views.xml',
        'views/miis.xml',
        'views/report_xlsx.xml',
        'views/auth_token_views.xml',
        'report/report.xml',
        'report/contract_detail_pdf_new_file.xml',
        'data/data.xml',
        'demo/demo.xml',
        'wizards/miis_download.xml',
    ],
    'qweb': [
    ],
    "assets": {
        "web.assets_backend": [
            "broker_contract/static/src/js/action_manager.js",
            'broker_contract/static/src/scss/contract_detail.scss',
        ],
    },
}

