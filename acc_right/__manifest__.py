# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Access_right for Product',
    'version': '13.0.1.0.0',
    'category': 'Extra Tools',
    'description': """
        for creating product """,
    'depends': ['product','stock','account','purchase','sale_management'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
}