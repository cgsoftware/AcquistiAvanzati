# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from lxml import etree
import decimal_precision as dp

import netsvc
import pooler
from osv import fields, osv, orm
from tools.translate import _


class account_invoice_acc(osv.osv):
    _name="account.invoice_acc"
    _columns={
              'account_invoice_id':fields.many2one('account.invoice', 'Fattura Testata', required=True),
              'costo_acc_id':fields.many2one('costi_acc_acq', 'Costo', required=True),
              'costo_acc': fields.float('Costo', required=True, digits_compute= dp.get_precision('Account')), 
              }

account_invoice_acc()

class account_invoice(osv.osv):
    
    def _get_journal(self, cr, uid, context=None):
        if context is None:
            context = {}
        if False:
            # qui fa lo standard
            type_inv = context.get('type', 'out_invoice')
            user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
            company_id = context.get('company_id', user.company_id.id)
            type2journal = {'out_invoice': 'sale', 'in_invoice': 'purchase', 'out_refund': 'sale_refund', 'in_refund': 'purchase_refund'}
            refund_journal = {'out_invoice': False, 'in_invoice': False, 'out_refund': True, 'in_refund': True}
            journal_obj = self.pool.get('account.journal')
            res = journal_obj.search(cr, uid, [('type', '=', type2journal.get(type_inv, 'sale')),
                                            ('company_id', '=', company_id),
                                            ('refund_journal', '=', refund_journal.get(type_inv, False))],
                                                limit=1)
        else:
            type_inv = context.get('type', 'out_invoice')
            user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
            company_id = context.get('company_id', user.company_id.id)
            type2journal = {'out_invoice': 'sale', 'in_invoice': 'purchase', 'out_refund': 'sale_refund', 'in_refund': 'purchase_refund'}
            refund_journal = {'out_invoice': False, 'in_invoice': False, 'out_refund': True, 'in_refund': True}
            journal_obj = self.pool.get('account.journal')
            res = journal_obj.search(cr, uid, [
                                            ('company_id', '=', company_id)
                                            ]
                                                )
            
        return res and res[0] or False    
    
    def _total_costi_acc(self, cr, uid, ids, name, args, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            res[invoice.id] = {
                'totale_costi': 0.0,
            }
            for line in invoice.costi_acc_ids:
                res[invoice.id]['totale_costi'] += line.costo_acc
            if res[invoice.id]['totale_costi'] <> 0:
                totqta = 0
                for riga_art in invoice.invoice_line:
                    totqta += riga_art.quantity
                if totqta>0:
                    costa_r = res[invoice.id]['totale_costi']/totqta
                    for riga_art in invoice.invoice_line:
                        ok = self.pool.get('account.invoice.line').write(cr,uid,[riga_art.id],{'costo_acc_rip':costa_r})                    
        return res
    

    def _get_invoice_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()

    def _get_invoice_tax(self, cr, uid, ids, context=None):
        result = {}
        for tax in self.pool.get('account.invoice.tax').browse(cr, uid, ids, context=context):
            result[tax.invoice_id.id] = True
        return result.keys()
    
    
    def _amount_all(self, cr, uid, ids, name, args, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            res[invoice.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0
            }
            for line in invoice.invoice_line:
                res[invoice.id]['amount_untaxed'] += line.price_subtotal
            for line in invoice.tax_line:
                res[invoice.id]['amount_tax'] += line.amount
            res[invoice.id]['amount_total'] = res[invoice.id]['amount_tax'] + res[invoice.id]['amount_untaxed']
        return res

    
    _inherit = 'account.invoice' 
    _columns={
              'costi_acc_ids':fields.one2many('account.invoice_acc', 'account_invoice_id', 'Costi Accessori', required=False),
              'totale_costi': fields.function(_total_costi_acc, method=True, type='float' ,digits_compute=dp.get_precision('Account'), string='Totale Costi Accessori', store=True,multi='all'),
              'amount_untaxed': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Untaxed',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),
              'amount_tax': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Tax',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),
              'amount_total': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Total',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),
              
              }
    
 #   def action_move_create(self, cr, uid, ids, *args):

 #       """Creates invoice related analytics and financial move lines"""
 #       return True
    
    
 #   def pay_and_reconcile(self, cr, uid, ids, pay_amount, pay_account_id, period_id, pay_journal_id, writeoff_acc_id, writeoff_period_id, writeoff_journal_id, context=None, name=''):
 #       if context is None:
 #           context = {}
 #       return True

account_invoice()


class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line' 
    _columns={
              'costo_acc_rip': fields.float('Costo Accessorio Ripartito', required=False, digits_compute= dp.get_precision('Account')),
              }
account_invoice_line()
    