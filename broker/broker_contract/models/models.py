# -*- coding: utf-8 -*-
import logging
import base64
import requests
import json
import base64
from io import BytesIO
from requests.auth import HTTPBasicAuth
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
from xmlrpc import client as xmlrpclib
import os
from datetime import date

# import qrcode
# import zlib
# from PIL import Image


_logger = logging.getLogger(__name__)

MONGOL_ENDPOINT = 'https://mobile.mongoldaatgal.mn:8084/api/v1/online/'
mongol_broker_no = '1000090002'
mongol_broker_terminal_no = "12324"

PRTL_ENDPOINT = 'http://66.181.175.50'
PRTL_PORT = '8005'
prtl_username = 'DIGITAL_ZUUCH'
prtl_password = "2o*D{/UCP2s8"
prtl_db_name = "pderp"
prtl_model_name = "pd.api"
# prtl_broker_id = "18374"

NOMIN_ENDPOINT = 'https://ins.nomin.mn'
NOMIN_PORT = ''
nomin_username = 'insur'
nomin_password = "insur123"
nomin_db_name = "nominerp"
nomin_model_name = "nomin.api"

ARD_ENDPOINT = 'http://43.231.115.165:8090/api/Guarantee/Invoice'
ard_api_key = 'GS8CjmdpaO'

AGULA_ENDPOINT = 'https://emb.agula.mn/api/v1'
# AGULA_ENDPOINT = 'https://emb-dev.agula.mn/api/v1'
agula_username = 'suregkharaatsai'
agula_password = 'ppbwkfRCuiCFcsHGsfVFc8'
# agula_password = 'Ywgt4DBQHiwEyjzPxsCN'

MUNKH_ENDPOINT = 'https://testapi.munkh.mn/api/Guarantee/Invoice'
munkh_apikey = '0BeT6qooV1' 

MIG_ENDPOINT = 'https://testapi.munkh.mn/api/Guarantee/Invoice'
mig_apikey = '0BeT6qooV1' 

