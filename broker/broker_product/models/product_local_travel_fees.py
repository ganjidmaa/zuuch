# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)
class ProductLocalTravelValuations(models.Model):
    _name = 'product.local.travel.valuations'
    _description = 'Product local travel valuation'
    _rec_name='valuation_format'

    valuation = fields.Integer('Үнэлгээ ₮')
    valuation_format = fields.Char(compute='_compute_valuation_format')
    type = fields.Selection([
        ('local_travel', 'Дотоод'),
        ('travel', 'Гадаад')
    ], default='local_travel', string='Төрөл')
    
    @api.depends('valuation')
    def _compute_valuation_format(self):
        for record in self:
            record.valuation_format = '{0:,.0f}'.format(record.valuation).replace(",", "'")


class ProductLocalTravelFees(models.Model):
    _name = 'product.local.travel.fees'
    _description = 'Product local travel fees'
    _rec_name='valuation_format'

    product_id = fields.Many2one('products')
    valuation_id = fields.Many2one('product.local.travel.valuations', string='Үнэлгээ ₮', domain=[('type', '=', 'local_travel')])
    valuation = fields.Integer(related='valuation_id.valuation', string='Үнэлгээ ₮')
    duration_id = fields.Many2one('local.durations', string='Хугацаа эхлэх')
    payment_fee = fields.Float('Хураамж ₮')
    valuation_format = fields.Char(compute='_compute_valuation_format')


    @api.depends('valuation')
    def _compute_valuation_format(self):
        for record in self:
            record.valuation_format = '{0:,.0f}'.format(record.valuation).replace(",", "'")


