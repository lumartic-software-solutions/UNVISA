from odoo import api, fields, models, _
from odoo.exceptions import UserError,RedirectWarning


class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    work_hours = fields.Float(string='Work Hours')

class SaleOrder(models.Model):
    _inherit = "sale.order"


#     copy_measurement = fields.Boolean('Copy Measurement', default=False)
    is_partner = fields.Boolean('Is Partner', default=False,compute="_compute_is_partner")
    
    #  partner wise readonly orderline
    @api.depends('partner_id')
    @api.multi
    def _compute_is_partner(self):
        if  self.partner_id and self.state == 'draft':
            self.is_partner = True
        else:
            self.is_partner = False
    
    
    # Set Customer Reference In Sale Order 
    @api.model
    def default_get(self, vals):
        default_get_res = super(SaleOrder, self).default_get(vals)
        context = self._context
        if context.get('default_opportunity_id', ""):
            crm_id = self.env['crm.lead'].search([('id', '=', context['default_opportunity_id'])])
            default_get_res.update({'client_order_ref': crm_id.name})
        return default_get_res
    
    @api.multi
    def print_quotation(self):
        self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
        return self.env['report'].get_action(self, 'custom_unvisa.custom_sale_template')
        
    @api.model
    def create(self,vals):
        res = super(SaleOrder, self).create(vals)
        count = 0
        for i in res.order_line:
            count += 1
            values = {} 
            line_vals = []
            for j in i.check_measurement_line:
                values = {  
                    'des_unit_measurement' :j.des_unit_measurement,
                    'long' :j.long,
                    'height' :j.height,
                    'ud' :j.ud,
                    'measurement_result' :j.measurement_result,
                    }
                line_vals.append((0,0,values))
            line_obj = self.env['sale.order.line']
            if i.related_product:
                for p in i.related_product: 
                    group_id=False     
                    data  = {
                        'name': p.name,
                        'origin': vals.get('origin'),
                        'partner_id' : vals.get('partner_id'),
                        'order_id':res.id,
                        'product_id': p.id,
                        'product_qty': i.product_uom_qty,
                        'product_uom': i.product_uom.id,
                        'company_id': i.order_id.company_id.id,
                        'group_id': group_id,
                        'check_product_uom': i.check_product_uom,             
                        'check_measurement_line': line_vals,
                        'sequence' : count}
                    line_obj.create(data)
            i.sequence = count
        return res
    
    
    '''@api.multi
    def write(self,values):
        res = super(SaleOrder, self).write(values)
        order_line = {} 
        count = 0
        if values.get('order_line'): 
            count += 1
            for i in values['order_line']:
                value = {} 
                line_vals = []
                lines = self.env['sale.order.line'].browse(i[1])
                line_obj = self.env['sale.order.line']
                xyz = i[2]
                     
                if  xyz != False:
                  
                         
                    count += 1
                    if xyz.get('check_measurement_line'):
                        result1 = i[2]['check_measurement_line']
                        check_lines = result1[0][2] 
                        for j in result1:
                            value = {  
                                'des_unit_measurement' :check_lines['des_unit_measurement'],
                                'long' :check_lines['long'],
                                'height' :check_lines['height'],
                                'ud' :check_lines['ud'],
                                'measurement_result' :check_lines['measurement_result'],
                                }
                             
                            line_vals.append((0,0,value))
                    if xyz.get('related_product'):
                        result = i[2]['related_product']
                        abc = result[0][2]
                        for k in abc:
                            brw_product = self.env['product.product'].search([('id', '=' ,k)])
                            group_id=False     
                            for p in brw_product:
                                data  = {
                                    'name': p.name,
                                    'origin': values.get('origin'),
                                    'partner_id' : values.get('partner_id'),
                                    'order_id':self.id,
                                    'product_id':p.id,
                                    'product_uom_qty': xyz['product_uom_qty'],
                                    'product_uom': xyz['product_uom'],
                                    'group_id': group_id,
                                    'sale_line_id' : self.id,
                                    'check_product_uom': xyz['check_product_uom'],             
                                    'check_measurement_line': line_vals,
                                    'sequence' : count}
                                line_obj.create(data)
                
                    
        return res'''
