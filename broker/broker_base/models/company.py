# -*- coding: utf-8 -*-

from odoo import models, fields, api

class BrokerCompany(models.Model):
    _inherit = ['res.company']
    _name = 'res.company'

    stamp = fields.Binary(string="Тамга", readonly=False)
    signature = fields.Binary(string="Гарын үсэг", readonly=False)