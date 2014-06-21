# -*- coding: utf-8 -*-

{
    'name': 'MRP Secteur automobile',
    'version': '1.0',
    'category': 'InfoSaône',
    'description': """
MRP pour le secteur automobile
    """,
    'author': 'Tony GALMICHE / Asma BOUSSELMI',
    'maintainer': 'InfoSaône',
    'website': 'http://www.infosaone.com',
    'depends': ['product','mrp', 'mrp_byproduct', 'is_automobile_contract'],
    'data': [
        'product_view.xml',
        'mrp_view.xml',
        'wizard/generate_previsions_view.xml',
        'mrp_sequence.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
