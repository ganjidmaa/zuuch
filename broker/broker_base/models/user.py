# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

DEFAULT_MESSAGE = "Default message"

SUCCESS = "success"
DANGER = "danger"
WARNING = "warning"
INFO = "info"
DEFAULT = "default"


class BrokerUser(models.Model):
    _inherit = ['res.users']
    _name = 'res.users'

    miis_user_number = fields.Integer('АЖД гэрээний дугаар')
    contract_prefix = fields.Char('Гэрээ угтвар')
    contract_count = fields.Integer('Гэрээний тоо', default=0)
    insurance_id = fields.Many2one('res.partner', domain=[('broker_type', '=', 'insurance')], string='Даатгал', tracking=True)
    branch = fields.Many2one('hr.department', string='Салбар', tracking=True)


    def notify_success(
        self,
        message="Default message",
        title=None,
        sticky=False,
        target=None,
        action=None,
        params=None,
    ):
        title = title or _("Амжилттай")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'type': SUCCESS,
                'message': _(message),
                'sticky': True
            }
        }

    def notify_danger(
        self,
        message="Default message",
        title=None,
        sticky=False,
        target=None,
        action=None,
        params=None,
    ):
        title = title or _("Алдаа")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'type': DANGER,
                'message': _(message),
                'sticky': True
            }
        }

    def notify_warning(
        self,
        message="Default message",
        title=None,
        sticky=False,
        target=None,
        action=None,
        params=None,
    ):
        title = title or _("Анхааруулга")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'type': WARNING,
                'message': _(message),
                'sticky': True
            }
        }

    def notify_info(
        self,
        message="Default message",
        title=None,
        sticky=False,
        target=None,
        action=None,
        params=None,
    ):
        title = title or _("Мэдээлэл")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'type': INFO,
                'message': _(message),
                'sticky': True
            }
        }

   
