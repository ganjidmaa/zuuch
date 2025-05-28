from odoo import models, fields, api, _
import requests
import json
import logging
import datetime
from datetime import date
MIIS_ENDPOINT = 'https://miis.ami.mn'

class MiisDownloadActionWizard(models.TransientModel):
    _name = 'miis.download.action.wizard'
    _description = 'Miis Download Action Wizard'

    start_date = fields.Date('Эхлэх огноо', tracking=True, default=lambda self: date.today())


    def confirm_action(self):
        api_token = self.env['settings'].sudo().browse(1).miis_auth_token
        if(not api_token):
            error_msg = _("АЖД системд гэрээ илгээх явцад алдаа гарлаа.")
            self.env.user.notify_warning(message=error_msg)
            return True

        headers = {
            "Content-type": "application/json",
            "Authorization": 'Bearer '+ api_token
        }

        payload = {
            "date": self.start_date.strftime('%Y-%m-%d')
        }

        response = requests.post(MIIS_ENDPOINT+'/admin/policy/list/sys', headers=headers, data=json.dumps(payload))
        response_data = response.json()       
        status_code = response.status_code
        error_msg = response_data['text']
        if(status_code == 200 and not error_msg):
            contracts = response_data['data']
            total_count = len(contracts)
            contract_count = 0
            for contract in contracts:
                duplicated_miis_contract = self.env['miis'].search([('contract_number', '=', contract['policy_number'])], limit=1)
                
                if(not duplicated_miis_contract):
                    user = self.env['res.users'].search([('miis_user_number', '=', contract['employee_id'])], limit=1)
                    if(not user):
                        continue

                    insurer = self.env['res.partner'].search([('registerno', '=', contract['register_number'])], limit=1)
                    if(not insurer and contract['insuree_name']):
                        insurer_data = {
                            'broker_type': 'customer',
                            'is_company': contract['is_person'],
                            'surname': contract['last_name'] if contract['last_name'] else '',
                            'name': contract['insuree_name'],
                            'registerno': contract['register_number'],
                            'phone': contract['phone_number'],
                            'email': contract['email'] if contract['email'] else '',
                            'street': contract['address'] if contract['address'] else '', 
                        }
                        insurer = self.env['res.partner'].create(insurer_data)

                    car = self.env['cars'].search([('state_number', '=', contract['platenumber'])], limit=1)
                    
                    if(not car):
                        car = self.env['cars'].create({
                            'state_number': contract['platenumber'],
                            'cabin_number': contract['cabinnumber'],
                            'build_year': '',
                            'imported_year': '',
                            'color': contract['colorname'],
                            'car_mark_name': contract['markname'],
                            'car_model_name': contract['modelname'],
                            'country_name': '',
                            'type': '',
                            'class_name': contract['classname'],
                            'motor_capacity': int(float(contract['capacity'])) if contract['capacity'] else '',
                            'payload_capacity': '',
                            'seating_capacity': contract['mancount'],
                            'is_trailer': contract['istrailer'],
                        })

                    insurance_id = self.env['res.partner'].search([('broker_type', '=', 'insurance'), ('insurance_org', '=', contract['insurance_company_id'])], limit=1).id
                    product_id = self.env['products'].search([('insurance_id', '=', insurance_id), ('insurance_type_id.slug', '=', 'ajd')], limit=1).id
                    dt_object = datetime.datetime.fromtimestamp(contract['fromdate']/1000)           
                    start_date = dt_object.strftime('%Y-%m-%d') 
                    dt1_object = datetime.datetime.fromtimestamp(contract['todate']/1000)           
                    end_date = dt1_object.strftime('%Y-%m-%d')
                    
                    new_miis_contract = self.env['miis'].create({
                        'car_id': car.id,   
                        'customer_id': insurer.id,   
                        'user_id': user.id,
                        'is_limit': contract['driver_limit'],   
                        'contract_number': contract['policy_number'],
                        'state': 'done',
                        'customer_type': contract['policy_type'],
                        'start_date': start_date,
                        'end_date': end_date,
                        'customer_registerno': contract['register_number'],
                        'customer_phone': contract['phone_number'],
                        'customer_email': contract['email'] if contract['email'] else '',
                        'state_number': contract['platenumber'],
                        'miis_policy_id': contract['policy_id'],
                        'insurance_id': insurance_id if insurance_id else '',
                        'product_id': product_id if product_id else '',
                        'base_amount': contract['ci0'],
                        'invoice_amount': contract['insfee'],
                        'download_ajd': True,
                    })
        
                    if(len(contract['drivers']) > 0):
                        for driver in contract['drivers']:
                            co_borrower = self.env['res.partner'].search([('registerno', '=', driver['register_number'])], limit=1)
                            if(not co_borrower):
                                co_borrower = self.env['res.partner'].create({
                                    'broker_type': 'customer',
                                    'is_company': False,
                                    'surname': driver.get('lastname', ''),
                                    'name': driver.get('firstname', ''),
                                    'registerno': driver.get('register_number'),
                                    'phone': driver.get('phone_number', ''),
                                    'email': driver.get('email', ''),
                                    'street': driver.get('address', ''),
                                })

                            new_miis_contract.driver_ids = [(4, co_borrower.id)]

                    contract_count = contract_count + 1

        return self.env.user.notify_success(message='Нийт %s гэрээнээс %s шинэ гэрээний мэдээлэл татагдалаа.' % (total_count, contract_count))

