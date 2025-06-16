import calendar
from datetime import datetime

from odoo import _, fields, models
from odoo.exceptions import UserError


class SalesReport(models.TransientModel):
    _name = "custom.sales.report"
    _description = "Sales Report"

    custom = fields.Selection(
        [("monthly", "Monthly"), ("yearly", "Yearly"), ("custom", "Custom")],
        string="Filter",
    )
    start_date = fields.Date(string="Start-Date")
    end_date = fields.Date(string="End-Date")
    yearly = fields.Selection(
        [(str(num), str(num)) for num in range(2023, 2031)],
        string="Year",
        default=str(datetime.now().year),
    )
    monthly = fields.Selection(
        [
            ("1", "January"),
            ("2", "February"),
            ("3", "March"),
            ("4", "April"),
            ("5", "May"),
            ("6", "June"),
            ("7", "July"),
            ("8", "August"),
            ("9", "September"),
            ("10", "October"),
            ("11", "November"),
            ("12", "December"),
        ],
        string="Select Month",
    )

    def _prepare_report_data(self):
        payment_method_totals_dct = {}
        grand_totals = {
            "excl_vat_total": 0.0,
            "vat_total": 0.0,
            "included_vat_total": 0.0,
        }
        processed_invoices = set()
        symbol = self.env.user.currency_id.symbol
        report_obj = self.env["ir.actions.report"]
        report = report_obj._get_report_from_name(
            "ff_sales_report.custom_sales_report_template"
        )
        (
            move_line,
            account_payment_obj,
            title,
            year,
            month,
            start_date,
            end_date,
            domain,
        ) = self.get_records()

        if not move_line:
            raise UserError(_("No Records Found.....!!!!"))
        cash_journal_ids = self.env["account.journal"].search([("type", "=", "cash")])
        for cash_journal_id in cash_journal_ids:
            payment_method_totals_dct[cash_journal_id.id] = {
                "journal_name": "Cash",
                "journal_total": 0.00,
            }
        for account_payment in account_payment_obj:
            journal_id = account_payment.journal_id
            journal_name = account_payment.journal_id.name
            amount = account_payment.amount
            if journal_id and journal_id.id not in payment_method_totals_dct:
                if not journal_id.name == "Bank":
                    payment_method_totals_dct[journal_id.id] = {
                        "journal_name": journal_name,
                        "journal_total": amount,
                    }
            else:
                payment_method_totals_dct[journal_id.id]["journal_total"] += amount

        for line in move_line:
            invoice_id = line.id
            if invoice_id not in processed_invoices:
                processed_invoices.add(invoice_id)
                grand_totals["excl_vat_total"] += line.amount_untaxed_signed
                grand_totals["vat_total"] += line.amount_tax_signed
                grand_totals["included_vat_total"] += line.amount_total_signed

        payment_method_totals = list(payment_method_totals_dct.values())
        vat_data = self._get_vat_data(domain)
        grand_total_excl_vat = grand_totals["excl_vat_total"]
        grand_total_vat = grand_totals["vat_total"]
        grand_total_incl_vat = grand_totals["included_vat_total"]

        return {
            "doc_ids": self.ids,
            "doc_model": report.model,
            "docs": self,
            "start_date": start_date,
            "end_date": end_date,
            "title": title,
            "month": month,
            "year": year,
            "symbol": symbol,
            "payment_method_totals": payment_method_totals,
            "vat_data": vat_data,
            "grand_total_excl_vat": grand_total_excl_vat,
            "grand_total_vat": grand_total_vat,
            "grand_total_incl_vat": grand_total_incl_vat,
        }

    def generate_report(self):
        self.ensure_one()
        data = self._prepare_report_data()
        action = self.env.ref("ff_sales_report.custom_sales_report_id").report_action(
            self, data=data
        )
        return action

    def get_records(self):
        domain = []
        account_payment_domain = []
        start_date = ""
        end_date = ""
        title = "Sales Report Of Golden Food Oy"
        month = ""
        year = ""
        if self.custom == "custom":
            title = "<h3><b>" + title + "</b></h3>"
            if self.start_date:
                start_date = self.start_date
                domain += [("invoice_date", ">=", self.start_date.strftime("%Y-%m-%d"))]
                account_payment_domain += [
                    ("date", ">=", self.start_date.strftime("%Y-%m-%d"))
                ]
            if self.end_date:
                end_date = self.end_date
                domain += [("invoice_date", "<=", self.end_date.strftime("%Y-%m-%d"))]
                account_payment_domain += [
                    ("date", "<=", self.end_date.strftime("%Y-%m-%d"))
                ]
        if self.custom == "monthly":
            if self.monthly:
                current_year = datetime.now().strftime("%Y")
                month_name = dict(self._fields["monthly"].selection).get(self.monthly)
                month = month_name + "-" + current_year
                dict(self._fields["monthly"].selection).get(self.monthly)
                title = "<h3><b> Monthly " + title + "</b></h3>"
                from_date = datetime.now().strftime("%Y-") + self.monthly + "-01"
                month_end = calendar.monthrange(
                    int(datetime.now().strftime("%Y")), int(self.monthly)
                )[1]
                to_date = (
                    datetime.now().strftime("%Y-") + self.monthly + "-" + str(month_end)
                )
                domain += [
                    ("invoice_date", ">=", from_date),
                    ("invoice_date", "<=", to_date),
                ]
                account_payment_domain += [
                    ("date", ">=", from_date),
                    ("date", "<=", to_date),
                ]
        if self.custom == "yearly":
            if self.yearly:
                year = self.yearly
                title = "<h3><b> Yearly " + title + "</b></h3>"
                year_start = self.yearly + "-01" + "-01"
                year_end = self.yearly + "-12" + "-31"
                domain += [
                    ("invoice_date", ">=", year_start),
                    ("invoice_date", "<=", year_end),
                ]
                account_payment_domain += [
                    ("date", ">=", year_start),
                    ("date", "<=", year_end),
                ]
        domain += [("move_type", "=", "out_invoice")]
        move_line = self.env["account.move"].search(domain)
        account_payment_obj = self.env["account.payment"].search(account_payment_domain)
        return (
            move_line,
            account_payment_obj,
            title,
            year,
            month,
            start_date,
            end_date,
            domain,
        )

    def _get_vat_data(self, domain):
        taxed_move_lines = self.env["account.move"].search(domain)
        move_line_ids = taxed_move_lines.mapped("line_ids")
        vat_data_dict = {}
        for line in move_line_ids:
            if line.tax_ids:
                for tax in line.tax_ids:
                    tax_price = line.price_subtotal * (tax.amount / 100)
                    if tax.id in vat_data_dict:
                        vat_data_dict[tax.id]["net"] += line.price_subtotal
                        vat_data_dict[tax.id]["tax"] += tax_price
                    else:
                        vat_data_dict[tax.id] = {
                            "tax_name": tax.name,
                            "net": line.price_subtotal,
                            "tax": tax_price,
                            "tax_line_id": tax.id,
                        }
        vat_data = list(vat_data_dict.values())
        return vat_data
