# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
{
    'name': 'Product Mass Update Category',
    'version': '14.0.0.1',
    'category': 'Product',
    'author': 'Vperfect CS Pvt Ltd',
    'maintainer': 'VperfectCS',
    'website': 'http://www.vperfectcs.com',
    'sequence': 1,
    'summary': 'This will update the internal category  of the selected product .',
    'images': ['static/description/banner.png'],
    'description': """
        PRODUCT UPDATE
        ==============
        This module provide the updation functionality on the multiple selected product.

        Features :-
        ===========
        Easy to update multiple product category of the selected product.
        Easy to access through wizard.
        
    """,
    'depends': [
        'product',
    ],
    'data': [
        "security/ir.model.access.csv",
        "wizard/product_category_update_wizard_view.xml",
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'price' : 10,
    'currency' : 'EUR',
}
