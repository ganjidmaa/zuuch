# -*- coding: utf-8 -*-
from email.policy import default
import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError, UserError

_logger = logging.getLogger(__name__)

class Product(models.Model):
    _name = 'products'
    _description = 'Broker Policy'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _mail_post_access = 'read'

    name = fields.Char('Бүтээгдэхүүний нэр', tracking=True)
    insurance_type_id = fields.Many2one('insurance.types', string='Даатгалын төрөл', tracking=True)
    insurance_type_slug = fields.Char(string='Даатгалын төрөл', related='insurance_type_id.slug', tracking=True)
    insurance_id = fields.Many2one('res.partner', domain=[('broker_type', '=', 'insurance')], string='Даатгал', tracking=True)
    user_id = fields.Many2one('res.users', string='Ажилтан', default=lambda self: self.env.user)
    status = fields.Boolean()
    desc = fields.Text()
    product_travel_fees = fields.One2many('product.travel.fees', 'product_id', string='.', tracking=True)
    product_local_travel_fees = fields.One2many('product.local.travel.fees', 'product_id', string='.', tracking=True)
    risks = fields.One2many('product.risks', 'product_id', string='.', tracking=True)
    services = fields.Many2many('services', 'product_service_rel', 'product_id', 'service_id', string='.', tracking=True)
    valuation_max_limit = fields.Integer('Үнийн дээд хязгаар')
    valuation_min_limit = fields.Integer('Үнийн доод хязгаар')
    payment_fee_percent = fields.Float('Хураамжийн хувь', tracking=True)
    broker_fee_percent = fields.Float('Зуучлалын хувь', tracking=True)
    discount_type = fields.Selection([
        ('percent', 'Хувиар'),
        ('amount', 'Тогтмол')
    ], 'Хөнгөлөлтийн төрөл')
    discount_amount = fields.Integer('Хөнгөлөлтийн хэмжээ')
    customer_duty_liable_amount = fields.Float('Өөрийн хариуцах дүн')
    customer_duty_liable_type = fields.Selection([
        ('percent', 'Хувь'),
        ('amount', 'Дүн')
    ], string='Өөрийн хариуцах төрөл')  
    template_text = fields.Html('Гэрээний загвар', default='')
    template_body = fields.Html('Дэлгэрэнгүй мэдээлэл', default='')
    erp_product_id = fields.Char('Erp бүтээгдэхүүний ID')
    erp_bundle_id = fields.Char('Erp багцын ID')

    attachment = fields.Binary(string="Attachment", attachment=True)
    attachment_name = fields.Char(string="Attachment Filename")  # Field to store the filename

