{
    "name": "Google Sheet SQL Export",
    "version": "12.0.1.0.0",
    "category": "Extra Tools",
    "author": "VperfectCS",
    "website": "http://vperfectcs.com/",
    "summary": "Google Spreadsheet Export to any Model data with respect to Create Data in Google Sheet",
    "description": """
The module adds the possibility to Export data and create fields from odoo in Google Spreadsheet.
=================================================================================================
1. Export/update Any Model Data From Odoo To Google Spreadsheet.
2. Create new Sheet and worksheet using odoo it self and also get URL directly in odoo record.
3. You can Create worksheet or update it also.
4. Create your own custom data using SQL Query Write.
""",
    "support": "info@vperfectcs.com",
    "depends": ["mail"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/google_sheet_data.xml",
        "views/google_spreadsheet_views.xml",
        "views/settings.xml",
    ],
    "external_dependencies": {
        "python": [
            "pandas",
            "tabulate",
            "gspread",
            "httplib2",
            "oauth2client",
        ],
    },
    "images": ["static/description/banner.png"],
    "installable": True,
    "application": True,
    "price": 99.00,
    "currency": "EUR",
}
