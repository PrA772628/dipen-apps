{
    'name': 'Google Sheet Import API',
    'version': '13.0.1.1.0',
    'category': 'Extra Tools',
    'author' : 'VperfectCS',
    'website' : 'http://vperfectcs.com/',
    'summary': "Google Spreadsheet Import to any Model with respect to update or Create Data or create fields",
    'description': """
The module adds the possibility to import data and create fields from Google Spreadsheets in odoo.
=================================================================================================
1. Create new records in any model
2. Update old record using first column as record selector
3. Can create new fields which having 'x_' as prefix
4. Fully Flaxible and having User Access rights
5. Cron job is makes you uptodate with sheet Data
6. New Field creation can support 'integer', 'float', 'char', 'text', 'date', 'datetime', 'boolean' types of fields
""",
    'support': 'info@vperfectcs.com',
    'depends': ['base'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/google_sheet_data.xml',
        'views/google_spreadsheet_views.xml',
        'views/settings.xml',
    ],
    'external_dependencies' : {
        'python' : [
            'gspread', 
            'oauth2client', 
            'httplib2'
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'price' : 99.00,
    'currency' : 'EUR',
}