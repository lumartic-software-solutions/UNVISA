from odoo import api, models,_
from datetime import datetime

class ReportAccountReport(models.AbstractModel):
    _name = 'report.custom_unvisa.custom_budget_template'
 
    @api.model
    def render_html(self, docids, data=None):
        budget_obj = self.env['crossovered.budget'].browse(docids[0])
        self.model = self.env.context.get('active_model')
        user = self.env["res.users"].browse(self._uid)
        from_date = budget_obj.create_date.split()
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': budget_obj,
            'doc' :user,
            'create_date' : from_date[0]
        }
        return self.env['report'].render('custom_unvisa.custom_budget_template', values=docargs)