# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)
class InsuranceType(models.Model):
    _name = 'insurance.types'
    _description = 'Insurance Types'

    name = fields.Char('Даатгалын төрөл')
    slug = fields.Char('Төрөл')
    status = fields.Boolean('Төлөв')
    tapatrip_code = fields.Integer('Тапатрип код')


