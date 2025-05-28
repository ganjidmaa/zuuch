import json
from odoo import http
from odoo.http import content_disposition, request
from odoo.http import serialize_exception as _serialize_exception
from odoo.tools import html_escape
from odoo.http import request
from odoo.exceptions import AccessDenied
from datetime import timedelta, datetime
import requests
import logging
from dateutil.relativedelta import relativedelta

CURRENCY_RATE_URL = "https://www.mongolbank.mn/mn/currency-rate/data"
_logger = logging.getLogger(__name__)

class XLSXReportController(http.Controller):

    @http.route('/xlsx_reports', type='http', auth='user', methods=['POST'], csrf=False)
    def get_report_xlsx(self, model, options, output_format, **kw):
        uid = request.session.uid
        report_obj = request.env[model].with_user(uid)

        callback_method = kw['callback_method']  
        options = json.loads(options)
        token = 'dummy-because-api-expects-one'
        try:
            if output_format == 'xlsx':
                response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                        ('Content-Disposition',
                         content_disposition(f"{kw['report_name']}.xlsx")),
                    ]
                )
                if(callback_method == 'get_reward_xlsx_report'):
                    report_obj.get_reward_xlsx_report(options, response)
                elif(callback_method == 'get_general_xlsx_report'):
                    report_obj.get_general_xlsx_report(options, response)
                elif(callback_method == 'get_financial_xlsx_report'):
                    report_obj.get_financial_xlsx_report(options, response)
                response.set_cookie('fileToken', token)
                return response
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))


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
                            if not (new_data.country_zone == 'shengen' and product.insurance_id.slug == 'practical'):
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
        _logger.info('---------- Creating Travel Contract ----------')
        _logger.info('Params received: %s', params)
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
                'passport_no': customer['passportNo'],
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
                if(str(travel_fee.duration_id.id) == str(duration_id) and str(travel_fee.country_zone_id.id) == str(country_zone_id) and str(travel_fee.valuation_id.valuation) == str(bundle_valuation)):
                    fee_currency = travel_fee.payment_fee
                    travel_fee_id = travel_fee.id

            payment_amount = (int(paid_amount) / person_number)

            contract_params = {
                'user_id': user.id,
                'insurance_type_id': product.insurance_type_id.id,
                'insurance_id': product.insurance_id.id,
                'product_id': product.id,
                'customer_id': customer_obj.id,
                'travel_date': start_date,
                'start_date': start_date,
                'end_date': datetime.strptime(start_date, "%Y-%m-%d")  + relativedelta(days=duration),
                'travel_id': travel.id,
                'travel_fees': travel_fee_id,
                'travel_fee_percent': fee_currency,
                'valuation': bundle_valuation,
                'payment': payment_amount,
                'total_payment': payment_amount,
                'exchange_rate': params['exchangeRate'] if params.get('exchangeRate') else currency,
                'paid': params['paidAmount'],
                'state': 'paid'
            }

            contract = request.env['contracts'].sudo().create(contract_params)
            contract.contract_number = params['contractNumber'] if params.get('contractNumber') else contract.generate_contract_number()
            contract.new_file_generate()
            contract.contract_pdf_id.write({'public': True})
            contract_pdf_files.append({'file_path': "https://digitalzuuch.mn/web/content/%s" % contract.contract_pdf_id.id, 'customer_email': customer['custEmail'], 'customer_name': customer['custFirstName']})
            # contract.with_delay().send_contract_email()
        return {'statusCode': 200, 'contract_files': contract_pdf_files} 


    @http.route('/get_contracts_list', auth='public', methods=['get'], csrf=False, type='json')
    def get_travel_contracts(self, **kwargs):
            user = request.env.user
            contracts = request.env['contracts'].sudo().search([])
            contract_list = []

            for contract in contracts:
                travel_people = []
                for person in contract.customer_id:
                    travel_people.append({
                        "custLastName": person.surname,
                        "custFirstName": person.name,
                        "custRd": person.registerno,
                        "custAddress": person.street,
                        "custPhone": person.phone,
                        "custEmail": person.email,
                        "passportNo": contract.travel_id.passport
                    })

                contract_data = {
                    "contractNumber": contract.contract_number,
                    "productId": contract.product_id.id,
                    "countryZone": contract.travel_id.country_zone_id.value,
                    "bundleValuation": int(contract.valuation),
                    "startDate": contract.travel_date.strftime('%Y-%m-%d'),
                    "endDate": contract.end_date.strftime('%Y-%m-%d'),
                    "createDate": contract.create_date.strftime('%Y-%m-%d %H:%M:%S'),
                    "exchangeRate": contract.travel_id.exchange_rate,
                    "duration": contract.travel_id.duration_id.value,
                    "paidAmount": contract.total_payment,
                    "paymentState": contract.state,
                    "people": travel_people
                }
 
                contract_list.append(contract_data)

            response = {'statusCode': 200, 'contracts': contract_list}
            return json.dumps(response)

