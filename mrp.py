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

class mrp_prevision(osv.osv):
    _name = 'mrp.prevision'
    _description = 'Prevision des fabrication dans le secteur automobile'
    _columns = {
        'name': fields.char('Name', size=128, required=True),
        'type': fields.selection([('sug_fabrication', 'Suggestion de fabrication'),
                                  ('besoin_sug', 'Besoin Suggere'),
                                  ('sug_cmd_four', 'Suggestion de commande fournisseur')], "Type", required=True),
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'start_date': fields.date('Date debut'),
        'end_date': fields.date('Date fin'),
        'quantity': fields.float('Quantity'),
        'note': fields.text('Information'),
        'niveau': fields.integer('Niveau', readonly=True, required=True),
        'stock_th': fields.float('Stock Theorique', readonly=True),
        'company_id': fields.many2one('res.company', 'Company', required=True, change_default=True, readonly=True),
        'active': fields.boolean('Active'),
    }

    _defaults = {
        'active': True,
        'name': lambda obj, cr, uid, context: '/',
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'mrp.prevision', context=c),
    }

    def create(self, cr, uid, vals, context=None):
        if vals.get('name','/')=='/':
            sequence_ids = []
            if vals['type'] == 'sug_fabrication':
                sequence_ids = self.pool.get('ir.sequence').search(cr, uid, [('code','like','mrp.prevision'),('name','=','Suggestion_fabrication'),], context=context)
            if vals['type'] == 'besoin_sug':
                sequence_ids = self.pool.get('ir.sequence').search(cr, uid, [('code','like','mrp.prevision'),('name','=','Besoin_suggere'),], context=context)
            if vals['type'] == 'sug_cmd_four':
                sequence_ids = self.pool.get('ir.sequence').search(cr, uid, [('code','like','mrp.prevision'),('name','=','Suggestion_commande_fournisseur'),], context=context)

            if sequence_ids:
                vals['name'] = self.pool.get('ir.sequence').get_id(cr, uid, sequence_ids[0], 'id', context) or '/'
            
        return super(mrp_prevision, self).create(cr, uid, vals, context=context)

mrp_prevision()

