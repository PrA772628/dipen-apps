{
    'name': 'Google Sheet Export API',
    'version': '12.0.1.1.0',
    'category': 'Extra Tools',
    'author' : 'VperfectCS',
    'website' : 'http://vperfectcs.com/',
    'summary': "Google Spreadsheet Export to any Model data with respect to update or Create Data in Google Sheet",
    'description': """
The module adds the possibility to Export data and create fields from odoo in Google Spreadsheet.
=================================================================================================
1. Export/Update Any Model Data From Odoo To Google Spreadsheet.
2. Create new Sheet and worksheet using odoo it self and also get URL directly in odoo record.
3. You can Create worksheet or update it also.
4. Select your data using Filter option
5. There are selection of Models and Fields with sequence handler.
""",
    'support': 'info@vperfectcs.com',
    'depends': [
        'google_sheet_data_import'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/google_sheet_data.xml',
        'views/google_spreadsheet_views.xml',
    ],
    'external_dependencies' : {
        'python' : [
            'pandas'
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'price' : 99.00,
    'currency' : 'EUR',
}