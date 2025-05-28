# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)
class ProductRisk(models.Model):
    _name = 'product.risks'
    _description = 'Product risks'

    product_id = fields.Many2one('products')
    contract_id = fields.Many2one('contracts')
    insurance_type_slug = fields.Char(related='product_id.insurance_type_slug')
    risk_id = fields.Many2one('risks')
    valuation_id = fields.Many2one('product.local.travel.valuations', string='Үнэлгээ')
    valuation = fields.Integer('Үнэлгээ $', related='valuation_id.valuation')
    is_optional = fields.Boolean('Сонголтот эрсдэл эсэх', compute='_commpute_is_risk_optional', store=True)
    duty_liable_percent = fields.Integer('Хамгаалах хувь', default='100')
    duty_liable_amount = fields.Integer('Хамгаалах дүн', default='0')
    risk_name = fields.Char(related='risk_id.name')
    coverage_total_amount = fields.Integer(compute='_compute_coverage_total_amount')

    @api.onchange('risk_id')
    def _commpute_is_risk_optional(self):
        for record in self:
            record.is_optional = record.risk_id.is_optional

    @api.onchange('duty_liable_amount')
    def change_duty_percent(self):
        if(self.duty_liable_amount > 0):
            self.duty_liable_percent = 0

    @api.onchange('duty_liable_percent')
    def change_duty_amount(self):
        if(self.duty_liable_percent > 0):
            self.duty_liable_amount = 0

    @api.onchange('duty_liable_amount', 'duty_liable_percent')
    def _compute_coverage_total_amount(self):
        for record in self:
            coverage_total_amount = 0
            if(record.valuation and record.duty_liable_percent):
                duty_amount = (record.valuation * record.duty_liable_percent) / 100
                coverage_total_amount = duty_amount
            else:
                coverage_total_amount = record.duty_liable_amount

            record.coverage_total_amount = coverage_total_amount




