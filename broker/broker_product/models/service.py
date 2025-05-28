# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)
class Service(models.Model):
    _name = 'services'
    _description = 'Services'

    name = fields.Char('Нэмэлт үйлчилгээ, хамгаалалт')
    desc = fields.Text(string='Тайлбар')


