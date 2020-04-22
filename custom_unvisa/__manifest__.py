{
    'name': ' Custom Unvisa',
    'category': 'Sale',
    'author': 'ITMusketeers Consultancy Services LLP',
    'description': """
================================================================================

1.Opportunity Name to Customer Reference.
2.Changes in U.O.M.
3.Display of quotes, sales orders and invoices.
4.Design of quotation, orders of sale and invoices.
================================================================================
""",
    'depends': ['stock','project', 'sales_team', 'product', 'web', 'base', 'sale', 'crm', 'report', 'sale_timesheet', 'sale_crm', 'account', 'account_accountant','account_budget'],
    'summary': ' Customization in Sale and Invoice. ',

    'data': [
            'views/custom_unvisa_view.xml',
            'views/assets.xml',
            'views/res_company_view.xml',
            'views/sale_report_template.xml',
            'views/custom_header_layout.xml',
		    'views/invoice_template.xml',
            'custom_report.xml',
            'views/budget_report.xml',
            'views/delivery_report_template.xml',
             ],

    'installable': True,
}
