# -*- coding: utf-8 -*-
{
    'name': 'watermark_pdf_report',
    'version': '1.0',
    'summary': "Watermark pdf report module",
    'sequence': 10,
    'author': "anand",
    'description': """
Add watermark to pdf reports
""",
    'category': 'Custom/Tools',
    'depends': [ 'base','web'],
    'data': [
        'views/settings.xml',
        'views/report_template.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'GPL-3',
}
