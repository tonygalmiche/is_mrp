# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    Asma BOUSSELMI - CONSULTANT OPENERP CONFIRME
#
##############################################################################

{
    'name': 'MRP Secteur automobile',
    'version': '1.0',
    'category': 'Manufacturing',
    'description': """
MRP pour le secteur automobile
    """,
    'author': 'Asma BOUSSELMI',
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
