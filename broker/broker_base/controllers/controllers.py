# -*- coding: utf-8 -*-
# from odoo import http


# class BrokerBase(http.Controller):
#     @http.route('/broker_base/broker_base', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/broker_base/broker_base/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('broker_base.listing', {
#             'root': '/broker_base/broker_base',
#             'objects': http.request.env['broker_base.broker_base'].search([]),
#         })

#     @http.route('/broker_base/broker_base/objects/<model("broker_base.broker_base"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('broker_base.object', {
#             'object': obj
#         })

