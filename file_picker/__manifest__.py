{
    'name': 'File Picker',
    'version': '12.0.1.0.0',
    'category': 'Choose Differnt Files',
    'author': 'Translation.ie',
    'website': 'https://www.translation.ie',
    'description': """
    This Module Allows Customer to Select Files from multiple platforms
    """,
    'depends': [
        'website','portal',
    ],
    'data': [
        'views/file_picker.xml',
        'views/settings.xml',
    ],
    'installable': True,
    'application': False,
}
