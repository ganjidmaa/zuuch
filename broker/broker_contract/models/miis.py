# -*- coding: utf-8 -*-

from email.policy import default
from odoo import models, fields, api, _
import logging
import base64
import qrcode
import requests
import json
from requests.auth import HTTPBasicAuth
from io import BytesIO
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from datetime import date


MIIS_ENDPOINT = 'https://miis.ami.mn'
ami_username = 'cisapp'
ami_password = "uGVd6VDmUjPf"

auth_username = '51999'
auth_password = "51999@"


class Miis(models.Model):
    _name = 'miis'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Miis Contract'
    _mail_post_access = 'read'
    _order = "id desc"
    

    customer_id = fields.Many2one('res.partner', string='Даатгуулагч', domain=[('broker_type', '=', 'customer')], tracking=True)
    customer_type = fields.Selection(string='Төрөл *',
        selection=[('1', 'Хувь хүн'), ('2', 'Хуулийн этгээд'), ('3', 'Мэргэшсэн С,Д'), ('4', 'Дамжин өнгөрөх')], default='1', tracking=True)
    customer_surname = fields.Char('Овог', related='customer_id.surname')
    customer_name = fields.Char('Нэр', related='customer_id.name')
    customer_registerno = fields.Char('Регистр *')
    customer_phone = fields.Char('Утас *')
    customer_email = fields.Char('Имэйл *')
    customer_passport = fields.Char('Пасспорт №', related='customer_id.additional_info')
    customer_street = fields.Char('Гэрийн хаяг', related='customer_id.street')
    customer_street2 = fields.Char('Ажлын хаяг', related='customer_id.street2')
    customer_birthday = fields.Date('Төрсөн огноо', related='customer_id.birthday')
    customer_national = fields.Boolean('Гадаад хүн', default=False)

    product_id = fields.Many2one('products', string='Бүтээгдэхүүн', domain="[('insurance_id', '=', insurance_id), ('insurance_type_id.slug', '=', 'ajd')]", tracking=True)
    product_name = fields.Char(related='product_id.name', string='Бүтээгдэхүүн')

    contract_number = fields.Char('Гэрээний №', tracking=True)
    start_date = fields.Date('Эхлэх огноо', tracking=True, default=lambda self: date.today())
    end_date = fields.Date('Дуусах огноо', tracking=True, default=lambda self: date.today() + relativedelta(months=12))
    insurance_id = fields.Many2one('res.partner', string='Даатгагч', domain=[('broker_type', '=', 'insurance'), ('insurance_org', '!=', '0')], tracking=True)
    insurance_name = fields.Char(related='insurance_id.name', string='Даатгал')
    insurance_slug = fields.Char(related='insurance_id.slug')
    insurance_type_name = fields.Char(related='product_id.insurance_type_id.name', string='Даатгалын төрөл')

    state = fields.Selection([
        ('draft', 'Ноорог'),
        ('pending', 'АЖД-д бүртгэгдсэн'),
        ('done', 'Төлөгдсөн')
    ], default='draft', string='Төлөв', store=True, readonly=True, copy=False, tracking=True)
    user_id = fields.Many2one('res.users', string='Гэрээ хийсэн ажилтан', default=lambda self: self.env.user, tracking=True)
    user_name = fields.Char('Гэрээ хийсэн ажилтан', related='user_id.name')
    can_approve = fields.Boolean('Can Approve', compute='_compute_can_approve', default=False)
    is_limit = fields.Boolean('Хязгаарлах эсэх', default=False)
    driver_ids = fields.Many2many('res.partner', 'miis_driver_rel', 'miis_id', 'driver_id', string='Жолооч', domain=[('broker_type', '=', 'customer')], tracking=True)


    car_id = fields.Many2one('cars', string='Машин', tracking=True)
    state_number = fields.Char('Улсын дугаар *', search='_search_state_number')
    cabin_number = fields.Char('Арлын дугаар', related='car_id.cabin_number')
    imported_year = fields.Char('Орж ирсэн он', related='car_id.imported_year')
    build_year = fields.Char('Үйлдвэрлэсэн он', related='car_id.build_year')
    color = fields.Char( string='Өнгө', related='car_id.color')
    car_mark_name = fields.Char(string='Марк', related='car_id.car_mark_name')
    car_model_name = fields.Char(string='Модел', related='car_id.car_model_name')
    country_name = fields.Char(string='Үйлдвэрлэсэн улс', related='car_id.country_name')
    type = fields.Char(string='Зориулалт', related='car_id.type')
    class_name = fields.Char(string='Ангилал', related='car_id.class_name')
    motor_capacity = fields.Integer(string='Моторын багтаамж', related='car_id.motor_capacity')
    payload_capacity = fields.Integer(string='Даац', related='car_id.payload_capacity')
    seating_capacity = fields.Integer(string='Суудлын хэмжээ', related='car_id.seating_capacity')
    is_trailer = fields.Boolean('Чиргүүлтэй эсэх', store=True, tracking=True)

    miis_policy_id = fields.Char('Erp багцын ID')
    qr_code = fields.Char('QR text', compute='generate_qr_code')
    qr_image = fields.Binary('QR код')
    invoice_id = fields.Char('Төлбөрийн ID', tracking=True)
    invoice_amount = fields.Float('Төлбөрийн дүн', tracking=True)
    paid = fields.Float('Төлсөн дүн', compute='_compute_paid')
    payment_fee_percent = fields.Float('Хувь', compute='_compute_fee_percent')
    base_amount = fields.Float('Cуурь хураамжийн дүн')
    valuation = fields.Float(compute='_compute_valuation')
    invoice_key = fields.Char('Гүйлгээний утга', tracking=True)
    invoice_bank = fields.Char('Банкны нэр', tracking=True)
    invoice_account = fields.Char('Дансны дугаар', tracking=True)
    invoice_account_name = fields.Char('Данс эзэмшигчийн нэр', tracking=True)
    manually_paid_state = fields.Boolean(' ', default=False)
    download_ajd = fields.Boolean('AMI-c татсан гэрээ', default=False)
    
    
    def _search_state_number(self, operator, value):
        car_ids = self.env['cars'].search('state_number', operator, value).ids
        return [('car_id', 'in', car_ids)]

    def generate_qr_code(self):
        for record in self:
            if qrcode and base64:
                qr = qrcode.QRCode(
                    version=3,
                    error_correction=qrcode.constants.ERROR_CORRECT_H,
                    box_size=20,
                    border=10,
                )


                qr.add_data(record.qr_code)
                qr.make(fit=True)
                img = qr.make_image()
                temp = BytesIO()
                img.save(temp, format="PNG")
                qr_image = base64.b64encode(temp.getvalue())
                record.qr_image = qr_image


    @api.onchange('state')
    def _compute_can_approve(self):
        if self.env.is_superuser():
            return

        current_user = self.env.user
        is_officer = self.env.user.has_group('broker_contract.group_broker_contract_user')
        is_manager = self.env.user.has_group('broker_contract.group_broker_contract_admin')
        for record in self:
            can_approve = False
            if not is_manager:
                if(record.state == 'draft'):
                    can_approve = True
            else:
                can_approve = True
            record.can_approve = can_approve


    @api.onchange('customer_type')
    def _compute_valuation(self):
        for record in self:
            valuation = '5000000'
            if(record.customer_type == 3):
                valuation = '10000000'
            record.valuation = valuation


    @api.depends('invoice_amount')
    def _compute_paid(self):
        for record in self:
            record.paid = record.invoice_amount


    @api.depends('invoice_amount','valuation')
    def _compute_fee_percent(self):
        for record in self:
            payment_fee_percent = 0
            if(record.invoice_amount):
                payment_fee_percent = record.invoice_amount / record.base_amount

            record.payment_fee_percent = payment_fee_percent
            
    def createMiisContract(self):
        api_token = self.env['settings'].sudo().browse(1).miis_auth_token
        if(not api_token):
            error_msg = _("АЖД системд гэрээ илгээх явцад алдаа гарлаа.")
            self.env.user.notify_warning(message=error_msg)
            return True

        headers = {
            "Content-type": "application/json",
            "Authorization": 'Bearer '+ api_token
        }


        borrowerList = []
        if(self.is_limit):
            for driver in self.driver_ids:
                borrowerList.append({
                    "phoneNumber": driver.phone,
                    "registerNumber": driver.registerno,
                    "email": driver.email
                })

        payload = {
            "phoneNumber": self.customer_phone,
            "registerNumber": self.customer_registerno,
            "email": self.customer_email,
            'insuranceCompanyId': self.insurance_id.insurance_org,
            "policyType": self.customer_type,
            "policyMonth": 1,
            "plateNumber": self.state_number if self.state_number else '',
            "isLimit": self.is_limit,
            "borrowerList": borrowerList,
        }

        response = requests.post(MIIS_ENDPOINT+'/admin/insurance/insuree/api', headers=headers, data=json.dumps(payload))
        response_data = response.json()    
        status_code = response.status_code

        if(status_code == 200 and response_data['status'] != 'Failed'):
            car_data = response_data['data']['vehicleInfo']
            insurer_data = response_data['data']['insureeInfo'] 
            co_borrowers = response_data['data']['coBorrower'] if len(borrowerList) > 0 else None

            car = self.env['cars'].search([('state_number', '=', car_data['plateNumber'])], limit=1)
            if(not car):
                car = self.env['cars'].create({
                    'state_number': car_data['plateNumber'],
                    'cabin_number': car_data['cabinNumber'],
                    'build_year': car_data['buildYear'],
                    'imported_year': car_data['importDate'],
                    'color': car_data['colorName'],
                    'car_mark_name': car_data['markName'],
                    'car_model_name': car_data['modelName'],
                    'country_name': car_data['countryName'],
                    'type': car_data['fueltype'],
                    'class_name': car_data['className'],
                    'motor_capacity': car_data['capacity'],
                    'payload_capacity': car_data['mass'],
                    'seating_capacity': car_data['manCount'],
                })
            self.car_id = car.id


            insurer = self.env['res.partner'].search([('registerno', '=', insurer_data['registerNumber'])], limit=1)
            if(not insurer):
                insurer = self.env['res.partner'].create({'name': insurer_data['name']})

            insurer.write({
                'broker_type': 'customer',
                'is_company': True if self.customer_type == '2' else False,
                'surname': insurer_data['lastname'],
                'name': insurer_data['name'],
                'registerno': insurer_data['registerNumber'],
                'phone': self.customer_phone,
                'email': self.customer_email,
                'street': insurer_data['address']
            })

            if(self.is_limit and co_borrowers):
                for driver in self.driver_ids:
                    for co_borrower in co_borrowers:
                        if(co_borrower['registerNumber'] == driver.registerno):
                            driver.write({
                                'broker_type': 'customer',
                                'surname': co_borrower['lastName'],
                                'name': co_borrower['firstName'],
                                'registerno': co_borrower['registerNumber'],
                                'phone': co_borrower['phoneNumber'],
                                'email': co_borrower['email'],
                                'street': co_borrower['address']
                            })

            self.customer_id = insurer.id
            self.state = 'pending'
            self.miis_policy_id = response_data['data']['policyId']

            self.env.user.notify_success(message='Мэдээлэл татагдалаа.')
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        else:
            error_msg = response_data['text']
            return self.env.user.notify_warning(message=error_msg)


    def getPaymentQr(self):
        api_token = self.env['settings'].sudo().browse(1).miis_auth_token
        if(not api_token):
            error_msg = _("АЖД системээс төлбөрийн мэдээлэл татах явцад алдаа гарлаа.")
            self.env.user.notify_warning(message=error_msg, title='Анхааруулга!')
            return True

        headers = {
            "Content-type": "application/json",
            "Authorization": 'Bearer '+ api_token
        }
        
        payload = {
            "policyId": self.miis_policy_id,
            "policyMonth": 1 if self.customer_type == '4' else 0,
            "isLie": False,
            'isChirguul': self.is_trailer
        }

        response = requests.post(MIIS_ENDPOINT+'/admin/insurance/insuree/calc', headers=headers, data=json.dumps(payload))
        response_data = response.json()
        status_code = response.status_code
        status = response_data['text']
        
        if(status_code == 200 and status == 'Тооцоолол амжилттай'):
            self.qr_code = response_data['data']['invoice']['qr_code']
            self.invoice_id = response_data['data']['invoice']['id']
            self.invoice_amount = response_data['data']['invoice']['invoiceAmount']
            self.base_amount = response_data['data']['base']
            self.invoice_key = response_data['data']['invoice']['invoiceKey']
            self.invoice_account = response_data['data']['invoice']['invoiceAccount']
            self.invoice_account_name = response_data['data']['invoice']['invoiceAccountName']
            self.invoice_bank = response_data['data']['invoice']['invoiceBank']

            self.generate_qr_code()
            self.env.user.notify_success(message=status)
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        else:
            return self.env.user.notify_warning(message=status)

    def payPaymentFn(self): 
        api_token = self.env['settings'].sudo().browse(1).miis_auth_token
        if(not api_token):
            error_msg = _("АЖД системээс төлбөрийн мэдээлэл татах явцад алдаа гарлаа.")
            return self.env.user.notify_warning(message=error_msg, title='Анхааруулга!')

        headers = {
            "Content-type": "application/json",
            "Authorization": 'Bearer '+ api_token
        }

        try:
            invoice_id = self.invoice_id
            response = requests.get(MIIS_ENDPOINT+'/admin/paid/invoice?invoiceId='+invoice_id, headers=headers)
            response_data = response.json()

            status_code = response.status_code
            status = response_data['status']

            if(status_code == 200 and status == 'Success'):
                self.manually_paid_state = True
                self.checkPaymentStatus()
            elif(response_data['status'] == 'Failed'):
                messageText = response_data['text'] if response_data['text'] else response_data['msgList'][0]['params']['reason']
                return self.env.user.notify_danger(message=messageText, title='Анхааруулга!')
        except IOError:
            error_msg = _("Төлбөрийн мэдээлэл шалгах явцад алдаа гарлаа.")
            return self.env.user.notify_warning(message=error_msg)


    def checkPaymentStatus(self):
        api_token = self.env['settings'].sudo().browse(1).miis_auth_token
        if(not api_token):
            error_msg = _("АЖД системээс төлбөрийн мэдээлэл шалгах явцад алдаа гарлаа.")
            self.env.user.notify_warning(message=error_msg)
            return True

        headers = {
            "Content-type": "application/json",
            "Authorization": 'Bearer '+ api_token
        }

        try:
            policy_id = self.miis_policy_id
            response = requests.post(MIIS_ENDPOINT+'/admin/insurance/insuree/checkpay/'+policy_id, headers=headers)
            response_data = response.json()
            status_code = response.status_code
            status = response_data['status']

            if(status_code == 200 and status == 'Success'):
                policy = response_data['data']['policy']
                self.state = 'done'
                self.contract_number = policy['policyNumber']
                self.message_post(
                    body=policy['pdfContract'],
                    subject="Гэрээний хавсралт файл."
                )
                self.env.user.notify_success(message=response_data['text'])
                return {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
            elif(response_data['status'] == 'Failed'):
                return self.env.user.notify_danger(message=response_data['text'])
        except IOError:
            error_msg = _("Төлбөрийн мэдээлэл шалгах явцад алдаа гарлаа.")
            return self.env.user.notify_warning(message=error_msg)
        

    def get_miis_auth_token(self):
        payload = {
            "username": auth_username,
            "password": auth_password,
            "grant_type": "password"
        }

        try:
            response = requests.post(MIIS_ENDPOINT+'/uaa/oauth/token', auth=HTTPBasicAuth(ami_username, ami_password), data=payload)
            data = response.json()
            status_code = response.status_code

            if(status_code == 200):
                api_token = data['access_token']
                settings = self.env['settings'].sudo().browse(1)
                settings.write({'miis_auth_token': api_token})
        except IOError:
            error_msg = _("--------------ERROR WHEN GET MIIS AUTH TOKEN------------.")
            logging.error(error_msg)


    def unlink(self):
        for record in self:
            if record.can_approve == False:
                raise UserError(f"Зөвхөн 'Ноорог' төлөвтэй гэрээг устгах боломжтой.")
      
        return super(Miis, self).unlink()