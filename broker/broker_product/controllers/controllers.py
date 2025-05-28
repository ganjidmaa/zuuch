# -*- coding: utf-8 -*-
import json
import logging
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied
from datetime import timedelta, datetime
import requests
import base64


_logger = logging.getLogger(__name__)
CURRENCY_RATE_URL = "https://www.mongolbank.mn/mn/currency-rate/data"

class BrokerContracts(http.Controller):

    @http.route('/tapa/get_travel_products', auth='public', methods=['POST'], csrf=False, type='json')
    def get_products(self, **kwargs):
        login = kwargs.get('login')
        password = kwargs.get('password')

        if not login or not password:
            return {"error": "Login and password are required.", "errorcode": 401}
    
        try:
            uid = request.session.authenticate(request.env.cr.dbname, login, password)
            if uid:        
                insurance_type = request.env['insurance.types'].sudo().search([('slug', '=', 'travel')], limit=1)

                available_products = []
                if(insurance_type):
                    products = request.env['products'].sudo().search([('insurance_type_id', '=', insurance_type.id)], order='insurance_id')

                    for key, product in enumerate(products):
                        travel_zone_datas = []
                        risk_datas = []

                        for new_data in product.product_travel_fees:
                            travel_zone_datas.append({
                                'country_zone': new_data.country_zone,
                                'country_zone_name': new_data.country_zone_name,
                                'duration': new_data.duration,
                                'valuation': new_data.valuation,
                                'payment_fee': new_data.payment_fee,
                                'has_family_option': new_data.has_family_fee,
                                'family_fee': new_data.family_fee,
                            })
                            
                        for risk_val in product.risks:
                            if(not risk_val.is_optional):
                                risk_datas.append({
                                    'risk_name': risk_val['risk_name'],
                                    'coverage_valuation': risk_val['valuation'],
                                    'coverage_amount': risk_val['duty_liable_amount'],
                                    'coverage_percent': risk_val['duty_liable_percent'],
                                })

                        available_products.append({
                            'insurer_name': product.insurance_id.name,
                            'product_id': product.id,
                            'product_name': product.name,
                            'product_travel_fees': travel_zone_datas,
                            'product_risks': risk_datas
                        })

                args = {
                    'errorcode': 200, 
                    'errormsg': 'Амжилттай',
                    'response': available_products
                }     
                return args
        
        except AccessDenied:
            return {"error": "Authentication failed. Incorrect login or password.", "errorcode": 401}
        
        return {"error": "Invalid login credentials."}

    @http.route('/tapa/contract_payment_data', auth='public', methods=['POST'], csrf=False, type='json')
    def contract_payment_hook(self, **kwargs):
        login = kwargs.get('login')
        password = kwargs.get('password')

        if not login or not password:
            return {"error": "Login and password are required.", "errorcode": 401}
    
        try:
            uid = request.session.authenticate(request.env.cr.dbname, login, password)
            if uid:        
                response = {'status': 201, 'message': 'error'}
                payment_state = kwargs['paymentState']
                if(payment_state == 'paid'):
                    contract_res = self.create_travel_contract(kwargs)
                    if(contract_res['statusCode'] == 200):
                        response = {'status': 200, 'message': 'success', 'contract_files': contract_res}
                    else:
                        response = {'status': 201, 'message': 'product not found'}
                return json.dumps(response)
        except AccessDenied:
            return {"error": "Authentication failed. Incorrect login or password.", "errorcode": 401}
        
        return {"error": "Invalid login credentials."} 

    def get_current_currency(self):
        currency_rate = requests.get('https://monxansh.appspot.com/xansh.json?currency=USD') 
        resp_content = currency_rate.content.decode("utf-8")
        data = json.loads(resp_content)
        currency = data[0]['rate_float']

        return currency

    def create_travel_contract(self, params):
        user = request.env.user
        travel_people = params['people']
        product_id = params['productId']
        country_zone = params['countryZone']
        paid_amount = params['paidAmount']
        contract_pdf_files = []
        product = request.env['products'].sudo().search([('id', '=', product_id)])
        if( not product):
            return {'statusCode': 201} 

        bundle_valuation = params['bundleValuation']
        start_date = params['startDate']
        duration = params['duration']
        person_number = len(travel_people)

        for customer in travel_people:
            customer_params = {
                'name': customer['custFirstName'],
                'surname': customer['custLastName'],
                'registerno': customer['custRd'],
                'street': customer['custAddress'],
                'phone': customer['custPhone'],
                'email': customer['custEmail'],
                'broker_type': 'customer'
            }
            customer_obj = request.env['res.partner'].sudo().create(customer_params)
            country_zone_id = request.env['country.zones'].sudo().search([('value', '=', country_zone)], limit=1).id
            duration_id = request.env['durations'].sudo().search([('value', '=', duration)], limit=1).id
            currency = self.get_current_currency()

            travel_params = {
                'passport': customer['passportNo'],
                'country_zone_id': country_zone_id,
                'duration_id': duration_id,
                'travel_date': start_date,
                'exchange_rate': currency
            }

            travel = request.env['travels'].sudo().create(travel_params)
            travel_fees = product.product_travel_fees
            fee_currency = 0
            travel_fee_id = 0
            for travel_fee in travel_fees:
                if(str(travel_fee.duration) == str(duration) and str(travel_fee.country_zone) == str(country_zone) and int(travel_fee.valuation) == int(bundle_valuation)):
                    fee_currency = travel_fee.payment_fee
                    travel_fee_id = travel_fee.id

            # payment_amount = fee_currency * currency
            payment_amount = (int(paid_amount) / person_number)

            contract_params = {
                'user_id': user.id,
                'insurance_type_id': product.insurance_type_id.id,
                'insurance_id': product.insurance_id.id,
                'product_id': product.id,
                'customer_id': customer_obj.id,
                'travel_date': start_date,
                'travel_id': travel.id,
                'travel_fees': travel_fee_id,
                'travel_fee_percent': fee_currency,
                'valuation': bundle_valuation,
                'payment': payment_amount,
                'total_payment': payment_amount,
                'paid': params['paidAmount'],
                'local_duration': duration,
                'state': 'paid'
            }

            contract = request.env['contracts'].sudo().create(contract_params)
            contract_prefix = user.contract_prefix if user.contract_prefix else ''
            contract_count = user.contract_count
            zeros_length = 5 - len(str(contract_count))
            zeros = ''
            i = 1
            while i <= zeros_length:
                i += 1
                zeros = zeros + '0'

            if(contract_prefix):
                date = datetime.today().strftime('%Y%m')
                contract_number = contract_prefix + '' + date + '' + str(zeros) + '' + str(contract_count+1)

            user.contract_count = user.contract_count+1

            contract.contract_number = contract_number
            contract.create_contract_pdf()
            contract.contract_pdf_id.write({'public': True})
            contract_pdf_files.append({'file_path': "https://digitalzuuch.mn/web/content/%s" % contract.contract_pdf_id.id, 'customer_email': customer['custEmail'], 'customer_name': customer['custFirstName']})
            # contract.with_delay().send_contract_email()
        return {'statusCode': 200, 'contract_files': contract_pdf_files} 

    def create_travel_contract_prev(self, params):
        user = request.env.user

        travel_people = params['people']
        product_id = params['productId']
        country_zone = params['countryZone']
        paid_amount = params['paidAmount']
        contract_pdf_files = []
        product = request.env['products'].sudo().search([('id', '=', product_id)])
        if( not product):
            return {'statusCode': 201} 

        bundle_valuation = params['bundleValuation']
        start_date = params['startDate']
        end_date = params['endDate']
        create_date = params['createDate']
        duration = params['duration']
        person_number = len(travel_people)

        for customer in travel_people:
            customer_params = {
                'name': customer['custFirstName'],
                'surname': customer['custLastName'],
                'registerno': customer['custRd'],
                'street': customer['custAddress'],
                'phone': customer['custPhone'],
                'email': customer['custEmail'],
                'broker_type': 'customer'
            }
            customer_obj = request.env['res.partner'].sudo().create(customer_params)
            country_zone_id = request.env['country.zones'].sudo().search([('value', '=', country_zone)], limit=1).id
            duration_id = request.env['durations'].sudo().search([('value', '=', duration)], limit=1).id
            currency = self.get_current_currency()

            travel_params = {
                'passport': customer['passportNo'],
                'country_zone_id': country_zone_id,
                'duration_id': duration_id,
                'travel_date': start_date,
                'exchange_rate': currency
            }

            travel = request.env['travels'].sudo().create(travel_params)
            travel_fees = product.product_travel_fees
            fee_currency = 0
            travel_fee_id = 0
            for travel_fee in travel_fees:
                if(str(travel_fee.duration) == str(duration) and str(travel_fee.country_zone) == str(country_zone) and int(travel_fee.valuation) == int(bundle_valuation)):
                    fee_currency = travel_fee.payment_fee
                    travel_fee_id = travel_fee.id

            # payment_amount = fee_currency * currency
            payment_amount = (int(paid_amount) / person_number)

            contract_params = {
                'contract_number': params['contractNumber'],
                'user_id': user.id,
                'insurance_type_id': product.insurance_type_id.id,
                'insurance_id': product.insurance_id.id,
                'product_id': product.id,
                'customer_id': customer_obj.id,
                'travel_date': start_date,
                'start_date': start_date,
                'end_date': end_date,
                'create_date': create_date,
                'travel_id': travel.id,
                'travel_fees': travel_fee_id,
                'travel_fee_percent': fee_currency,
                'valuation': bundle_valuation,
                'payment': payment_amount,
                'total_payment': payment_amount,
                'paid': params['paidAmount'],
                # 'local_duration': duration,
                'state': 'paid'
            }

            contract = request.env['contracts'].sudo().create(contract_params)
            # contract_prefix = user.contract_prefix if user.contract_prefix else ''
            # contract_count = user.contract_count
            # zeros_length = 5 - len(str(contract_count))
            # zeros = ''
            # i = 1
            # while i <= zeros_length:
            #     i += 1
            #     zeros = zeros + '0'

            # if(contract_prefix):
            #     date = datetime.today().strftime('%Y%m')
            #     contract_number = contract_prefix + '' + date + '' + str(zeros) + '' + str(contract_count+1)

            user.contract_count = user.contract_count+1
            if create_date:
                request.env.cr.execute("""
                    UPDATE contracts
                    SET create_date = %s
                    WHERE id = %s
                """, (create_date, contract.id))

            # contract.contract_number = params['contractNumber']
            # contract.create_contract_pdf()
            # contract.contract_pdf_id.write({'public': True})
            # contract_pdf_files.append({'file_path': "https://digitalzuuch.mn/web/content/%s" % contract.contract_pdf_id.id, 'customer_email': customer['custEmail'], 'customer_name': customer['custFirstName']})
            # contract.with_delay().send_contract_email()
        # return {'statusCode': 200, 'contract_files': contract_pdf_files} 
        return {'statusCode': 200, 'contract_files': contract.id} 

