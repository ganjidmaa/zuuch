# -*- coding: utf-8 -*-

from email.policy import default
from odoo import models, fields, api


class Settings(models.Model):
    _name = 'settings'
    _description = 'Settings'
    
    miis_auth_token = fields.Char('Албан журмын API токен')
    mongol_auth_token = fields.Char('Монгол даатгалын токен')
    agula_auth_token = fields.Char('Агула даатгалын токен')
    last_contract_number = fields.Char('Хамгийн сүүлийн дэс дугаар', default=1)