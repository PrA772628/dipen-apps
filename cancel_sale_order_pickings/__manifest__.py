# -*- coding: utf-8 -*-
{
    'name': 'Cancel Sale Order Pickings',
    'category': 'Utility',
    'summary': 'This module allows to cancel 1 steps, 2 steps or 3 steps done pickings from sale order it selfs',
    'version': '14.0.1.1.0',
    'author': "VperfectCS",
    'maintainer': 'VperfectCS',
    'website': "http://www.vperfectcs.com",
    'description': """
        This module allows to cancel 1 steps, 2 steps or 3 steps done pickings from sale order it selfs
        """,
    'depends': ['sale_stock','delivery'],
    'images': ['static/description/banner.png'],
    'data': [
        'views/sale_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'price': 49,
    'currency': 'EUR',
}