# Set Measurement  In Sale Order Line           
class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"  
    
    # Compute Total Result 
    @api.depends('check_measurement_line.measurement_result')
    @api.multi
    def _total_result(self):
        for order in self:
            order.result = 0.0
            for line in order.check_measurement_line:
                order.result += line.measurement_result
                
    @api.depends('check_measurement_line.measurement_result')
    @api.multi
    def _compute_total_ud(self):
        for order in self:
            order.total_ud = 0.0
            for line in order.check_measurement_line:
                order.total_ud += line.ud
    
    
    copy_measurement = fields.Boolean('Copy Measurement', default=False) 
    check_product_uom = fields.Boolean('Check Product Uom', default=False)  
    check_measurement_line = fields.One2many('check.measurement.line', 'line_id', string="Measurement",copy=True)
    check_measurement = fields.Char("Check Measurement")
    measurement_line = fields.One2many('check.measurement.line', 'line_ids', string="Measurement",copy=True)
    result = fields.Float('Result', compute="_total_result")  
    work_hours = fields.Float(string='Work Hours')
    total_ud = fields.Integer("Total UD",compute="_compute_total_ud")
    related_product = fields.Many2many('product.product',string="Related Product")
    
    #Set copy measurement record in check measurement line
    @api.model
    def set_copy_measurement_record(self,product_uom):
        context = self._context
        if 'order_line' in context:
            order_line = context.get('order_line')
            if len(order_line) != 0 :
                lines = order_line[-1:]
                for line in lines:
                    # create method 
                    if line[1] == False :
                        measurement = line[2]['copy_measurement']
                        if measurement == True :
                            get_data = line[2]['check_measurement_line']
                            set_data = self.update_copy_measurement_result(get_data,product_uom)
                            self.check_measurement_line = set_data
                    # write method
                    else:
                        get_line = self.env['sale.order.line'].browse(line[1])
                        get_data = []
                        for rec in get_line:
                            measurement = False
                            if line[2] :
                                if 'copy_measurement' in  line[2] :
                                    measurement = line[2]['copy_measurement']
                            else:
                                measurement = rec.copy_measurement
                            if measurement == True :
                                for measurement_line in rec.check_measurement_line:
                                    val = {                                           
                                      'custom': measurement_line.custom ,
                                      'des_unit_measurement': measurement_line.des_unit_measurement,
                                      'height': measurement_line.height,
                                      'long': measurement_line.long,
                                      'measurement_result': measurement_line.measurement_result,
                                      'new_height': measurement_line.new_height,
                                      'new_long': measurement_line.new_long,
                                      'ud': measurement_line.ud,
                                       }
                                    get_data.append((0,0,val))
                                    set_data = self.update_copy_measurement_result(get_data,product_uom)
                                    self.check_measurement_line = set_data
    
    #  update copy measurement result in check measurement line
    @api.model            
    def update_copy_measurement_result(self,get_data,product_uom):
        if get_data :
            for data in get_data :
                uom_result = self.env['product.uom'].search([('id','=',product_uom)],limit=1)
                if uom_result :
                    data[2]['custom'] =  uom_result.name
                    if uom_result.name == "ml":
                        measurement_result = (data[2]['long'] * data[2]['ud'] ) or 0.0
                    elif uom_result.name == "ML":
                        measurement_result = (data[2]['long'] + data[2]['height'])
                        total = measurement_result * data[2]['ud'] * 2 or 0.0
                        measurement_result = total
                    elif uom_result.name == "m" or uom_result.name == "m2" or uom_result.name == "m3" or uom_result.name == "m2l" or uom_result.name == "m2L": 
                        if data[2]['new_long'] and data[2]['new_height']:
                            total = data[2]['new_long'] * data[2]['new_height']
                            measurement_result = total * data[2]['ud'] * 0.0001 or 0.0
                        else:
                            total = data[2]['long'] + data[2]['height']
                            measurement_result = (2 * data[2]['ud'] * total) / 100 or 0.0
                    data[2]['measurement_result'] = measurement_result  
            return get_data     
            
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return 
        else:
            if self.product_id.type == 'service':
                self.work_hours = self.product_id.work_hours
            else:
                self.work_hours = 0.00
        if not self.order_id:
            return
        part = self.order_id.partner_id
        if not part:
            warning = {
                    'title': _('Warning!'),
                    'message': _('You must first select a partner!'),
                }
            return {'warning': warning}
    
    # Set Order Quantity
    @api.multi
    @api.onchange('result')
    def onchange_result(self):
        self.product_uom_qty = self.result
        if self.product_uom.name == 'ML':
                self.product_uom_qty = self.result/100
    
    
    
    # Set Product Uom  for Measurement  
    @api.multi
    @api.onchange('product_uom')
    def onchange_product_uom(self):
        if  self.product_uom :
            self.check_measurement = self.product_uom.name
            if self.product_uom.name == 'ML' or  self.product_uom.name == 'ml' or self.product_uom.name == 'm'  or self.product_uom.name == 'm3' or self.product_uom.name == 'm2' or self.product_uom.name == 'm2l' or self.product_uom.name == 'm2L':
                #set copy measurement record 
                self.set_copy_measurement_record(self.product_uom.id)
                self.check_product_uom = True
            else:    
                self.check_product_uom = False
    
                
    
    # Set Check Measurement Line  In Invoice Line     
    @api.multi
    def _prepare_invoice_line(self, qty):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        res = {}
        account = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id
        if not account:
            raise UserError(_('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') % 
                (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))

        fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
        if fpos:
            account = fpos.map_account(account)
        line_vals = []
        for lines in self.check_measurement_line:
            values = {  'des_unit_measurement' :lines.des_unit_measurement,
                        'long' :lines.long,
                        'height' :lines.height,
                        'new_long' : lines.new_long,
                        'new_height' : lines.new_height,
                        'ud' :lines.ud,
                        'measurement_result' :lines.measurement_result,
                                    }
            line_vals.append(values)
        res = {
            'name': self.name,
            'sequence': self.sequence,
            'origin': self.order_id.name,
            'account_id': account.id,
            'price_unit': self.price_unit,
            'quantity': qty,
            'discount': self.discount,
            'uom_id': self.product_uom.id,
            'product_id': self.product_id.id or False,
            'layout_category_id': self.layout_category_id and self.layout_category_id.id or False,
            'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
            'account_analytic_id': self.order_id.project_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'check_product_uom': self.check_product_uom,
            'check_measurement_line': [(0, 0, data) for data in line_vals],
            'copy_measurement' : self.copy_measurement
        }
        return res
    
