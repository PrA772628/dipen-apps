{
    'name': "Subcontracting Work Order without BOM",
    'summary': """Subcontracting in MRP Work Orders without BOM""",
    'description': """ Automatic PO to subcontractor from WO """,
    'author': "VperfectCS",
    'maintainer': 'VperfectCS',
    'website': "http://www.vperfectcs.com",
    'version': '14.0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['subcontracting_workorder'],
    'images': ['static/description/banner.png'],

    # always loaded
    'data': [
        'views/mrp_wo_subcontract.xml',
        'security/ir.model.access.csv',
    ],
        
    'installable': True,
    'auto_install': False,
    'application': True,
    'price': 29,
    'currency': 'EUR',
}
