from odoo import api, fields, models, _, registry, SUPERUSER_ID
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp
import threading


#  Project Stage 
class ProjectStage(models.Model):
    _name = "project.stage"  
    
    name =  fields.Char(string='Name')
    fold = fields.Boolean(string='Folded in Kanban',
        help='This stage is folded in the kanban view when there are no records in that stage to display.')

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    
    project_id = fields.Many2one('project.project',string='Project')   
    
#  Project Method
class Project(models.Model):
    _inherit = "project.project"
    
    #  Compute Invoice Status Method
    @api.multi
    def _compute_invoice_status (self):
        for inv in self:
		    invoice_id = self.env['account.invoice'].search([('project_id','=',inv.id)])
		    if len(invoice_id) >= 1:
		        inv.invoice_status = 'invoiced'
		    else:
		        inv.invoice_status = 'no'
    
    invoice_status = fields.Selection([
        ('invoiced', 'To Invoice'),
        ('no', 'Nothing to Invoice')
        ], string='Invoice Status',compute="_compute_invoice_status" ,readonly=True)
    stage_id = fields.Many2one('project.stage',string='Stage')
    
    #  View Invoice Method
    @api.multi
    def view_project_invoice(self):
        invoice_id = self.env['account.invoice'].search([('project_id','=',self.id)])
        action = self.env.ref('account.action_invoice_tree').read()[0]
        if len(invoice_id) == 1:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoice_id.id
        elif len(invoice_id) > 1:
            action['domain'] = [('id', 'in', invoice_id.ids)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    #   For open Project form view from kanban
    @api.multi
    def view_project_project(self):
        project_id = self.env['project.project'].search([('id','=',self.id)])
        action = self.env.ref('custom_project.custom_project_view_project_all').read()[0]
        if project_id:
            action['views'] = [(self.env.ref('project.edit_project').id, 'form')]
            action['res_id'] = project_id.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    #  Add Followers when project created and set stage id Method
    @api.model
    def create(self, vals):
        stage_id = self.env['project.stage'].search([('name','=','Nuevo')],limit=1)
        if stage_id :
            vals.update({'stage_id' : stage_id.id})
        res = super(Project, self).create(vals)
        user_login_list = ['Tony','Marivi','Marcos']
        user_list = []
        for rec in user_login_list : 
            user_id = self.env['res.users'].search([('name', '=', rec)])
            if user_id:
                user_list.append(user_id.partner_id.id)
        mail_invite = self.env['mail.wizard.invite'].with_context({
            'default_res_model': 'project.project',
            'default_res_id': res.id
        }).create({
            'partner_ids': [(6,0,user_list)],
            'send_mail': True})
        mail_invite.add_followers()
        return res


        
# set customer reference in project
class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'
    
    @api.multi
    def project_create(self, vals):
        '''
        This function is called at the time of analytic account creation and is used to create a project automatically linked to it if the conditions are meet.
        '''
        self.ensure_one()
        Project = self.env['project.project']
        sale_id = self.env['sale.order'].search([('name', '=', vals.get('name'))])
        project = Project.with_context(active_test=False).search([('analytic_account_id', '=', self.id)])
        if not project and self._trigger_project_creation(vals):
            project_values = {
                'name': sale_id.client_order_ref or " ",
                'analytic_account_id': self.id,
                'use_tasks': True,
            }
            return Project.create(project_values).id
        return False

# set planned hours  in project task and create task of measurement lines
class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'
    
    def _create_service_task(self):
        project = self._get_project()
        planned_hours = self._convert_qty_company_hours()
        for j in self.sale_line_id:
            if j.check_measurement_line:
                for i in j.check_measurement_line:
                    task = self.env['project.task'].create({
                        'name': i.des_unit_measurement or 'Measurement Line',
                        'date_deadline': self.date_planned,
                        'planned_hours': (j.product_uom_qty * j.work_hours) or planned_hours,
                        'remaining_hours': planned_hours,
                        'partner_id': j.order_id.partner_id.id or self.partner_dest_id.id,
                        'user_id': j.order_id.user_id.id,
                        'procurement_id': self.id,
                        'description': self.name + '<br/>',
                        'project_id': project.id,
                        'company_id': self.company_id.id,
                        'task_line' : i.id,
                        'ud' : i.ud,
                        'length' : i.length,
                        'width' : i.width,
                        'height' : i.height,
                        'measurement_result' : i.measurement_result,
                        'description_pad' : j.name,
                        'state':'draft'
                    })
                self.write({'task_id' : task.id})
                msg_body = _("Task Created (%s): <a href=# data-oe-model=project.task data-oe-id=%d>%s</a>") % (self.product_id.name, task.id, task.name)
                self.message_post(body=msg_body)
                if self.sale_line_id.order_id:
                    self.sale_line_id.order_id.message_post(body=msg_body)
                    task_msg = _("This task has been created from: <a href=# data-oe-model=sale.order data-oe-id=%d>%s</a> (%s)") % (self.sale_line_id.order_id.id, self.sale_line_id.order_id.name, self.product_id.name)
                    task.message_post(body=task_msg)
                return task
            else:
                res = super(ProcurementOrder, self)._create_service_task()
                return res


#  manage timing fields with task
class ProjectTask(models.Model):
    _inherit = 'project.task'
    
    @api.one
    def _compute_partner_access(self):
        if self.user_has_groups('project.group_project_manager'):
            self.partner_access = False
        else :
            self.partner_access = True
    
    
    partner_access = fields.Boolean('Partner Access',compute='_compute_partner_access') 
    customer = fields.Char('Customer Name',related="partner_id.name")   
    address = fields.Char('Address',related="partner_id.street")    
    phone = fields.Char('Phone',related="partner_id.phone")  
    mobile = fields.Char('Mobile',related="partner_id.mobile")          
    email = fields.Char('Email',related="partner_id.email")          
    task_line = fields.Many2one('check.measurement.line', string="Task Line")
    start_time = fields.Datetime("Start Time")
    pause_time = fields.Datetime("Pause Time")
    con_time = fields.Datetime("Continue Time")
    end_time = fields.Datetime("End Time")
    restart_time = fields.Datetime("Restart Time")
    state = fields.Selection([('draft', 'New'), ('start', 'Start'), ('pause', 'Pause'), ('continue', 'Continue'), ('end', 'End'), ('stop', 'Stop')], string='Status', default='draft')
    length = fields.Float('Long')  
    width = fields.Float('Width')   
    height = fields.Float('Height') 
    ud = fields.Float('UD') 
#     internal_note = fields.Text('Internal Notes',related="sale_line_id.order_id.internal_note")
    measurement_result = fields.Float('Measurement result partial 1')
    invoice_status = fields.Selection([
        ('invoiced', 'Invoiced'),
        ('no', 'Nothing To Invoice')
        ], string='Invoice Status',default='no',readonly=True)
    
    @api.multi
    def stop_task(self):
        context = self._context
        if context.get('stop_task'):
            for i in self:
                i.write({'state' : 'stop'})
                