# Check Measurement Line  To Set Multiple  Measurement 
class CheckMeasurementLine(models.Model):
    _name = 'check.measurement.line' 
    
    @api.depends('long')
    @api.multi
    def _compute_long(self):
        for l in self:
            count_long = l.long / 6
            digit = int(count_long)
            if l.long % 6 != 0.0:
                digit += 1
            l.new_long = digit * 6
            
    @api.depends('height')
    @api.multi
    def _compute_height(self):
        for l in self:
            count_height = l.height / 6
            digit = int(count_height)
            if l.height % 6 != 0.0:
                digit += 1
            l.new_height = digit * 6
                
    @api.multi
    @api.onchange('long' ,'height')
    def onchange_calculation(self):
        for i in self:
            if i.long:
                i._compute_long()
            if i.height:
                i._compute_height()
        return
    
    line_id = fields.Many2one('sale.order.line', string='Order lines')
    line_ids = fields.Many2one('sale.order.line', string='Order lines')
    invoice_line_id = fields.Many2one('account.invoice.line', string='Invoice lines')
    budget_line_id = fields.Many2one('crossovered.budget.lines',string='Budget Lines')
    des_unit_measurement = fields.Text('Description')  
    long = fields.Float('Long', default=1.0)  
    height = fields.Float('Height', default=1.0)
    new_long = fields.Float('Long',default=0.0)
    new_height = fields.Float('Height',default=0.0)
    ud = fields.Float('UD' , required=True, default=1.0) 
    measurement_result = fields.Float('Measurement result partial 1 ')
    custom = fields.Char('custom', default=lambda self: self._context.get('check_uom')) 
    
    # Calculate Measurement  
    @api.multi
    @api.onchange('ud', 'long' ,'height','new_long','new_height')
    def onchange_measurement(self):
        context = dict(self._context)
        if 'check_uom' in context:
            uom_result = self.env['product.uom'].search([('name','=',context.get('check_uom'))],limit=1)
            if uom_result.name == "ml":
                self.measurement_result = (self.long * self.ud) or 0.0
            elif uom_result.name == "ML":
                measurement_result = (self.long + self.height )
                total = measurement_result * self.ud * 2 or 0.0
                self.measurement_result = total
            elif uom_result.name == "m" or uom_result.name == "m2" or uom_result.name == "m3" or uom_result.name == "m2l" or uom_result.name == "m2L": 
                if self.new_long and self.new_height:
                    total = self.new_long * self.new_height
                    self.measurement_result = total * self.ud * 0.0001 or 0.0
                else:
                    total = self.long + self.height
                    self.measurement_result = (2 * self.ud * total) / 100 or 0.0
        return {}
    
        
        
