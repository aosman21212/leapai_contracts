# -*- coding: utf-8 -*-
{
    'name': 'LeapAI Unified Contracts System',
    'version': '19.0.1.0.0',
    'category': 'Contracts',
    'summary': 'نظام العقود الموحد — وزارة الطاقة السعودية | Unified Contract System — Saudi Ministry of Energy',
    'description': """
LeapAI Unified Contracts System
================================
Complete contract lifecycle management for Saudi Arabia:

• Tender & Bidding — Manage tenders, invite bidders, evaluate bids, award (المناقصات)
• Contract Management — Lump sum, unit rate, turnkey; amendments; tracking (العقود)
• Payment Certificates — Interim (IPC) & Final (FPC) with VAT, retention, advance recovery (شهادات الدفع)
• Bank Guarantees & Bonds — Bid bond, performance, advance, retention/maintenance (الضمانات)
• Saudi-specific — SAR, VAT 15%, Nitaqat, CR, IBAN, regional classification
• Bilingual — Arabic (RTL) & English

Contact
-------
Location : King Abdulaziz Branch Road, Riyadh, Saudi Arabia
Email    : sales@leapai.ai
Phone    : +966 53 553 3627
Website  : https://leapai.ai/

Developer
---------
Abdulkaraim Osman — Tech Manager | Backend Engineer | DevOps Engineer
Bab International Corp For Specialized Services
LinkedIn : https://www.linkedin.com/in/abdulkaraim-o-385b7a110/
    """,
    'author': 'LeapAI / Abdulkaraim Osman — Bab International Corp',
    'website': 'https://leapai.ai/',
    'support': 'sales@leapai.ai',
    'license': 'LGPL-3',
    'application': True,
    'depends': ['mail', 'account'],
    'data': [
        'security/contracts_security.xml',
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'views/contract_tender_views.xml',
        'views/contract_bid_views.xml',
        'views/contract_contract_views.xml',
        'views/contract_amendment_views.xml',
        'views/contract_payment_certificate_views.xml',
        'views/contract_guarantee_views.xml',
        'views/menu.xml',
    ],
    'demo': ['demo/demo_data.xml'],
    'images': [
        'static/description/screen_contract.png',
        'static/description/screen_ipc.png',
        'static/description/screen_guarantees.png',
    ],
    'installable': True,
    'auto_install': False,
}
