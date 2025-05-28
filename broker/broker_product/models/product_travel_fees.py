# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)
class ProductTravelFees(models.Model):
    _name = 'product.travel.fees'
    _description = 'Product travel fees'
    _rec_name = 'valuation_format'

    product_id = fields.Many2one('products')
    country_zone_id = fields.Many2one('country.zones', string='Бүс')
    duration_id = fields.Many2one('durations', string='Хугацаа')
    valuation_id = fields.Many2one('product.local.travel.valuations', string='Үнэлгээ $', domain=[('type', '=', 'travel')])
    valuation = fields.Integer('Үнэлгээ $', related='valuation_id.valuation')
    payment_fee = fields.Float('Хураамж $')
    has_family_fee = fields.Boolean('Гэр бүл эсэх', default=False)
    family_fee = fields.Float('Гэр бүлийн хураамж $')
    duration = fields.Char(related='duration_id.value')
    country_zone = fields.Char(related='country_zone_id.value')
    country_zone_name = fields.Char(related='country_zone_id.name')
    valuation_format = fields.Char(compute='_compute_valuation_format')

    @api.depends('valuation')
    def _compute_valuation_format(self):
        for record in self:
            record.valuation_format = '{0:,.0f}'.format(record.valuation).replace(",", "'")
