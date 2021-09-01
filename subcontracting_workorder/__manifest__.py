{
    'name': "Subcontracting in Work Orders",
    'summary': """Subcontracting in MRP Work Orders""",
    'description': """ Automatic PO to subcontractor from WO """,
    'author': "VperfectCS",
    'maintainer': 'VperfectCS',
    'website': "http://www.vperfectcs.com",
    'version': '14.0.2.0.0',

    # any module necessary for this one to work correctly
    'depends': ['mrp','purchase','sale_management','subcontracting'],
    'images': ['static/description/banner.png'],

    # always loaded
    'data': [
        'views/mrp_wo_subcontract.xml',
    ],
        
    'installable': True,
    'auto_install': False,
    'application': True,
    'price': 49,
    'currency': 'EUR',
}