class Contract(models.Model):
    _name = 'contracts'
    _rec_name = 'contract_number'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Broker Contracts'
    _mail_post_access = 'read'
    _order = "id desc"

    active = fields.Boolean('Active', default=True)

    product_id = fields.Many2one('products', string='Бүтээгдэхүүн', domain="[('insurance_id', '=', insurance_id), ('insurance_type_id.slug', '!=', 'ajd')]", tracking=True)
    erp_product_id = fields.Char(related='product_id.erp_product_id')
    product_name = fields.Char(related='product_id.name', string='Бүтээгдэхүүн')
    valuation_range = fields.Char('Хязгаарлалт', compute="_compute_valuation_range")

    insurance_type_id = fields.Many2one('insurance.types', string='Даатгалын төрөл', related='product_id.insurance_type_id', store=True, tracking=True)
    insurance_type_slug = fields.Char(related='insurance_type_id.slug', string='Даатгалын тэмдэг', store=True)
    insurance_type_name = fields.Char(related='insurance_type_id.name', string='Даатгалын төрөл')

    travel_fees = fields.Many2one('product.travel.fees', string='Хамгаалалт',  store=True)
    local_travel_fees = fields.Many2one('product.local.travel.fees', string='Хамгаалалтууд', domain="[('id', '=', False)]", store=True)
    
    contract_number = fields.Char('Гэрээний №', tracking=True)
    start_date = fields.Date('Эхлэх огноо', tracking=True, default=lambda self: date.today())
    end_date = fields.Date('Дуусах огноо', tracking=True)
    insurance_id = fields.Many2one('res.partner', string='Даатгагч', domain=[('broker_type', '=', 'insurance')], tracking=True)
    insurance_slug = fields.Char(related='insurance_id.slug')
    insurance_name = fields.Char(related='insurance_id.name')

    sent_contract_erp = fields.Boolean('Даатгалын системд гэрээ бичсэн эсэх', tracking=True, default=False)
    

    customer_id = fields.Many2one('res.partner', string='Даатгуулагч', domain=[('broker_type', '=', 'customer')], tracking=True, _rec_name='registerno')
    customer_type = fields.Selection(string='Төрөл',
        selection=[('person', 'Хувь хүн'), ('company', 'Хуулийн этгээд')], related='customer_id.company_type')
    customer_surname = fields.Char('Овог', related='customer_id.surname')
    customer_name = fields.Char('Нэр', related='customer_id.name')
    customer_age = fields.Char('Нас', related='customer_id.age')
    customer_registerno = fields.Char('Регистр', related='customer_id.registerno')
    customer_phone = fields.Char('Утас', related='customer_id.phone')
    customer_email = fields.Char('Имэйл', related='customer_id.email')
    customer_passport = fields.Char('Пасспорт №', related='customer_id.passport_no')
    customer_street = fields.Char('Гэрийн хаяг', related='customer_id.street')
    customer_street2 = fields.Char('Ажлын хаяг', related='customer_id.street2')
    customer_birthday = fields.Date('Төрсөн огноо', related='customer_id.birthday')

    emergency_contact_id = fields.Many2one('res.partner', string='Яаралтай үед холбоо барих', domain=[('broker_type', '=', 'customer')], tracking=True)
    emergency_contact_type = fields.Selection(string='Холбоо барих хүний төрөл',
        selection=[('person', 'Хувь хүн'), ('company', 'Компани')])
    emergency_contact_surname = fields.Char('Яаралтай үед холбоо барих Овог', related='emergency_contact_id.surname')
    emergency_contact_name = fields.Char('Яаралтай үед холбоо барих Нэр', related='emergency_contact_id.name')
    emergency_contact_registerno = fields.Char('Яаралтай үед холбоо барих Регистр', related='emergency_contact_id.registerno')
    emergency_contact_phone = fields.Char('Яаралтай үед холбоо барих Утас', related='emergency_contact_id.phone')
    emergency_contact_email = fields.Char('Яаралтай үед холбоо барих Имэйл', related='emergency_contact_id.email')
    emergency_contact_street = fields.Char('Яаралтай үед холбоо барих Хаяг', related='emergency_contact_id.street')
    emergency_contact_birthday = fields.Date('Яаралтай үед холбоо барих Төрсөн огноо', related='emergency_contact_id.birthday')

    user_id = fields.Many2one('res.users', string='Гэрээ хийсэн ажилтан', default=lambda self: self.env.user, tracking=True)
    user_name = fields.Char('Гэрээ хийсэн ажилтан', related='user_id.name')
    state = fields.Selection([
        ('draft', 'Ноорог'),
        ('paid', 'Төлөгдсөн'),
        ('sent', 'ERP Гэрээ бичсэн'),
    ], default='draft', string='Төлөв', store=True, readonly=True, copy=False, tracking=True)
    valuation = fields.Float('Үнэлгээ', tracking=True)
    has_covid_protect = fields.Boolean('Ковидын хамгаалалт', tracking=True)
    payment = fields.Float('Төлбөр', tracking=True)
    risk_payment = fields.Float('Нэмэлт эрсдэлийн төлбөр', tracking=True)
    discount_amount = fields.Float('Хөнгөлөлт', tracking=True)
    total_payment = fields.Float('Нийт төлбөр', tracking=True)
    customer_duty_liable_amount = fields.Float('Өөрийн хариуцах дүн', related='product_id.customer_duty_liable_amount')
    customer_duty_liable_type = fields.Selection([
        ('percent', 'Хувь'),
        ('amount', 'Дүн')
    ], string='Өөрийн хариуцах төрөл', related='product_id.customer_duty_liable_type')  
    payment_fee_percent = fields.Float('Хураамжийн хувь', related='product_id.payment_fee_percent', store=True, tracking=True)
    travel_fee_percent = fields.Float('Хураамж $', store=True)
    additional_risk_payment = fields.Float('Нэмэлт эрсдэл', tracking=True)
    payment_type = fields.Integer('Төлбөрийн төрөл')
    payment_condition = fields.Integer('Төлбөрийн нөхцөл')
    paid = fields.Float('Төлсөн дүн', tracking=True)
    cancel_reason = fields.Char('Буцаасан шалтгаан')
    cancel_amount = fields.Char('Буцаасан дүн')
    cancel_account = fields.Char('Буцаасан данс')
    cancel_has_fee = fields.Char('Цуцлахад хураамж авах эсэх')
    cancel_has_referee = fields.Char('Цуцлахад хураамж буцаасан эсэх')
    cancel_date = fields.Date('Буцаасан огноо')

    can_approve = fields.Boolean(
        'Can Approve', compute='_compute_can_approve', default=False)

    bank_name = fields.Char(compute='compute_insurance_bank_name')
    account_number = fields.Char(compute='compute_insurance_bank_name')
    account_holder_name = fields.Char(compute='compute_insurance_bank_name')

    contract_pdf_id = fields.Many2one('ir.attachment', string="Гэрээ", copy=False, public=True)

    car_id = fields.Many2one('cars', string='Машин', tracking=True)
    state_number = fields.Char('Улсын дугаар', related='car_id.state_number', search='_search_state_number')
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
    is_trailer = fields.Boolean('Чиргүүлтэй эсэх', related='car_id.is_trailer')

    is_limit = fields.Boolean('Хязгаарлах эсэх', default=False, tracking=True)
    driver_ids = fields.Many2many('res.partner', 'contract_driver_rel', 'contract_id', 'driver_id', domain=[('broker_type', '=', 'customer')], string='Жолооч', tracking=True)
    health_id = fields.Many2one('healths', 'Эрүүл мэнд')
    travel_people = fields.Many2many('res.partner', 'contract_travel_rel', 'contract_id', 'people_id', string='Аялагчийн мэдээлэл', tracking=True)
    travel_people_count = fields.Integer(compute="_compute_people_count")
    travel_id = fields.Many2one('travels', 'Аялал', tracking=True)
    passport = fields.Char('Гадаад пасспорт', related='travel_id.passport')
    country_zone_id = fields.Many2one('country.zones', related='travel_id.country_zone_id', string='Аялах чиглэл')
    country = fields.Char('Аялах улс', related='travel_id.country')
    duration_id = fields.Many2one('durations', string='Хугацаа', related='travel_id.duration_id')
    local_duration_id = fields.Many2one('local.durations', string='Аялах хугацаа', related='travel_id.local_duration_id')
    local_duration = fields.Integer('Хугацаа', related='travel_id.local_duration')
    exchange_rate = fields.Integer('Ханш')
    travel_date = fields.Date('Аялах огноо', related='travel_id.travel_date')
    is_family = fields.Boolean(related='travel_id.is_family')
    purpose = fields.Char(related='travel_id.purpose')
    property_id = fields.Many2one('properties', 'Эд хөрөнгө')

    erp_invoice_id = fields.Char('Нэхэмжлэхийн ID', tracking=True)
    erp_customer_id = fields.Char('Даатгуулагчийн ID', tracking=True)
    erp_contract_url = fields.Char('Даатгалын гэрээ линк', tracking=True)
    erp_contract_id = fields.Char('Erp гэрээний ID', tracking=True)
    erp_contract_number = fields.Char('Erp гэрээний №', tracking=True)
    erp_policy_id = fields.Char('Erp багцын ID', tracking=True)
    erp_state = fields.Selection([
        ('draft', 'Үгүй'),
        ('sent', 'Тийм')
    ], string='ERP системд илгээсэн', default='draft', tracking=True)
    qr_code = fields.Char('QR text', compute='generate_qr_code', store=True)
    qr_image = fields.Binary('QR код')

    is_email_sent = fields.Boolean('Имэйл илгээсэн эсэх', default=False)
    is_restored = fields.Boolean('Нөхөж хийсэн эсэх', default=False)

    @api.depends('product_id')
    def _compute_valuation_range(self):
        for record in self:
            valuation_range = ''
            if(record.product_id):
                valuation_min_limit = '{:,}'.format(record.product_id.valuation_min_limit)
                valuation_max_limit = '{:,}'.format(record.product_id.valuation_max_limit)
                valuation_range = str(valuation_min_limit) + ' - ' + str(valuation_max_limit)

            record.valuation_range = valuation_range


    @api.onchange('travel_people')
    def _compute_people_count(self):
        for record in self:
            record.travel_people_count = len(record.travel_people) if len(record.travel_people) else 1

    @api.onchange('insurance_id')
    def compute_insurance_bank_name(self):
        for record in self:
            partner_account = self.env['res.partner.bank'].search([('partner_id', '=', record.insurance_id.id)], limit=1)

            record.bank_name = partner_account.bank_id.name
            record.account_number = partner_account.acc_number
            record.account_holder_name = partner_account.acc_holder_name


    @api.onchange('insurance_type_id')
    def get_current_exchange_price(self):
        for record in self:
            currency = 0
            if record.insurance_type_slug == 'travel':
                currency_rate = requests.get('https://monxansh.appspot.com/xansh.json?currency=USD') 
                resp_content = currency_rate.content.decode("utf-8")
                data = json.loads(resp_content)
                currency = data[0]['rate_float']
            record.exchange_rate = currency


    @api.onchange('valuation')
    def valuation_range_warning(self):
        for record in self:
            min_limit = record.product_id.valuation_min_limit
            max_limit = record.product_id.valuation_max_limit

            if(record.valuation and min_limit != 0 and max_limit != 0):
                if(record.valuation < min_limit or record.valuation > max_limit):
                    record.valuation = 0
                    self.env.user.notify_danger(message='Үнэлгээний хязгаарлалтад багтаана уу!', title='Анхааруулга!')


    @api.onchange('payment_fee_percent', 'valuation', 'additional_risk_payment', 'exchange_rate', 'has_covid_protect', 'travel_people', 'travel_fee_percent')
    def compute_payment(self):
        for record in self:
            computed_payment = False
            people_count = record.travel_people_count

            if(record.insurance_type_slug not in ['travel', 'local_travel'] and record.valuation and record.payment_fee_percent):
                payment = (record.valuation * ((record.payment_fee_percent + record.additional_risk_payment) / 100)) 
                computed_payment = True

            if(record.insurance_type_slug == 'travel' and record.exchange_rate > 0):
                payment = record.travel_fee_percent * record.exchange_rate * people_count
                if(record.has_covid_protect):
                    payment = payment + (payment * 10) / 100
                computed_payment = True
            elif(record.insurance_type_slug == 'local_travel'):
                payment = record.travel_fee_percent * people_count
                computed_payment = True

            if(computed_payment):  
                record.payment = payment


    @api.onchange('payment', 'discount_amount')
    def compute_discount(self):
        for record in self:
            discount_amount = record.discount_amount
            if(record.payment):
                # if (record.product_id.discount_type == 'percent'): 
                #     discount_amount = (record.payment * record.discount_amount / 100) 
                #     record.discount_amount = discount_amount
                # else:
                    # discount_amount = record.product_id.discount_amount 
                    # record.discount_amount = discount_amount

                record.total_payment = record.payment - discount_amount


    @api.onchange('travel_fees', 'is_family', 'has_covid_protect')
    def compute_travel_fee(self):
        for record in self:
            valuation = 0
            payment = 0
            if(self.travel_fees):
                valuation = self.travel_fees.valuation
                if record.is_family and self.travel_fees.has_family_fee:
                    payment = self.travel_fees.family_fee 

                if not record.is_family:    
                    payment = self.travel_fees.payment_fee

                if record.has_covid_protect:
                    payment = payment + (payment * 10) / 100

            record.valuation = valuation
            record.travel_fee_percent = payment


    @api.onchange('local_travel_fees')
    def compute_local_travel_fee(self):
        for record in self:
            valuation = 0
            payment = 0
            if(record.local_travel_fees):
                valuation = record.local_travel_fees.valuation_id.valuation
                payment = record.local_travel_fees.payment_fee

            record.valuation = valuation
            record.travel_fee_percent = payment


    @api.onchange('start_date')
    def change_end_date(self):
        if(self.start_date and self.insurance_type_slug not in ['travel', 'local_travel']):
            self.end_date = self.start_date + relativedelta(years=1)

    @api.onchange('travel_date', 'duration_id', 'local_duration_id')
    def compute_contract_dates(self):
        if(self.travel_date and self.duration_id and self.insurance_type_slug == 'travel'):
            self.start_date = self.travel_date
            self.end_date = self.travel_date + relativedelta(days=int(self.duration_id.value))

        if(self.travel_date and self.local_duration_id and self.insurance_type_slug == 'local_travel'):
            self.start_date = self.travel_date
            self.end_date = self.travel_date + relativedelta(days=int(self.local_duration_id.value_max))

    @api.onchange('state_number')
    def get_data_from_smartcar(self):
        if(self.state_number and len(self.state_number) == 7):
            SMARTCAR_ENDPOINT = 'https://xyp-api.smartcar.mn/xyp-api/v1/xyp/get-data-public'
            headers = {"Content-type": "application/json"}

            data = {
                'serviceCode': "WS100401_getVehicleInfo",
                'customFields': {'plateNumber': self.state_number}
            }
    
            try:
                req = requests.post(SMARTCAR_ENDPOINT, data=json.dumps(data), headers=headers, timeout=30)

                req.raise_for_status()
                content = req.json()

                self.build_year = content['buildYear']
                self.cabin_number = content['cabinNumber']
                self.imported_year = fields.Date.from_string(content['importDate']).year
                self.color = content['colorName']
                self.car_mark_name = content['markName']
                self.car_model_name = content['modelName']
                self.country_name = content['countryName']
                self.type = content['type']
                self.class_name = content['className']
                self.motor_capacity = content['capacity']
                self.payload_capacity = content['mass']
                self.seating_capacity = content['manCount']
                self.is_trailer =  False if not content['transmission'] else True

            except IOError:
                error_msg = _("Smartcar холбогдох үед алдаа гарлаа, зөв дугаар оруулж шалгана уу")
                self.env.user.notify_warning(message=error_msg, title='Анхааруулга!')
                self.build_year = ''
                self.cabin_number = ''
                self.imported_year = ''
                self.color = ''
                self.car_mark_name =  ''
                self.car_model_name =  ''
                self.country_name =  ''
                self.type =  ''
                self.class_name =  ''
                self.motor_capacity =  ''
                self.payload_capacity =  ''
                self.seating_capacity =  ''
                self.is_trailer = False


    @api.onchange('insurance_id','is_restored')
    def get_generate_contract_number(self):
        for record in self:
            record.contract_number = self.generate_contract_number()

    def generate_contract_number(self):
        for record in self:
            contract_number = ''
            contract_prefix = self.env.user.contract_prefix
            contract_count = self.env.user.contract_count
            zeros_length = 5 - len(str(contract_count))
            zeros = ''
            i = 1
            while i <= zeros_length:
                i += 1
                zeros = zeros + '0'

            if(contract_prefix):
                date = fields.Datetime.today().strftime('%Y%m')
                contract_number = contract_prefix + '' + date + '' + str(zeros) + '' + str(contract_count+1)
            return contract_number

                
    @api.constrains('customer_duty_liable_amount', 'customer_duty_liable_type')
    def constrain_duty_liable_amount(self):
        for record in self:
            if(record.customer_duty_liable_type == 'percent' and record.customer_duty_liable_amount > 100):
                raise ValidationError('Буруу хувь оруулсан байна.')
            if(not record.customer_duty_liable_type and record.customer_duty_liable_amount > 0):
                raise ValidationError('Өөрийн хариуцах хэсгийн төрөл сонгоно уу.')
            if(record.customer_duty_liable_type and record.customer_duty_liable_amount == 0):
                raise ValidationError('Өөрийн хариуцах хэсгийн дүн оруулна уу.')

    def _search_state_number(self, operator, value):
        car_ids = self.env['cars'].search('state_number', operator, value).ids
        return [('car_id', 'in', car_ids)]


    @api.model
    def create(self, vals):
        slug = self.env['products'].browse(vals.get('product_id')).insurance_type_id.slug
        settings = self.env['settings'].sudo().browse(1)
    
        self.env.user.write({'contract_count': self.env.user.contract_count+1})
        if(slug in ['car', 'ajd']):
            car = self.env['cars'].create({
                'state_number': vals.get('state_number'),
                'cabin_number': vals.get('cabin_number'),
                'build_year': vals.get('build_year'),
                'imported_year': vals.get('imported_year'),
                'color': vals.get('color'),
                'car_mark_name': vals.get('car_mark_name'),
                'car_model_name': vals.get('car_model_name'),
                'country_name': vals.get('country_name'),
                'type': vals.get('type'),
                'class_name': vals.get('class_name'),
                'motor_capacity': vals.get('motor_capacity'),
                'payload_capacity': vals.get('payload_capacity'),
                'seating_capacity': vals.get('seating_capacity'),
                'is_trailer': vals.get('is_trailer'),
            })
            vals['car_id'] = car.id

        elif(slug in ['travel', 'local_travel'] and not vals.get('travel_id')):
            travel = self.env['travels'].create({
                'country_zone_id': vals.get('country_zone_id'),
                'country': vals.get('country'),
                'duration_id': vals.get('duration_id'),
                'exchange_rate': vals.get('exchange_rate'),
                'travel_date': vals.get('travel_date'),
                'purpose': vals.get('purpose'),
                'is_family': vals.get('is_family'),
                'local_duration_id': vals.get('local_duration_id'),
                'local_duration': vals.get('local_duration'),
            })
            vals['travel_id'] = travel.id

        if(vals.get('customer_name')):
            customer = self.env['res.partner'].create({
                'broker_type': 'customer',
                'is_company': True if vals.get('customer_type') == 'company' else False,
                'surname': vals.get('customer_surname'),
                'name': vals.get('customer_name'),
                'registerno': vals.get('customer_registerno'),
                'phone': vals.get('customer_phone'),
                'email': vals.get('customer_email'),
                'street': vals.get('customer_street'),
            })
            vals['customer_id'] = customer.id

        if(vals.get('is_restored') == True):
            vals['state'] = 'paid'

        contract = super(Contract, self).create(vals)
        settings.last_contract_number = int(settings.last_contract_number)+1
        return contract


    def write(self, vals):
        # if self.can_approve == False:
        #         raise UserError("Зөвхөн 'Ноорог' төлөвтэй гэрээг засах боломжтой.")
        
        if(vals.get('insurance_type_slug') in ['car', 'ajd'] or self.insurance_type_slug in ['car', 'ajd']):
            car = self.env['cars'].browse(self.car_id.id)

            car.write({
                'state_number': vals.get('state_number') if vals.get('state_number') else self.state_number,
                'cabin_number': vals.get('cabin_number') if vals.get('cabin_number') else self.cabin_number,
                'build_year': vals.get('build_year') if vals.get('build_year') else self.build_year,
                'imported_year': vals.get('imported_year') if vals.get('imported_year') else self.imported_year,
                'color': vals.get('color') if vals.get('color') else self.color,
                'car_mark_name': vals.get('car_mark_name') if vals.get('car_mark_name') else self.car_mark_name,
                'car_model_name': vals.get('car_model_name') if vals.get('car_model_name') else self.car_model_name,
                'country_name': vals.get('country_name') if vals.get('country_name') else self.country_name,
                'type': vals.get('type') if vals.get('type') else self.type,
                'class_name': vals.get('class_name') if vals.get('class_name') else self.class_name,
                'motor_capacity': vals.get('motor_capacity') if vals.get('motor_capacity') else self.motor_capacity,
                'payload_capacity': vals.get('payload_capacity') if vals.get('payload_capacity') else self.payload_capacity,
                'seating_capacity': vals.get('seating_capacity') if vals.get('seating_capacity') else self.seating_capacity,
                'is_trailer': vals.get('is_trailer') if vals.get('is_trailer') else self.is_trailer,
            })
        elif(vals.get('insurance_type_slug') in ['travel', 'local_travel'] or self.insurance_type_slug in ['travel', 'local_travel']):
            if(self.travel_id):
                travel = self.env['travels'].browse(self.travel_id.id)
            else:
                travel = self.env['travels'].create({})
                vals['travel_id'] = travel.id

            travel.write({
                'country_zone_id': vals.get('country_zone_id') if vals.get('country_zone_id') else self.country_zone_id.id,
                'country': vals.get('country') if vals.get('country') else self.country,
                'duration_id': vals.get('duration_id') if vals.get('duration_id') else self.duration_id,
                'exchange_rate': vals.get('exchange_rate') if vals.get('exchange_rate') else self.exchange_rate,
                'travel_date': vals.get('travel_date') if vals.get('travel_date') else self.travel_date,
                'purpose': vals.get('purpose') if vals.get('purpose') else self.purpose,
                'is_family': vals.get('is_family') if vals.get('is_family') else self.is_family,
            })

        customer = self.env['res.partner'].browse(self.customer_id.id)
        customer.write({
            'is_company': True if vals.get('customer_type') == 'company' else False,
            'surname': vals.get('customer_surname') if vals.get('customer_surname') else self.customer_surname,
            'name': vals.get('customer_name') if vals.get('customer_name') else self.customer_name,
            'registerno': vals.get('customer_registerno') if vals.get('customer_registerno') else self.customer_registerno,
            'phone': vals.get('customer_phone') if vals.get('customer_phone') else self.customer_phone,
            'email': vals.get('customer_email') if vals.get('customer_email') else self.customer_email,
            'street': vals.get('customer_street') if vals.get('customer_street') else self.customer_street,
        })

        contract = super(Contract, self).write(vals)

        return contract


    def unlink(self):
        for record in self:
            if record.can_approve == False:
                raise UserError(f"Зөвхөн 'Ноорог' төлөвтэй гэрээг устгах боломжтой.")

        return super(Contract, self).unlink()


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


    def payment_paid(self):
        for record in self:
            record.state = 'paid'
            record.paid = record.total_payment
            if(record.insurance_type_slug in ['travel', 'local_travel']):
                if(record.travel_people_count > 1):
                    record.split_contract()
                else:
                    self.customize_customer()
            self.send_contract_email()

    def send_contract_email(self):
        if(not self.product_id.attachment):
            return self.env.user.notify_danger(message='Гэрээний хавсралт байхгүй байна.')   
        
        email_template = self.env.ref('broker_contract.mail_template_contract_pdf_new16')
        # if(not self.contract_pdf_id):
        self.new_file_generate()

        email = self.customer_email if self.customer_email else ''

        if email_template and email:
            email_values = {
                'subject': f'{self.insurance_id.name} - {self.product_id.name}',
                'email_to': email,
                'email_from': 'ubisol.app@gmail.com',
                'attachment_ids': [(6, 0, [self.contract_pdf_id.id])],
            }
            
            email_template.send_mail(self.id, email_values=email_values, force_send=True)
            self.is_email_sent = True

            self.message_post_with_source(
                email_template,
                subtype_xmlid='mail.mt_activities',
            )
            
            return self.env.user.notify_success(message='Амжилттай илгээлээ.')   


    def new_file_generate(self):
        if(not self.product_id.attachment):
            return self.env.user.notify_danger(message='Гэрээний хавсралт байхгүй байна.')   
        
        #------- read docx from product and save it to another folder with changed variables
        tmp_folder_name = '/tmp/docx_to_pdf/'
        if not os.path.exists(tmp_folder_name):
            self._create_temp_folder(tmp_folder_name)
        file_display_name = self.product_id.attachment_name.split('.')[0]
        template_path = tmp_folder_name + self.product_id.attachment_name
        
        contract_data = base64.decodebytes(self.product_id.attachment)
        contract_data = BytesIO(contract_data)
        doc = DocxTemplate(contract_data)
        context = self.convert_var_to_data(doc, tmp_folder_name)
        doc.render(context, autoescape=True)
        doc.save(template_path)
        
        #------- convert new docx to pdf file and save it to same folder 
        pdf_name = file_display_name+'.pdf'
        # cmd = "/Applications/LibreOffice.app/Contents/MacOS/soffice --headless --convert-to pdf " + template_path + " --outdir " + tmp_folder_name 
        cmd = "/lib/libreoffice/program/soffice --headless --convert-to pdf " + template_path + " --outdir " + tmp_folder_name 
        os.system(cmd)

        #------- read pdf file from path and save it to self contract's attachment
        input_stream = open(tmp_folder_name+pdf_name, 'rb')
        try:
            report = input_stream.read()
            self.create_contract_pdf(report)
        finally:
            input_stream.close()



    def create_contract_pdf(self, report):
        #------------- read and write PDF from path
        data_record = base64.b64encode(report)
        ir_values = {
            'name': _("Гэрээ %s.pdf") % self.contract_number,
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/pdf',
            'res_id': self.id,
            'res_model': self._name,
        }

        if self.contract_pdf_id:
            linked_messages = self.env['mail.message'].search([
                ('attachment_ids', 'in', self.contract_pdf_id.id)
            ])
            for message in linked_messages:
                message.attachment_ids = [(3, self.contract_pdf_id.id)]  # Unlink the attachment from the message
                message.unlink()  # Unlink from the message
        
        attachment = self.env['ir.attachment'].create(ir_values)
        self.contract_pdf_id = attachment.id
        self.message_post(
            body="Гэрээний хавсралт файл.",
            subject="Document Attachment",
            attachment_ids=[attachment.id],  # Attach the created attachment
        )

    def convert_var_to_data(self, doc, tmp_folder_name):
    # def convert_var_to_data(self, tmp_folder_name):
        company = self.env['res.company'].browse(1)

        stamp_path = os.path.join(tmp_folder_name, "stamp_image1.png")
        signature_path = os.path.join(tmp_folder_name, "signature_image.png")
        logo_path = os.path.join(tmp_folder_name, "insurer_logo.png")

        if company.stamp:
            stamp_base64 = base64.b64decode(company.stamp)
            if not os.path.exists(stamp_path):
                with open(stamp_path, 'wb') as f:
                    f.write(stamp_base64)

        if company.signature:
            signature_base64 = base64.b64decode(company.signature)
            # Write the binary data to the file
            if not os.path.exists(signature_path):
                with open(signature_path, 'wb') as f:
                    f.write(signature_base64)


        if self.insurance_id.image_1920:
            insurance_logo_base64 = base64.b64decode(self.insurance_id.image_1920)

            if not os.path.exists(logo_path):
                with open(logo_path, 'wb') as f:
                    f.write(insurance_logo_base64)

        duty_liable_suffex = '%' if self.customer_duty_liable_type == 'percent' else '₮'
        payment_prefix = 'MNT ' if self.travel_id.exchange_rate > 0 else 'USD '
        insured_name = self.customer_surname +' '+ self.customer_name if self.customer_surname else self.customer_name

        context = {
            'erp_contract_number': self.erp_contract_number or '',
            'contract_number': self.contract_number or '',
            'insurance_name': self.insurance_id.name or '',
            'insurance_type_name': self.insurance_type_id.name or '',
            'product_name': self.product_id.name or '',
            'create_date': self.create_date.strftime('%Y.%m.%d') or '',
            'start_date': self.start_date.strftime('%Y.%m.%d') or '',
            'end_date': self.end_date.strftime('%Y.%m.%d') or '',
            'today': date.today().strftime('%Y.%m.%d') or '',
            'year': date.today().strftime('%Y') or '',
            'month': date.today().strftime('%m') or '',
            'day': date.today().strftime('%d') or '',
            'customer_surname': self.customer_surname or '',
            'customer_name': self.customer_name or '',
            'customer_registerno': self.customer_registerno or '',
            'customer_phone': self.customer_phone or '',
            'customer_email': self.customer_email or '',
            'customer_birthday': str(self.customer_birthday) if self.customer_birthday else '',
            'customer_address': self.customer_street or '',
            'work_address': self.customer_street2 or '',
            'customer_position': self.customer_passport or '',
            'emergency_contact_name': self.emergency_contact_name or '',
            'emergency_contact_phone': self.emergency_contact_phone or '',
            'insurer_name': company.name or '',
            'insured_name': insured_name or '',
            'country': self.travel_id.country or '',
            'customer_duty_liable': f'{self.customer_duty_liable_amount:,}' + duty_liable_suffex or '',
            'valuation': f'{self.valuation:,}' or '',
            'payment_percent': f'{self.payment_fee_percent:,}' or '',
            'payment': f'{self.payment:,}' or '',
            'discount': f'{self.discount_amount:,}' or '',
            'payable': f'{self.total_payment:,}' or '',
            'paid': f'{self.paid:,}' or '',
            'user_name': self.user_id.partner_id.surname or '' +' '+ self.user_id.partner_id.name or '',
            'user_mobile': self.user_id.partner_id.mobile or '',
            'company_stamp': InlineImage(doc, image_descriptor=stamp_path, width=Mm(25)),
            'company_signature': InlineImage(doc, image_descriptor=signature_path, width=Mm(15)),
            'insurer_logo': InlineImage(doc, image_descriptor=logo_path, height=Mm(6)),
        }

        if(self.insurance_type_id.slug == 'travel'):
            context.update({
                'travel_fee_percent': str(self.travel_fee_percent) + '$' or '',
                'duration': self.travel_id.duration_id.name or '',
                'passport': self.travel_id.passport or '',
                'travel_date': self.travel_id.travel_date.strftime('%Y.%m.%d') or '',
                'purpose': self.travel_id.purpose or '',
                'zone': self.travel_id.country_zone_id.name or '',
                'exchange_rate': f'{self.travel_id.exchange_rate:,}' or '',
                'valuation': 'USD ' + f'{self.valuation:,}' or '',
                'payment': payment_prefix + f'{self.payment:,}' or '',
                'discount': payment_prefix + f'{self.discount_amount:,}' or '',
                'payable': payment_prefix + f'{self.total_payment:,}' or '',
                'paid': f'{self.paid:,}' or '',
                'is_limit': 'Тийм' if self.is_limit else 'Үгүй'
            })
        elif(self.insurance_type_id.slug == 'car'):
            context.update({
                'plate_number': self.car_id.state_number or '',
                'cabin_number': self.car_id.cabin_number or '',
                'build_date': self.car_id.build_year or '',   
                'car_mark': self.car_id.car_mark_name or '',   
                'car_model': self.car_id.car_model_name or '',   
                'import_date': self.car_id.imported_year or '',   
                'color': self.car_id.color or ''
            })

        return context

    def _create_temp_folder(self, tmp_folder_name):
        '''Систем дээр хадгалсан binary буюу file -ийг уншиж docx болгон хувиргах'''
        cmd = 'mkdir ' + tmp_folder_name
		
        if not os.path.exists(tmp_folder_name):
            os.makedirs(tmp_folder_name)


    def split_contract(self):
        for record in self:
            payment = record.payment
            total_payment = record.total_payment
            travel_people_count = record.travel_people_count

            for index, travel_person in enumerate(record.travel_people):
                if index == 0:
                    continue

                customer = travel_person
                before_contract_vals = record.copy_data({
                    'travel_people_count': 1,
                    'payment': payment / travel_people_count,
                    'total_payment': total_payment / travel_people_count,
                    'state': 'paid',
                    'customer_id': customer.id, 
                    'travel_people': [(5, 0, 0)],
                    'travel_id': record.travel_id.id,
                    'contract_number': record.contract_number+' - '+str(index+1)
                })[0] 
                new_contract = self.env['contracts'].sudo().create(before_contract_vals)

            record.travel_people_count = 1
            record.state = 'paid'
            record.payment = payment/travel_people_count
            record.total_payment = total_payment/travel_people_count
            record.contract_number = record.contract_number+' - 1'
            self.customize_customer()

    def customize_customer(self):
        if len(self.travel_people) > 0:
            self.customer_id = self.travel_people[0].id
        # self.travel_people = [(5, 0, 0)]

    def bank_name_btn(self):
        return True

    def account_number_btn(self):
        return True
    
    def account_holder_name_btn(self):
        return True

    def handleApi(self):
        insurance_slug = self.insurance_slug
        # if(self.product_id.erp_product_id == 0 or self.product_id.erp_bundle_id == 0):
        #     return self.env.user.notify_warning(message='ERP системд холбогдох ID мэдээлэл байхгүй байна.', title='Анхааруулга!')

        # if insurance_slug == 'mongol':
        #     msg, target=self.createMongolInsurance()
        # elif insurance_slug == 'practical':
            # msg, target=self.createPracticalContract()
        msg, target=self.createPracticalContract()

        if target == 200:
            return self.env.user.notify_success(message=msg, title='Амжилттай!')  
        else:
            return self.env.user.notify_warning(message=msg, title='Анхааруулга!')

    def checkPayment(self):
        insurance_slug = self.insurance_slug

        if insurance_slug == 'mongol':
            msg, target = self.checkMongolPayment()
        
        if target == 200:
            return self.env.user.notify_success(message=msg, title='Амжилттай!')  
        else:
            return self.env.user.notify_warning(message=msg, title='Анхааруулга!')

