# -*- coding: utf-8 -*-
# Odoo, Open Source Itm Material Theme.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).# 

import odoo
from odoo import fields, models, api
from odoo.http import request



class ResCompany(models.Model):
    _inherit = 'res.company'

    color_background = fields.Char('Select Theme Color', default="#337AB7")
    dashboard_background = fields.Binary(attachment=True)
    
    @api.multi
    def write(self, data):
        res = super(ResCompany, self).write(data)
        if data.get('color_background'):
            self.env['ir.qweb'].clear_caches()
        return res

    @api.model
    def create(self, data):
        res = super(ResCompany, self).write(data)
        if data.get('color_background'):
            self.env['ir.qweb'].clear_caches()
        return res


class Http(models.AbstractModel):
    _inherit = 'ir.http'


    def session_info(self):
        user = request.env.user
        display_switch_company_menu = user.has_group('base.group_multi_company') and len(user.company_ids) > 1
        version_info = odoo.service.common.exp_version()
        return {
            "session_id": request.session.sid,
            "uid": request.session.uid,
            "is_admin": request.env.user.has_group('base.group_system'),
            "is_superuser": request.env.user._is_superuser(),
            "user_context": request.session.get_context() if request.session.uid else {},
            "db": request.session.db,
            "server_version": version_info.get('server_version'),
            "server_version_info": version_info.get('server_version_info'),
            "name": user.name,
            "username": user.login,
            "company_id": request.env.user.company_id.id if request.session.uid else None,
            "partner_id": request.env.user.partner_id.id if request.session.uid and request.env.user.partner_id else None,
            "user_companies": {'current_company': (user.company_id.id, user.company_id.name), 'allowed_companies': [(comp.id, comp.name) for comp in user.company_ids]} if display_switch_company_menu else False,
            "currencies": self.get_currencies(),
            "custom_color" :  request.env.user.company_id.color_background or '#337AB7'
        }
    

    

