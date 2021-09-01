{
    'name': "Subcontracting",
    'summary': """Subcontracting in MRP""",
    'description': """ Automatic PO to subcontractor from MO """,
    'author': "VperfectCS",
    'maintainer': 'VperfectCS',
    'website': "http://www.vperfectcs.com",
    'version': '13.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['mrp','purchase','sale_management','mrp_subcontracting'],
    'images': ['static/description/banner.png'],

    # always loaded
    'data': [
        'views/manufacture_subcontract.xml',
        'views/purchase_subcontract.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'price': 49,
    'currency': 'EUR',
}