{
    'name': "Subcontracting with product configuration on BOM",
    'summary': """Subcontracting in MRP""",
    'description': """ Automatic PO, delivery and receipt to subcontractor from MO """,
    'author': "VperfectCS",
    'maintainer': 'VperfectCS',
    'website': "http://www.vperfectcs.com",
    'version': '14.0.1.1.0',

    # any module necessary for this one to work correctly
    'depends': ['mrp','purchase','sale_management','mrp_subcontracting'],
    'images': ['static/description/banner.png'],

    # always loaded
    'data': [
        'views/manufacture_subcontract.xml',
        'views/purchase_subcontract.xml',
        'security/ir.model.access.csv',
        
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'price': 49,
    'currency': 'EUR',
}