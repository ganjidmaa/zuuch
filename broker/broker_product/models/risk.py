# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)
class Risk(models.Model):
    _name = 'risks'
    _description = 'Risks'

    name = fields.Char('Даатгалын эрсдэл')
    is_optional = fields.Boolean('Сонголтот эсэх')
    desc = fields.Text(string='Тайлбар')


