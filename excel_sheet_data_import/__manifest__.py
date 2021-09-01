# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Excel Spreadsheet Import',
    'category': 'Extra Tools',
    'summary': "Excel or CSV Import to any Model with respect to update or Create Data or create fields",
    'version': '14.0.1.0.0',
    'author': 'VperfectCS',
    'website': 'http://www.vperfectcs.com',
    'description': """
The module adds the possibility to import data and create fields from Excel or CSV Sheet in odoo.
=================================================================================================
1. Create new records in only allowed model by Adminstrator
2. Update old record using selection of first till fifth column as record selector option in record view
3. Can create new fields which having 'x_' as prefix
4. Fully Flaxible and having User Access rights
5. Can have option to only Create or Create/Update both
6. New Field creation can support 'many2one', 'integer', 'float', 'char', 'text', 'date', 'datetime', 'boolean' types of fields
7. Update the sheet and use worksheets name to import data
8. Supported format are .csv,  .xls, .xlsx.
""",
    'support': 'info@vperfectcs.com',
    'depends': ['base'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/excel_spreadsheet_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'price': 99.00,
    'currency': 'EUR',
    'installable': True,
    'application': True,
}