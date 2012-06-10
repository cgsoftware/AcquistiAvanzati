# -*- encoding: utf-8 -*-

import netsvc
import pooler, tools
import math
from tools.translate import _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time


from osv import fields, osv



class costi_acc_acq(osv.osv):
    
   _name = "costi_acc_acq"
   _description = "Costi Accessori da Ripartire sulle fatture di Acquisto"
   
   _columns = {
                'name':fields.char('Descrizione', size=64, required=True, readonly=False),
                'contropartita':fields.many2one('account.account', "Contropartita di Costo", required=True),
                
                }

costi_acc_acq() 