class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    
#     copy_measurement = fields.Boolean('Copy Measurement', default=False)
    is_partner = fields.Boolean('Is Partner', default=False,compute="_compute_is_partner")
    
    @api.multi
    def invoice_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        self.ensure_one()
        self.sent = True
        return self.env['report'].get_action(self, 'custom_unvisa.custom_invoice_template')

    #  partner wise readonly invoiceline
    @api.depends('partner_id')
    @api.multi
    def _compute_is_partner(self):
        for part in self:
            if  part.partner_id and part.state == 'draft':
                part.is_partner = True
            else:
                part.is_partner = False
        
        
class AccountInvoiceLines(models.Model):
    _inherit = 'account.invoice.line'
    
    @api.depends('check_measurement_line.measurement_result')
    @api.multi
    def _total_resultinvoice(self):
        for i in self:
            i.results = 0.0
            for l in i.check_measurement_line:
                i.results += l.measurement_result
    
    @api.depends('check_measurement_line.measurement_result')
    @api.multi
    def _compute_total_ud(self):
        for order in self:
            order.total_ud = 0.0
            for line in order.check_measurement_line:
                order.total_ud += line.ud
        
    copy_measurement = fields.Boolean('Copy Measurement', default=False)
    check_product_uom = fields.Boolean('Check Product Uom', default=False)  
    check_measurement_line = fields.One2many('check.measurement.line', 'invoice_line_id', string="Measurement")
    total_ud = fields.Integer("Total UD",compute="_compute_total_ud")
    results = fields.Float('Result', compute="_total_resultinvoice")
    check_measurement = fields.Char("Check Measurement")
    sale_order_no = fields.Char(related='sale_line_ids.order_id.name',string="Order No",readonly=True)
    
    @api.multi
    @api.onchange('results')
    def onchange_results(self):
        self.quantity = self.results
        if self.uom_id.name == 'ML':
                self.quantity = self.results/100
    
    # Set Product Uom  for Measurement In Invoice Line
    @api.multi
    @api.onchange('uom_id')
    def onchange_product_uom(self):
        if  self.uom_id :
            self.check_measurement = self.uom_id.name
            if self.uom_id.name == 'ML' or self.uom_id.name == 'ml' or self.uom_id.name == 'm' or self.uom_id.name == 'ml'  or self.uom_id.name == 'm3' or self.uom_id.name == 'm2' or self.uom_id.name == 'm2l' or self.uom_id.name == 'm2L':
                #  set copy measurement record
                self.set_copy_measurement_record(self.uom_id.id)
                self.check_product_uom = True
            else:    
                self.check_product_uom = False
                
    #Set copy measurement record in check measurement line
    @api.model
    def set_copy_measurement_record(self,product_uom):
        context = self._context
        if 'invoice_line_ids' in context:
            invoice_line = context.get('invoice_line_ids')
            if len(invoice_line) != 0 :
                lines = invoice_line[-1:]
                for line in lines:
                    # create method 
                    if line[1] == False :
                        measurement = line[2]['copy_measurement']
                        if measurement == True :
                            get_data = line[2]['check_measurement_line']
                            set_data = self.update_copy_measurement_result(get_data,product_uom)
                            self.check_measurement_line = set_data
                    # write method
                    else:
                        get_line = self.env['account.invoice.line'].browse(line[1])
                        get_data = []
                        for rec in get_line:
                            measurement = False
                            if line[2] :
                                if 'copy_measurement' in  line[2] :
                                    measurement = line[2]['copy_measurement']
                            else:
                                measurement = rec.copy_measurement
                            if measurement == True :
                                for measurement_line in rec.check_measurement_line:
                                    val = {                                           
                                      'custom': measurement_line.custom ,
                                      'des_unit_measurement': measurement_line.des_unit_measurement,
                                      'height': measurement_line.height,
                                      'long': measurement_line.long,
                                      'measurement_result': measurement_line.measurement_result,
                                      'new_height': measurement_line.new_height,
                                      'new_long': measurement_line.new_long,
                                      'ud': measurement_line.ud,
                                       }
                                    get_data.append((0,0,val))
                                    set_data = self.update_copy_measurement_result(get_data,product_uom)
                                    self.check_measurement_line = set_data
    
    #  update copy measurement result in check measurement line
    @api.model            
    def update_copy_measurement_result(self,get_data,product_uom):
        if get_data :
            for data in get_data :
                uom_result = self.env['product.uom'].search([('id','=',product_uom)],limit=1)
                if uom_result :
                    data[2]['custom'] =  uom_result.name
                    if uom_result.name == "ml":
                        measurement_result = (data[2]['long'] * data[2]['ud'] ) or 0.0
                    elif uom_result.name == "ML":
                        measurement_result = (data[2]['long'] + data[2]['height'])
                        total = measurement_result * data[2]['ud'] * 2 or 0.0
                        measurement_result = total
                    elif uom_result.name == "m" or uom_result.name == "m2" or uom_result.name == "m3" or uom_result.name == "m2l" or uom_result.name == "m2L": 
                        if data[2]['new_long'] and data[2]['new_height']:
                            total = data[2]['new_long'] * data[2]['new_height']
                            measurement_result = total * data[2]['ud'] * 0.0001 or 0.0
                        else:
                            total = data[2]['long'] + data[2]['height']
                            measurement_result = (2 * data[2]['ud'] * total) / 100 or 0.0
                    data[2]['measurement_result'] = measurement_result  
            return get_data 
                
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

