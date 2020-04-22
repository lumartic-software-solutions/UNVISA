{
    'name': 'Custom Project',
    'category': 'Project',
    'author': 'ITMusketeers Consultancy Services LLP',
    'description': """
================================================================================

To Change the functionality of Project And Task.
================================================================================
""",
    'depends': ['project', 'contacts','sales_team', 'product', 'web', 'base', 'sale', 'crm', 'report', 'sale_timesheet', 'sale_crm', 'account', 'account_accountant','kanban_draggable'],
    'summary': 'To Generate custom oroval',

    'data': [
        'wizard/create_project_invoice_wizard.xml',
        'wizard/custom_wizard.xml',
		'views/custom_task_view.xml',
		'views/project_view.xml',
		
            
             ],

    'installable': True,
}
