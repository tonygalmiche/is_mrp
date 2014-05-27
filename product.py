# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    Asma BOUSSELMI - CONSULTANT OPENERP CONFIRME
#
##############################################################################

from datetime import datetime, timedelta
import time
from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _

class product_product(osv.osv):
    _inherit = 'product.product'

    _columns = {
        'lot_mini': fields.float('Lot Mini'),
        'multiple': fields.float('Multiple de'),
        'delai_fabrication': fields.integer('Delai de fabrication minimum en jours'),
        'temps_realisation': fields.float('Temps de realisation en secondes'),
    }

    _defaults = {
        'lot_mini': 0.0,
        'multiple': 1.0,
        'delai_fabrication': 0.0,
        'temps_realisation': 0.0,
    }

product_product()