# set planned hours  in project task
class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'
    
    def _create_service_task(self):
        project = self._get_project()
        planned_hours = self._convert_qty_company_hours()
        task = self.env['project.task'].create({
            'name': '%s:%s' % (self.origin or '', self.product_id.name),
            'date_deadline': self.date_planned,
            'planned_hours': (self.sale_line_id.product_uom_qty * self.sale_line_id.work_hours) or planned_hours,
            'remaining_hours': planned_hours,
            'partner_id': self.sale_line_id.order_id.partner_id.id or self.partner_dest_id.id,
            'user_id': self.env.uid,
            'procurement_id': self.id,
            'description': self.name + '<br/>',
            'project_id': project.id,
            'company_id': self.company_id.id,
        })
        self.write({'task_id': task.id})
        msg_body = _("Task Created (%s): <a href=# data-oe-model=project.task data-oe-id=%d>%s</a>") % (self.product_id.name, task.id, task.name)
        self.message_post(body=msg_body)
        if self.sale_line_id.order_id:
            self.sale_line_id.order_id.message_post(body=msg_body)
            task_msg = _("This task has been created from: <a href=# data-oe-model=sale.order data-oe-id=%d>%s</a> (%s)") % (self.sale_line_id.order_id.id, self.sale_line_id.order_id.name, self.product_id.name)
            task.message_post(body=task_msg)

        return task

                
class UnvisaBudgetLine(models.Model):
    _inherit = 'crossovered.budget.lines'
    
    check_measurement_line = fields.One2many('check.measurement.line', 'budget_line_id', string="Measurement")
    check_product_uom = fields.Boolean('Check Product Uom', default=False)
    
#set active category in section
class Layoutsale(models.Model):
    _inherit = "sale.layout_category"
    
    active_categ = fields.Boolean(string='Active')  

class StockMove(models.Model):
    _inherit = "stock.move"
         
    check_measurement_line = fields.One2many(related='procurement_id.sale_line_id.check_measurement_line', string="Measurement")

class StockPackOperation(models.Model):
    _inherit = "stock.pack.operation"
         
    check_measurement_line = fields.One2many(related='linked_move_operation_ids.move_id.procurement_id.sale_line_id.check_measurement_line', string="Measurement")
