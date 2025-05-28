import logging
from odoo import api, models, _
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta, time
from odoo.tools import image_data_uri
from markupsafe import Markup


_logger = logging.getLogger(__name__)

class ContractDetailPdfNew(models.AbstractModel):
    _name = 'report.broker_contract.contract_detail_pdf_new4'
    _description = 'Broker Contract Pdf'

    def _get_report_values(self, docids, data=None):
        _logger.info("docids: %s", docids)
        contracts = self.env['contracts'].browse(docids)
        contract_data = {}

        for contract in contracts:
            now_date = (datetime.now()).strftime('%Y-%m-%d')
            contract_data['template_text'] = contract.product_id.template_text
            contract_data['template_body'] = contract.product_id.template_body

            contract_data['header'] = contract.product_id.name.upper()
            contract_data['insurance_logo'] = contract.insurance_id.image_1920
            contract_data['insurance_slug'] = contract.insurance_type_id.slug
            stamp_data = self.env['res.company'].browse(1).stamp or False 
            image_url = ""
            if stamp_data:
                image_url = image_data_uri(stamp_data)
        

            if(contract.product_id.template_text):
                contract_data['template_text'] = contract_data['template_text'].replace('<p></p>', '')
                contract_data['template_text'] = contract_data['template_text'].replace('$contract_number', contract.contract_number or '')
                contract_data['template_text'] = contract_data['template_text'].replace('$insurance_name', contract.insurance_id.name or '')
                contract_data['template_text'] = contract_data['template_text'].replace('$insurance_type_name', contract.insurance_type_id.name or '' )
                contract_data['template_text'] = contract_data['template_text'].replace('$product_name', contract.product_id.name or '')
                contract_data['template_text'] = contract_data['template_text'].replace('$create_date', contract.create_date.strftime('%Y.%m.%d'))
                contract_data['template_text'] = contract_data['template_text'].replace('$start_date', contract.start_date.strftime('%Y.%m.%d'))
                contract_data['template_text'] = contract_data['template_text'].replace('$end_date', contract.end_date.strftime('%Y.%m.%d'))
                
                contract_data['template_text'] = contract_data['template_text'].replace('$customer_surname', contract.customer_surname or '')
                contract_data['template_text'] = contract_data['template_text'].replace('$customer_name', contract.customer_name)
                contract_data['template_text'] = contract_data['template_text'].replace('$customer_registerno', contract.customer_registerno or '')
                contract_data['template_text'] = contract_data['template_text'].replace('$customer_phone', contract.customer_phone or '')
                contract_data['template_text'] = contract_data['template_text'].replace('$customer_email', contract.customer_email or '')
                contract_data['template_text'] = contract_data['template_text'].replace('$customer_birthday', str(contract.customer_birthday) if contract.customer_birthday else '')
                contract_data['template_text'] = contract_data['template_text'].replace('$customer_address', contract.customer_street or '')
                contract_data['template_text'] = contract_data['template_text'].replace('$work_address', contract.customer_street2 or '')
                contract_data['template_text'] = contract_data['template_text'].replace('$customer_position', contract.customer_passport or '')

                contract_data['template_text'] = contract_data['template_text'].replace('$emergency_contact_name', contract.emergency_contact_name or '')
                contract_data['template_text'] = contract_data['template_text'].replace('$emergency_contact_phone', contract.emergency_contact_phone or '')
                # insurer2_name = contract.user_id.partner_id.surname or '' +' '+ contract.user_id.partner_id.name or ''
                insurer_name = self.env['res.company'].browse(1).name
                insured_name = contract.customer_surname +' '+ contract.customer_name if contract.customer_surname else contract.customer_name
                contract_data['template_text'] = contract_data['template_text'].replace('$insurer_name', insurer_name)
                contract_data['template_text'] = contract_data['template_text'].replace('$insured_name', insured_name)
                contract_data['template_text'] = contract_data['template_text'].replace('$country', contract.travel_id.country or '')
                duty_liable_suffex = '%' if contract.customer_duty_liable_type == 'percent' else ''
                contract_data['template_text'] = contract_data['template_text'].replace('$customer_duty_liable', f'{contract.customer_duty_liable_amount:,}' + duty_liable_suffex or '')
                
                contract_data['template_text'] = contract_data['template_text'].replace('$valuation', f'{contract.valuation:,}')
                contract_data['template_text'] = contract_data['template_text'].replace('$payment_percent', f'{contract.payment_fee_percent:,}')
                contract_data['template_text'] = contract_data['template_text'].replace('$payment', f'{contract.payment:,}')
                contract_data['template_text'] = contract_data['template_text'].replace('$discount', f'{contract.discount_amount:,}')
                contract_data['template_text'] = contract_data['template_text'].replace('$payable', f'{contract.total_payment:,}')
                contract_data['template_text'] = contract_data['template_text'].replace('$paid', f'{contract.paid:,}')
                contract_data['template_text'] = contract_data['template_text'].replace('$user_name', contract.user_id.partner_id.surname or '' +' '+ contract.user_id.partner_id.name or '')
                contract_data['template_text'] = contract_data['template_text'].replace('user_mobile', contract.user_id.partner_id.mobile or '')
               

                if(contract.insurance_type_id.slug == 'travel'):
                    contract_data['template_text'] = contract_data['template_text'].replace('$duration', contract.travel_id.duration_id.name or '')
                    contract_data['template_text'] = contract_data['template_text'].replace('$passport', contract.travel_id.passport or '')
                    contract_data['template_text'] = contract_data['template_text'].replace('$travel_date', contract.travel_id.travel_date.strftime('%Y.%m.%d') or '')
                    contract_data['template_text'] = contract_data['template_text'].replace('$purpose', contract.travel_id.purpose or '')
                    contract_data['template_text'] = contract_data['template_text'].replace('$zone', contract.travel_id.country_zone_id.name or '')
                    contract_data['template_text'] = contract_data['template_text'].replace('$exchange_rate', f'{contract.travel_id.exchange_rate:,}' or '')
                    has_covid_protection = 'Тийм' if contract.has_covid_protect else 'Үгүй'
                    contract_data['template_text'] = contract_data['template_text'].replace('$covid_protect', has_covid_protection)
                    contract_data['template_text'] = contract_data['template_text'].replace('$valuation', 'USD ' + f'{contract.valuation:,}')
                    payment_prefix = 'MNT ' if contract.travel_id.exchange_rate > 0 else 'USD '
                    contract_data['template_text'] = contract_data['template_text'].replace('$payment', payment_prefix + f'{contract.payment:,}')
                    contract_data['template_text'] = contract_data['template_text'].replace('$discount', payment_prefix + f'{contract.discount_amount:,}')
                    contract_data['template_text'] = contract_data['template_text'].replace('$payable', payment_prefix + f'{contract.total_payment:,}')
                    contract_data['template_text'] = contract_data['template_text'].replace('$paid', f'{contract.paid:,}')
                elif(contract.insurance_type_id.slug == 'car'):
                    contract_data['template_text'] = contract_data['template_text'].replace('$plate_number', contract.car_id.state_number or '')
                    contract_data['template_text'] = contract_data['template_text'].replace('$cabin_number', contract.car_id.cabin_number or '')
                    contract_data['template_text'] = contract_data['template_text'].replace('$build_date', contract.car_id.build_year or '')
                    contract_data['template_text'] = contract_data['template_text'].replace('$car_mark', contract.car_id.car_mark_name or '')
                    contract_data['template_text'] = contract_data['template_text'].replace('$car_model', contract.car_id.car_model_name or '')
                    contract_data['template_text'] = contract_data['template_text'].replace('$import_date', contract.car_id.imported_year or '')
                    contract_data['template_text'] = contract_data['template_text'].replace('$color', contract.car_id.color or '')
                
                img_base64 = Markup(f'<img src="{image_url}" alt="Car Image" style="width:130px !important; height: auto;" />')
                template_text = contract_data['template_text'].replace('$company_stamp', img_base64)
                contract_data['template_text'] = Markup(template_text)
                
            if(contract.product_id.template_body):
                contract_data['template_body'] = contract_data['template_body'].replace('<p></p>', '')
                contract_data['template_body'] = contract_data['template_body'].replace('$user_name', contract.user_id.partner_id.surname or '' +' '+ contract.user_id.partner_id.name or '')
                contract_data['template_body'] = contract_data['template_body'].replace('$customer_surname', contract.customer_surname or '')
                contract_data['template_body'] = contract_data['template_body'].replace('$customer_name', contract.customer_name)
                template_text = contract_data['template_body'].replace('$company_stamp', img_base64)
                contract_data['template_body'] = Markup(template_text)


        return {    
            'docs': [contract_data]
        }
            