# ------------------------------API----------------------------------------
# ---------------
    def getMongolHeaderData(self):
        headers = {
            "Content-type": "application/json",
            "Auth-Token": self.env['settings'].sudo().browse(1).mongol_auth_token
        }

        data = {
            "broker_no": mongol_broker_no, 
            "broker_terminal_no": mongol_broker_terminal_no, 
            "contract": [
                {
                    "product": self.product_id.erp_product_id, 
                    "Invoice_no": self.erp_contract_id
                }
            ]
        }

        return headers, data

    def generate_qr_code(self):
        for record in self:
            base64_str = record.qr_code
            logging.info(base64_str)


    def createMongolInsurance(self):
        _logger.info('createMongolInsurance')
        headers, data = self.getMongolHeaderData()
        vals = {}
        request_code = '901014'
        driver_datas = {
                "register_no": self.customer_registerno, 
                "cif_name": self.customer_name, 
                "cif_middle_name": self.customer_surname,
                "phone": self.customer_phone,
                "address_code": "",
                "cif_address": "", 
                "email": self.customer_email
            }
        # if(self.is_limit == True and len(self.driver_ids) > 0):
        #     for driver in self.driver_ids:
        #         driver_datas.append({
        #             "register_no": driver.registerno, 
        #             "cif_name": driver.name, 
        #             "cif_middle_name": driver.surname,
        #             "phone": driver.phone,
        #             "address_code": "",
        #             "cif_address": "", 
        #             "email": driver.email
        #         })

        
        data = {
            'broker_no': mongol_broker_no,
            'broker_terminal_no': mongol_broker_terminal_no,
            'contract': [{
                "product": self.product_id.erp_product_id, 
                "data": {
                    "sub_id": self.product_id.erp_bundle_id, 
                    "duration": (fields.Date.from_string(self.end_date).year - fields.Date.from_string(self.start_date).year),
                    "valuation": self.valuation,
                    "scp": 0,
                    "rate": 1 if self.is_limit == False else 2,
                    "begdate": self.start_date.strftime("%Y-%m-%d"),
                    "payment_method": "QPAY", 
                    "policy_no": self.contract_number,
                    "fee": self.total_payment,
                    "driver": driver_datas, 
                    "car": {
                        "color": self.color, 
                        "engineCapacity": self.motor_capacity, 
                        "make": self.car_mark_name, 
                        "model": self.car_model_name, 
                        "number": self.state_number, 
                        "payloadcapacity": self.payload_capacity,
                        "seatingcapacity": self.seating_capacity, 
                        "transporttype": self.class_name, 
                        "vin": self.cabin_number, 
                        "impYear": self.imported_year, 
                        "buildYear": self.build_year
                    },
                }
            }]
        }

        try:
            req = requests.post(MONGOL_ENDPOINT+request_code, data=json.dumps(data), headers=headers, timeout=30)
            logging.info(req)
            req.raise_for_status()
            
            decoded_data = req.text.encode().decode('utf-8-sig')
            decoded_data = json.loads(decoded_data)
            if(decoded_data['result_code'] == 0):
                result_data = decoded_data['result_data']
                self.erp_contract_id = result_data['Fee'][0]['Invoice_no']
                # self.qr_code = result_data['Fee'][0]['qpay_image']
                self.qr_image = result_data['Fee'][0]['qpay_image']
                self.erp_state = 'sent'

                success_msg = _("Гэрээний нэхэмжлэх амжилттай татлаа.")
                return success_msg, 200
        except IOError:
            error_msg = _("Монгол даатгалтай холбогдох үед алдаа гарлаа")
            return error_msg, 500

    def validateMongolInsurance(self):
        headers, data = self.getMongolHeaderData()
        _logger.info('validateMongolInsurance')    
        request_code = '901015'
        vals = []
       
        req = requests.post(MONGOL_ENDPOINT+request_code, data=json.dumps(data), headers=headers, timeout=30)
        req.raise_for_status()
        response = req.text.encode().decode('utf-8-sig')
        response = json.loads(response)
        if(response['result_code'] == 0):
            vals = {
                'erp_contract_url': response['result_data'][0]['download_url'],
            }

            self.state = 'sent'
            self.message_post(
                body=response['result_data'][0]['download_url'],
                subject="Гэрээний хавсралт файл."
            )
            success_msg = _("Гэрээ амжилттай үүслээ.")
            self.env.user.notify_success(message=success_msg, title='Амжилттай!')
        else:
            error_msg = response['result_desc']
            self.env.user.notify_warning(message=error_msg, title='Анхааруулга!')

        return vals
    
    def checkMongolPayment(self):
        headers, data = self.getMongolHeaderData()
        _logger.info('checkMongolPayment')    
        request_code = '901016'
        try:
            req = requests.post(MONGOL_ENDPOINT+request_code, data=json.dumps(data), headers=headers, timeout=30)
            req.raise_for_status()
            response = req.text.encode().decode('utf-8-sig')
            response = json.loads(response)

            if(response['result_code'] == 0 and response['result_data'][0]['succeed']):
                self.erp_invoice_id = response['result_data'][0]['trace_no']
                self.state = 'paid'

                self.validateMongolInsurance()
                success_msg = _("Гэрээний төлбөр амжилттай төлөгдсөн байна.")
                return success_msg, 200
            else:
                warning_msg = _("Гэрээний төлбөр төлөгдөөгүй байна.")
                return warning_msg, 201

        except IOError:
            error_msg = _("Монгол даатгалтай холбох үед алдаа гарлаа.")
            return error_msg, 500
        

