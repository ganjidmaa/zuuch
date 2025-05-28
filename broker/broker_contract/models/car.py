# -*- coding: utf-8 -*-

from email.policy import default
from odoo import models, fields, api


class Car(models.Model):
    _name = 'cars'
    _description = 'Broker Car'
    
    state_number = fields.Char('Улсын дугаар')
    cabin_number = fields.Char('Арлын дугаар')
    imported_year = fields.Char('Орж ирсэн он')
    build_year = fields.Char('Үйлдвэрлэсэн он')
    color = fields.Char( string='Тээврийн хэрэгсэлийн өнгө')
    car_mark_name = fields.Char(string='Марк')
    car_model_name = fields.Char(string='Модел')
    country_name = fields.Char(string='Үйлдвэрлэсэн улс')
    type = fields.Char(string='Зориулалт')
    class_name = fields.Char(string='Ангилал')
    motor_capacity = fields.Integer(string='Моторын багтаамж')
    payload_capacity = fields.Integer(string='Даац')
    seating_capacity = fields.Integer(string='Суудлын хэмжээ')
    certificate_number = fields.Char(string='Гэрчилгээний дугаар')
    is_trailer = fields.Boolean('Чиргүүлтэй эсэх', default=False)

