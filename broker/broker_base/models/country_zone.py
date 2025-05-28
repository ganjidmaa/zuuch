# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CountryZone(models.Model):
    _name = 'country.zones'
    _description = 'Country Zone'

    name = fields.Char('Аялах чиглэл')
    value = fields.Char('Аялах чиглэл латин')

class Duration(models.Model):
    _name = 'durations'
    _description = 'Хугацаа'

    name = fields.Char('Хугацаа')
    value = fields.Char('Хугацаа')
    
class LocalDuration(models.Model):
    _name = 'local.durations'
    _description = 'Хугацаа'

    name = fields.Char('Хугацаа')
    value_min = fields.Integer('Хугацаа')
    value_max = fields.Integer('Хугацаа')
    