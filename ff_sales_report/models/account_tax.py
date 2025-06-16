from odoo import fields, models


class AccountFiscalPositionInherit(models.Model):
    _inherit = "account.tax"
    _description = "Adding an boolean filed"

    tax_boolean = fields.Boolean("TAX Boolean")
