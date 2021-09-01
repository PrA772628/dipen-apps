{
    'name': 'Easy Loan Management',
    'version': '14.0.1.0.0',
    'summary': 'Request For Loan',
    'sequence': 2,
    'description': """
    Easy loan management workflow Define Loan Type
    Add different loan types
    Add Loan Proofs or Required Documents List
    Loan Account Based on Loan Type
    Send Confirmation Notification to Loan Manager
    Manager can Approve Loan Request
    Account Link to Loan
    Loan Installment Summery journal entries
    Work Flow : Draft => Confirm => Approve => Disburse => Open => Close
    Send Due Installment Notification to Borrower
    Loan PDF Report
    Loan Summary PDF Report and View on Screen
    Loan Interest Certificate PDF Report
    """,
    'images': 'static/description/icon.png',
    'category': 'Loans',
    'author': 'Dipen Kanani',
    'maintainer': '',
    'website': 'www.EasyLoan.com',
    'license': '',
    'contributors': [
    ],
    'depends': ['base', 'hr', 'account','product'],
    'external_dependencies': {
    },
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'wizards/loan_reject.xml',
        'views/loan_proof_view.xml',
        'views/loan_type_view.xml',
        'views/loan_policy_view.xml',
        'views/loan_request_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
