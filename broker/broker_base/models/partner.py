# -*- coding: utf-8 -*-
import re
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime

class BrokerPartner(models.Model):
    _inherit = ['res.partner']
    _name = 'res.partner'
    _rec_name = 'display_name'
    _rec_names_search = ['registerno']

    broker_type = fields.Selection([
        ('insurance', 'Даатгал'),
        ('customer', 'Харилцагч')
    ], string='Төрөл')

    surname = fields.Char('Овог', required=False)
    name = fields.Char('Нэр', required=False)
    registerno = fields.Char('Регистр') 
    insurance_org = fields.Integer('АЖД-н API code')
    miis_code = fields.Integer('АЖД-н ID')
    driver_license = fields.Char('Жолооны үнэмлэх')
    birthday = fields.Date('Төрсөн огноо', compute='compute_birthday', store=True)
    age = fields.Char('Нас', compute='compute_age')
    gender = fields.Char('Хүйс', compute='compute_gender', store=True)
    image_1920 = fields.Binary(string="Лого", readonly=False)
    stamp = fields.Binary(string="Тамга", readonly=False)
    slug = fields.Char('Таних тэмдэг')
    passport_no = fields.Char('Гадаад пасспорт')

    def _compute_display_name(self):
        for record in self:
            # Customize the display name logic here
            if record.registerno:
                record.display_name = f"{record.name} - {record.registerno}"
            else:
                record.display_name = record.name

    @api.depends('registerno')
    def compute_birthday(self):
        for record in self:
            """Compute the age based on the registration number."""
            register = record.registerno.strip() if record.registerno else ''
            if len(register) != 10:
                continue
    
            year = register[2:4]
            month = register[4:6]
            day = register[6:8]

            # Determine birth year and correct month
            if month[0] >= "2":  # If the first digit of the month is >= 2, assume 2000s
                birth_year = "20" + year
                corrected_month = str(int(month[0]) - 2) + month[1]  # Correct month
                birth_date_str = f"{birth_year}-{corrected_month}-{day}"
            else:  # Otherwise, assume 1900s
                birth_year = "19" + year
                birth_date_str = f"{birth_year}-{month}-{day}"

            try:
                birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d')
            except ValueError:
                logging.error(f"Invalid date format for registration number: {register}")
                continue

            record.birthday = birth_date


    @api.depends('birthday')
    def compute_age(self):
        for record in self:
            if(record.birthday):
                birth_year = record.birthday.strftime('%Y')
           
                age = int(datetime.now().year) - int(birth_year)
                self.age = age
            else:
                self.age = 0


    @api.depends('registerno')
    def compute_gender(self):  
        for record in self: 
            register = record.registerno.strip() if record.registerno else ''
            if len(register) != 10:
                continue

            tegsh = [0, 2, 4, 6, 8]
            for num in tegsh:
                if register[-2] == str(num):
                    record.gender = 'female'
                    break
                else:
                    record.gender = 'male'
            else:
                record.gender = 'male'