# ---------------
    def createPracticalContract(self):
        erp_customer_id, uid = self.createPracticalCustomer()
        policy_data = []
        car_item = {}
        travel_item = {}
        local_travel_item = {}
        asset_item = {}
        car_datas = self.car_id
        travel_data = self.travel_id


        gzd_type = 'Travel'
        protection_type = 'Comprehensive travel insurance'
        if(self.car_id):
            car_item = {
                'x_mainNumber': self.cabin_number,
                'x_carNumber': self.state_number,
                'x_mark': self.car_mark_name,
                'x_model': self.car_model_name,
                'x_productYear': self.build_year,
                'x_productYearM': self.imported_year,
                'x_color': self.color
            }
        elif(self.insurance_type_slug == 'travel' and self.travel_id):
            country_zones = [
                {'id': 'asian', 'name': 'Ази', 'type': 6},
                {'id': 'worldwide', 'name': 'Worldwide excluding USA & Canada', 'type': 2},
                {'id': 'usa_canada_japan', 'name': 'USA, Canada & Japan', 'type': 3},
                {'id': 'shengen', 'name': 'Schengen /+15 days/', 'type': 4}
            ]
            
            travel_type = 0
            for zone in country_zones:
                if zone['id'] == self.country_zone_id.value:
                    travel_type = zone['type']
                    continue

            
            travel_item = {
                'currency_date': self.create_date.strftime("%Y-%m-%d") if self.create_date else None,
                'insur_current_rate': self.exchange_rate,
                'insur_policy_currency': 2,
                'ins_estimate': self.valuation * self.exchange_rate,
                'ins_estimate_cur': self.valuation,
                'ins_fee': self.total_payment,
                'ins_fee_cur': self.total_payment/self.exchange_rate,
                'how_day': self.duration_id.value,
                'partner_type': 'person',
                'group_id': travel_type,
                'x_passNumber': self.customer_passport,
                'x_foriegnNames': self.customer_name,
                'x_foriegnReg': self.customer_registerno,
                'x_childname': '',
                'x_childReg': '',
                'x_travelGoal': gzd_type,
                'x_protectionType': protection_type
            }
        elif(self.insurance_type_slug == 'local_travel' and self.travel_id):
            local_travel_item = {
                'x_age_your': 0,
                'x_indemnity': '1',
                'x_unelgee': self.valuation,
                'x_branch': ''
            }
        elif(self.insurance_type_slug == 'property'):
            asset_item = {
                'x_locationItem': self.property_id.address,
                'x_zuiliinNer': self.property_id.title,
                'x_purpose': '',
                'x_other': 'other',
                'x_owner': self.customer_name,
                'x_typeHorong': '',
                'x_mk': 1,
                'x_serialNumber': ''
            }

        erp_product_id, erp_bundle_id = self.practicalErpIdMatch(travel_type, self.valuation)
        policy_ids = [
            {
                'insur_policy_currency': 111,
                'partner_id': erp_customer_id,
                'security_start_date': self.travel_date.strftime("%Y-%m-%d") if self.travel_date else None,
                'security_end_date': self.end_date.strftime("%Y-%m-%d") if self.end_date else None,
                'insurance_product_id': erp_product_id,
                'choose_id': erp_bundle_id,
                'auto_number': True,
                'ins_estimate': self.valuation,
                'fee_percent': self.payment_fee_percent,
                'ins_fee': self.total_payment,
                **local_travel_item,
                **travel_item,
                **asset_item,
                **car_item,
            }
        ]
        params = {
            "partner_id": erp_customer_id,
            "payment_divide": 1,
            "payment_amount": self.total_payment,
            "insurance_product_id": erp_product_id,
            "start_date": self.travel_date.strftime("%Y-%m-%d") if self.travel_date else None,
            "end_date": self.end_date.strftime("%Y-%m-%d") if self.end_date else None,
            "policy_ids": policy_ids,
            "file_datas": []
        }

        logging.info('params')
        logging.info(json.dumps(params))

        try:
            modules = xmlrpclib.ServerProxy('%s:%s/xmlrpc/2/object' % (PRTL_ENDPOINT, PRTL_PORT)).execute(
                prtl_db_name, uid, prtl_password, 'pd.api', 'create_contract', params)
        
            logging.info('modules')
            logging.info(modules)
            if len(modules) > 1 and modules['result'] == 'success':
                self.erp_customer_id = erp_customer_id 
                self.erp_contract_id = modules['contract_id']   
                self.erp_contract_number = modules['policy_name']   
                self.erp_policy_id = modules['policy_id']
                self.erp_state = 'sent'
                self.state = 'sent'

                success_msg = _("Гэрээ ERP системд амжилттай бичигдлээ.")
                return success_msg, 200
        except IOError:
            error_msg = _("Практикал даатгалын системд гэрээ илгээх явцад алдаа гарлаа.")
            return error_msg, 201

    def createPracticalCustomer(self):
        uid = xmlrpclib.ServerProxy('%s:%s/xmlrpc/2/common' % (PRTL_ENDPOINT, PRTL_PORT)).authenticate(
            prtl_db_name, prtl_username, prtl_password, {})
        erp_customer_id = ''
        params = {
            "name": self.customer_name,
            "lastname" : self.customer_surname,
            "vat": self.customer_registerno,
            "phone": self.customer_phone,
            "email": self.customer_email,
            "street": self.customer_street,
        }

        modules = xmlrpclib.ServerProxy('%s:%s/xmlrpc/2/object' % (PRTL_ENDPOINT, PRTL_PORT)).execute(
            prtl_db_name, uid, prtl_password, 'pd.api', 'create_partner', params)
    
        if len(modules) > 1 and modules['result'] == 'success':
            erp_customer_id = modules['partner_id']   
        elif modules.get('error_msg') == 'Харилцагч үүссэн байна!' and modules['partner_id']:
            erp_customer_id = modules['partner_id']

        return erp_customer_id, uid
    
    def practicalErpIdMatch(self, travel_type, valuation):
        logging.info(travel_type)  
        logging.info(valuation)
        if(self.insurance_type_slug == 'car'):
            erp_product_id = 2
            erp_bundle_id = 78
        elif(self.insurance_type_slug == 'travel'):
            erp_product_id = 63
            if(travel_type == 4):
                erp_bundle_id = 349
            elif(valuation == 45000):
                erp_bundle_id = 175
            else:
                erp_bundle_id = 258
        elif(self.insurance_type_slug == 'local_travel'):
            erp_product_id = 62
            erp_bundle_id = 25
        elif(self.insurance_type_slug == 'property'):
            erp_product_id = 67
            erp_bundle_id = 26

        return erp_product_id, erp_bundle_id
    
    
