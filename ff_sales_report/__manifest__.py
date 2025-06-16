{
    "name": "Sales PDF Report",
    "version": "17.0.1.0.0",
    "summary": "Sales PDF Report",
    "category": "Sales",
    "author": "ForeFront Technologies",
    "depends": ["base", "sale"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/sales_report_wizard.xml",
        "report/sales_report.xml",
        "views/account_tax.xml",
    ],
    "license": "LGPL-3",
    "images": [],
    "installable": True,
    "auto_install": False,
    "application": True,
}
