# -*- coding: utf-8 -*-
from odoo import models, fields, api
        
class Travel(models.Model):
    _name = 'travels'
    _description = 'Broker Travel'
    
    passport = fields.Char('Гадаад пасспорт')
    country_zone_id = fields.Many2one('country.zones', string='Аялах чиглэл')
    duration_id = fields.Many2one('durations', string='Хугацаа')
    local_duration_id = fields.Many2one('local.durations', string='Аялах хугацаа')
    local_duration = fields.Integer(string='Хугацаа хоногоор')
    exchange_rate = fields.Integer('Ханш')
    travel_date = fields.Date('Аялах огноо')
    is_family = fields.Boolean('Гэр бүлээрээ эсэх')
    purpose = fields.Char('Аяллын зорилго')
    country = fields.Char('Аялах улс')

