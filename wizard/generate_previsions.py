# -*- coding: utf-8 -*-

import time
import datetime

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc

class mrp_generate_previsions(osv.osv_memory):

    _name = "mrp.previsions.generate"
    _description = "Generate previsions"
    _columns = {
        'max_date': fields.date('Date Max', required=True),
    }

    def _check_date_max(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)
        if obj.max_date <= time.strftime('%Y-%m-%d'):
            return False
        return True

    _constraints = [
        (_check_date_max, 'La date max doit etre superieure a la date de jours', ['max_date']),
    ]


    #Calculer les dates entre deux dates différentes
    def list_dates_availables(self, cr, uid, date_max, context=None):
        list_dates = []
        
        date = time.strftime('%Y-%m-%d')        
        from_dt = datetime.datetime.strptime(date, '%Y-%m-%d')
        to_dt = datetime.datetime.strptime(date_max, '%Y-%m-%d')
        timedelta = to_dt - from_dt
        diff_day = timedelta.days + float(timedelta.seconds) / 86400

        j=0
        while(j <= diff_day):
            d = datetime.datetime.strptime(date, '%Y-%m-%d') + datetime.timedelta(days=j)
            j +=1
            list_dates.append(d.strftime('%Y-%m-%d'))

        list_dates.sort()
        return list_dates

    #Déterminer la liste des produits utilisés dans les commandes, les OF et les prévisions suggérées
    def list_products_availables(self, cr, uid, niveau, context=None):
        lst_products = []

        if niveau == 0:
            #Chercher dans les commandes
            order_obj = self.pool.get('sale.order.line')
            sale_ids = order_obj.search(cr, uid, [], context=context)
            if sale_ids:
                for sale in order_obj.browse(cr, uid, sale_ids, context=context):
                    if sale.product_id not in lst_products:
                        lst_products.append(sale.product_id)
                    else:
                        continue
            #Chercher dans les ordres de fabrication
            mrp_obj = self.pool.get('mrp.production')
            mrp_ids = mrp_obj.search(cr, uid, [], context=context)
            if mrp_ids:
                for mrp in mrp_obj.browse(cr, uid, mrp_ids, context=context):
                    if mrp.product_id not in lst_products:
                        lst_products.append(mrp.product_id)
                    else:
                        continue

        else: #Chercher dans les prévision besoin suggéré de niveau adéquat
            prevision_obj = self.pool.get('mrp.prevision')
            prevision_ids = prevision_obj.search(cr, uid, [('type','=','besoin_sug'),('niveau','=',niveau),], context=context)
            if prevision_ids:
                for prev in prevision_obj.browse(cr, uid, prevision_ids, context=context):
                    if prev.product_id not in lst_products:
                        lst_products.append(prev.product_id)
                    else:
                        continue

        return lst_products
    

    #Calculer la somme des quantités des commandes
    def sum_qty_cmd(self, cr, uid, date, product, context=None):
        if date == time.strftime('%Y-%m-%d'):
            cr.execute("SELECT SUM(product_uom_qty) FROM sale_order_line line " \
                   "JOIN sale_order sale ON line.order_id = sale.id " \
                   "WHERE sale.state NOT IN ('done', 'cancel') " \
                   "AND sale.date_expedition <= %s AND line.product_id = %s", (date, product,))
        else:
            cr.execute("SELECT SUM(product_uom_qty) FROM sale_order_line line " \
                       "JOIN sale_order sale ON line.order_id = sale.id " \
                       "WHERE sale.state NOT IN ('done', 'cancel') " \
                       "AND sale.date_expedition = %s AND line.product_id = %s", (date, product,))
        qty_cmd = cr.fetchone()

        if qty_cmd[0] is None:
            return 0
        else:
            return qty_cmd[0]

    #Retourner la quantité des produits non fabriqués
    def sum_qty_of(self, cr, uid, lst_mrp, context=None):
        qty_of = 0
        if lst_mrp:
            for prod in self.pool.get('mrp.production').browse(cr, uid, lst_mrp, context=context):
                done = 0.0
                for move in prod.move_created_ids2:
                    if move.product_id == prod.product_id:
                        if not move.scrapped:
                            done += move.product_qty
                qty_prod = (prod.product_qty - done)
                qty_of += qty_prod
                
        return qty_of
        
    #Calculer la somme des quantités des ordres de fabrications lancés
    def list_mrp_prod(self, cr, uid, date, product, context=None):
        date1 = time.strftime('%Y-%m-%d %H:%M:%S', time.strptime(date + ' 00:00:00', '%Y-%m-%d %H:%M:%S'))
        date2 = time.strftime('%Y-%m-%d %H:%M:%S', time.strptime(date + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
        if date == time.strftime('%Y-%m-%d'):
            cr.execute("SELECT DISTINCT(id) FROM mrp_production WHERE product_id = %s AND date_planned <= %s AND state not in ('cancel', 'done')", (product, date2,))
        else:
            cr.execute("SELECT DISTINCT(id) FROM mrp_production WHERE product_id = %s AND date_planned <= %s AND date_planned >= %s AND state not in ('cancel', 'done')", (product, date2, date1,))
        lst_mrp = [t[0] for t in cr.fetchall()]
        if lst_mrp:
            return self.sum_qty_of(cr, uid, lst_mrp, context=context)
        else:
            return 0


    #Calculer la somme des quantités des prévisions de suggestion
    def sum_qty_prevision_sug(self, cr, uid, prevision, context=None):
        if prevision:
            return prevision.quantity
        else:
            return 0
            

    #Calculer la somme des quantités des prévision de type besoin suggérés
    def sum_qty_besoin_sugg(self, cr, uid, date, product, niveau, context=None):
        if date == time.strftime('%Y-%m-%d'):
            cr.execute("SELECT SUM(quantity) FROM mrp_prevision " \
                   "WHERE type = 'besoin_sug' AND start_date <= %s AND product_id = %s AND niveau = %s", (date, product, niveau,))
        else:
            cr.execute("SELECT SUM(quantity) FROM mrp_prevision " \
                   "WHERE type = 'besoin_sug' AND start_date = %s AND product_id = %s AND niveau = %s", (date, product, niveau))
        qty_ft = cr.fetchone()

        if qty_ft[0] is None:
            return 0
        else:
            return qty_ft[0]

    #déterminer la date max des besoins suggérés
    def date_max_suggestion(self, cr, uid, product, niveau, context=None):
        cr.execute("SELECT max(start_date) FROM mrp_prevision " \
                   "WHERE product_id = %s and niveau = %s ", (product, niveau,))
        max_date = cr.fetchone()

        if max_date[0] is None:
            return ''
        else:
            return max_date[0]

    # Calculer la quantité réelle en stock
    def calcul_qty_stock_reel(self, cr, uid, product, context=None):
        inventory_obj = self.pool.get('stock.inventory.line')
        
        cr.execute('SELECT MAX(inv.id) FROM stock_inventory inv ' \
                   'JOIN stock_inventory_line inv_line ON inv.id = inv_line.inventory_id ' \
                   'WHERE inv_line.product_id = %s ', (product, ))
        last_inventory = cr.fetchone()
                                
        inventory_ids = inventory_obj.search(cr, uid, [('product_id','=',product), ('inventory_id','=',last_inventory[0])], context=context)
        qty_stock = 0
        if inventory_ids:
            for inv in inventory_obj.browse(cr, uid, inventory_ids, context=context):
                    qty_stock += inv.product_qty

        return qty_stock
        
    #Calculer le stock theorique 
    def calcul_stock_theorique(self, cr, uid, qty_stock, qty, qty_mrp, qty_prev, qty_four, context=None):
        qty_th = qty_stock - qty + qty_mrp + qty_prev + qty_four
        return qty_th

    #Calculer la quantité de la prévision en fonction de lot mini et multiple de
    def calcul_prevision_qty(self, cr, uid, stock_th, product, context=None):
        if -(stock_th) <= product.lot_mini:
            return product.lot_mini
        else: # la valeur absolu de stock_th est superieure au lot_mini
            qty1 = -(stock_th) - product.lot_mini
            qty2 = qty1 / product.multiple
            if int(qty2) < qty2:
                qty2 = int(qty2) + 1
            return product.lot_mini + (qty2 * product.multiple)


    #Calculer la somme des quantités des commandes
    def sum_qty_cmd_four(self, cr, uid, date, product, context=None):
        if date == time.strftime('%Y-%m-%d'):
            cr.execute("SELECT SUM(product_qty) FROM purchase_order_line line " \
                   "JOIN purchase_order purchase ON line.order_id = purchase.id " \
                   "WHERE purchase.state NOT IN ('done', 'cancel') " \
                   "AND line.date_planned <= %s AND line.product_id = %s", (date, product,))
        else:
            cr.execute("SELECT SUM(product_qty) FROM purchase_order_line line " \
                       "JOIN purchase_order purchase ON line.order_id = purchase.id " \
                       "WHERE purchase.state NOT IN ('done', 'cancel') " \
                       "AND line.date_planned = %s AND line.product_id = %s", (date, product,))
        qty_cmd = cr.fetchone()
        if date == time.strftime('%Y-%m-%d') and product == 57:
            print 'result ********', qty_cmd
        if qty_cmd[0] is None:
            return 0
        else:
            return qty_cmd[0]

    def prevision_fournisseur(self, cr, uid, product, context=None):
        cr.execute("SELECT MAX(id) FROM mrp_prevision " \
                   "WHERE type = 'sug_cmd_four' AND product_id = %s ", (product,))
        prevision_id = cr.fetchone()
        if prevision_id[0] is None:
            return False
        else:
            return True
        
    #Retourner Vrai s'il faut créer une prévision fournisseur
    def create_prevision_sug_cmd_four(self, cr, uid, product, date, stock_four, context=None):
        cr.execute("SELECT MAX(id) FROM mrp_prevision " \
                   "WHERE type = 'sug_cmd_four' AND product_id = %s ", (product,))
        prevision_id = cr.fetchone()
        if prevision_id[0] is None:
            return True
        else:
            prevision_obj = self.pool.get('mrp.prevision')
            prevision = prevision_obj.browse(cr, uid, prevision_id[0], context=context)
            if self.calcul_prevision_qty(cr, uid, (prevision.stock_th - stock_four), prevision.product_id, context=context) <= prevision.quantity:
                return False
            else:
                return True

    #Calculer la date debut de la prevision
    def calcul_date_prevision(self, cr, uid, date, quantity, product, context=None):
        time_production = quantity * product.temps_realisation
        start_date = datetime.datetime.strptime(date, '%Y-%m-%d') - datetime.timedelta(days=product.delai_fabrication) - datetime.timedelta(seconds=time_production)
        start_time = start_date.strftime('%H:%M:%S')
        if start_time > '01:00:00':
            start_date = datetime.datetime.strptime(date, '%Y-%m-%d') - datetime.timedelta(days=(product.delai_fabrication + 1)) - datetime.timedelta(seconds=time_production)
        start_date = start_date.strftime('%Y-%m-%d')
        return start_date


    #Créer une prévision
    def create_prevision(self, cr, uid, product, quantity, start_date, end_date, type, niveau, stock_th, note, context=None):
        prevision_obj = self.pool.get('mrp.prevision')
        prevision_values = {
            'name': '/',
            'type': type,
            'product_id': product,
            'quantity': quantity,
            'start_date': start_date,
            'end_date': end_date,
            'niveau': niveau,
            'stock_th': stock_th,
            'note': note,
        }

        prevision = prevision_obj.create(cr, uid, prevision_values, context=context)
        return prevision
    
    #Déterminer le premier niveau de la nomenclature d'un produit
    def get_product_boms(self, cr, uid, product, context=None):
        boms = []
        bom_obj = self.pool.get('mrp.bom')
        
        template_id = product.product_tmpl_id and product.product_tmpl_id.id or False
        if template_id:
            bom_ids = bom_obj.search(cr, uid, [('product_tmpl_id','=',template_id),], context=context)
            if bom_ids:
                for line in bom_obj.browse(cr, uid, bom_ids[0], context=context).bom_line_ids:
                    boms.append(line.id)
        return boms

    #Vérifier si un produit a une nomenclature ou non
    def product_nomenclature(self, cr, uid, product, context=None):
        bom_obj = self.pool.get('mrp.bom')
        
        product = self.pool.get('product.product').read(cr, uid, product, ['product_tmpl_id'], context=context)
        template_id = product['product_tmpl_id'] and product['product_tmpl_id'][0] or False
        if template_id:
            bom_ids = bom_obj.search(cr, uid, [('product_tmpl_id','=',template_id),], context=context)
            if bom_ids:
                if bom_obj.browse(cr, uid, bom_ids[0], context=context).bom_line_ids :
                    return True
        return False
                    



    def generate_previsions(self, cr, uid, ids, context=None):
        prevision_obj = self.pool.get('mrp.prevision')
        bom_line_obj = self.pool.get('mrp.bom.line')
        
        result = []
        
        if context is None:
            context = {}
        data = self.read(cr, uid, ids)[0]

        if data:
            #Chercher les dates entre la date d'aujourd'hui et la date max
            dates = self.list_dates_availables(cr, uid, data['max_date'], context=context)
            #supprimer les previsions de type "suggestion de fabrication" existantes
            prevision_ids = prevision_obj.search(cr, uid, [('active','=',True),], context=context)
            prevision_obj.unlink(cr, uid, prevision_ids, context=context)

            niveau = 0
            lst_items = []
            
            while (niveau < 10):
                #Créer des FS pour les produits ayant des commandes et des Ordres de fabrication si le niveau = 0
                #Créer des FS pour les produits ayant des prévision de type Besoin suggéré si le niveau > 1
                lst_products = self.list_products_availables(cr, uid, niveau, context=context)
                if lst_products:
                    res_fs = []
                    for product in lst_products:
                        #Initialiser la prevision et le stock theorique
                        prevision = None
                        stock_theor = 0

                        exist_item = False
                        if lst_items:
                            for item in lst_items:
                                if item['product_id'] == product.id:
                                    exist_item = True
                                else:
                                    continue
                        if not lst_items or not exist_item:
                            lst_items.append({'product_id':product.id, 'stock_reel':0, 'date_max_ft': '', 'qty_four':0, 'niv_four':10, 'sum_stock_th':0, 'sum_qty_prev':0 })
                                                            
                        for date in dates:
                            #Calculer la somme des quantités des commandes si niveau = 0
                            #Calculer la somme des quantités des prévisions besoin suggéré si niveau > 0
                            qty = 0
                            if niveau == 0:
                                qty = self.sum_qty_cmd(cr, uid, date, product.id, context=context)
                            else:
                                qty = self.sum_qty_besoin_sugg(cr, uid, date, product.id, niveau, context=context)

                            #Calculer la somme des quantités des ordres de fabrications
                            qty_mrp = self.list_mrp_prod(cr, uid, date, product.id, context=None)
                            #Calculer la somme des quantités des prévisions de suggestion                           
                            qty_prev = self.sum_qty_prevision_sug(cr, uid, prevision, context=context)

                            #Calculer la somme des quantités des commandes fournisseurs
                            qty_four = 0
                            for item in lst_items:
                                if item['product_id'] == product.id:
                                    if niveau < item['niv_four']:
                                        item['niv_four'] = niveau
                                        date_max = self.date_max_suggestion(cr, uid, product.id, niveau, context=context)
                                        item['date_max_ft'] = date_max

                                    qty_four = self.sum_qty_cmd_four(cr, uid, date, product.id, context=context)
                                    if niveau == item['niv_four'] and date <= item['date_max_ft']:
                                        item['qty_four'] += qty_four
                                    else:
                                        if date == time.strftime('%Y-%m-%d'):
                                            qty_four = item['qty_four']
                                        else:
                                            qty_four = 0
                                else:
                                    continue
                            
                            #Calculer le stock theorique
                            if date == time.strftime('%Y-%m-%d'): #Première itération
                                qty_stock = self.calcul_qty_stock_reel(cr, uid, product.id, context=context)
                                for item in lst_items:
                                    if item['product_id'] == product.id:
                                        if niveau == item['niv_four']:
                                            item['stock_reel'] = qty_stock                                            
                                        else:
                                            qty_stock = item['stock_reel']
                                    else:
                                        continue
                                
                                stock_th = self.calcul_stock_theorique(cr, uid, qty_stock, qty, qty_mrp, qty_prev, qty_four, context=context)
                            else: #Reste des itérations
                                stock_th = self.calcul_stock_theorique(cr, uid, stock_theor, qty, qty_mrp, qty_prev, qty_four, context=context)                            

                            #Mettre à jour le stock reel et la quantité des commandes fournisseurs
                            for item in lst_items:
                                if item['product_id'] == product.id:
                                    if stock_th <= 0:
                                        item['stock_reel'] = 0
                                        item['qty_four'] = 0
                                    else:
                                        sum_items = item['stock_reel'] + item['qty_four']
                                        if sum_items > stock_th:
                                            diff = sum_items - stock_th
                                            if item['stock_reel'] >= diff:
                                                item['stock_reel'] -= diff
                                            else:
                                                qty = diff - item['stock_reel']
                                                item['qty_four'] -= qty
                                                item['stock_reel'] = 0
                                        else:
                                            pass

                            #Si le stock theorique est negatif, on crée une prévision de suggestion
                            if stock_th < 0:
                                #Calculer la quantité de la prévision en fonction de lot mini et multiple de
                                quantity = self.calcul_prevision_qty(cr, uid, stock_th, product, context=context)
                                
                                #Calculer la date debut de la prevision
                                start_date = self.calcul_date_prevision(cr, uid, date, quantity, product, context=context)

                                #Si il existe des prévisions qui peuvent satisfaire la quantité a créer, on ne crée pas une nouvelle prévision
                                create_prev = True
                                if not self.product_nomenclature(cr, uid, product.id, context=context):
                                    for item in lst_items:
                                        if item['product_id'] == product.id:
                                                sum_qty = self.calcul_prevision_qty(cr, uid, item['sum_stock_th'] + stock_th, product, context=context)
                                                if sum_qty <= item['sum_qty_prev']:
                                                    item['sum_stock_th'] += stock_th
                                                    stock_th = 0
                                                    create_prev = False
                                                else:
                                                    create_prev = True
                                        else:
                                            continue

                                    type_prev = 'sug_cmd_four'
                                else:
                                    type_prev = 'sug_fabrication'

                                if create_prev:
                                    prevision_id = self.create_prevision(cr, uid, product.id, quantity, start_date, date, type_prev, niveau, stock_th, '', context=context)
                                    result.append(prevision_id)
                                    res_fs.append(prevision_id)
                                    prevision_init = prevision_obj.browse(cr, uid, prevision_id, context=context)

                                    prevision = prevision_init
                                    stock_theor = stock_th
                                    for elem in lst_items:
                                        if elem['product_id'] == product.id and type_prev == 'sug_cmd_four':
                                            elem['sum_stock_th'] += stock_th
                                            elem['sum_qty_prev'] += quantity
                                        else:
                                            continue

                                else:
                                    prevision = None
                                    stock_theor = stock_th
                            else:
                                prevision = None
                                stock_theor = stock_th

                    
                    #Créer des prévisions Besoin de suggestion
                    if res_fs:
                        niveau += 1
                        res_ft = []
                        for prevision in prevision_obj.browse(cr, uid, res_fs, context=context):
                            bom_ids = self.get_product_boms(cr, uid, prevision.product_id, context=context)
                            if bom_ids:
                                for bom in bom_line_obj.browse(cr, uid, bom_ids, context=context):
                                    qty = prevision.quantity * bom.product_qty
                                    note = 'Prevision: ' + str(prevision.name) + '\n' + 'Produit: ' + str(prevision.product_id.default_code)
                                    prev_bes_sug_id = self.create_prevision(cr, uid, bom.product_id.id, qty, prevision.start_date, prevision.end_date, 'besoin_sug', niveau, 0, note, context=context)
                                    res_ft.append(prev_bes_sug_id)
                                    result.append(prev_bes_sug_id)
                        if not res_ft:
                            niveau = 10
                    else:
                        niveau = 10

        action_model = False
        data_pool = self.pool.get('ir.model.data')
        action = {}
        action_model,action_id = data_pool.get_object_reference(cr, uid, 'is_mrp', "action_mrp_prevision_form")
        
        if action_model:
            action_pool = self.pool.get(action_model)
            action = action_pool.read(cr, uid, action_id, context=context)
            action['domain'] = "[('id','in', ["+','.join(map(str,result))+"])]"
        return action
                                        
                
mrp_generate_previsions()
