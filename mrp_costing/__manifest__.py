{
    'name': 'MRP Costing',
    'version': '13.0.1.0.0',
    'author': 'VPerfectCS',
    'category': 'Tools',
    'category':"""
    This Module Allows You To Calculate Product Final Cost Based on Manufacturing Order.
    """,
    'depends': [
        'mrp','account','hr','hr_timesheet',
    ],
    'data': [
        "security/security.xml",
        'security/ir.model.access.csv',
        'views/product_cost.xml',
        'data/seq.xml',
    ],
    "images": ["static/description/banner.gif"],
    'installable': True,
    'auto_install': False,
    'application': False,
}