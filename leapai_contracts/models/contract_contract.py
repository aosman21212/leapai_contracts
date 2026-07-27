# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ContractContract(models.Model):
    _name = 'contract.contract'
    _description = 'Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_signed desc'
    _rec_name = 'name'

    # ── Identity ──────────────────────────────────────────────────────────────
    name = fields.Char('Contract Name — اسم العقد', required=True, tracking=True)
    reference = fields.Char(
        'Contract No. — رقم العقد', readonly=True, default='New',
        copy=False, tracking=True
    )
    tender_id = fields.Many2one('contract.tender', 'Source Tender — المناقصة')
    contract_type = fields.Selection([
        ('lump_sum',   'Lump Sum — مبلغ إجمالي'),
        ('unit_rate',  'Unit Rate — أسعار وحدة'),
        ('cost_plus',  'Cost Plus — التكلفة زائد'),
        ('turnkey',    'Turnkey — مفتاح في يد'),
        ('framework',  'Framework Agreement — اتفاقية إطارية'),
    ], string='Contract Type — نوع العقد', required=True,
        default='lump_sum', tracking=True)

    # ── Contractor ────────────────────────────────────────────────────────────
    partner_id = fields.Many2one(
        'res.partner', 'Contractor — المقاول', required=True, tracking=True
    )
    partner_cr = fields.Char('CR No. — السجل التجاري')
    partner_vat = fields.Char('VAT No. — الرقم الضريبي')
    partner_iban = fields.Char('IBAN — رقم الحساب')
    partner_bank = fields.Char('Bank — البنك')

    # ── Dates ─────────────────────────────────────────────────────────────────
    date_signed = fields.Date('Signing Date — تاريخ التوقيع', tracking=True)
    start_date = fields.Date('Start Date — تاريخ البدء', tracking=True)
    end_date = fields.Date('End Date — تاريخ الانتهاء', tracking=True)
    original_end_date = fields.Date('Original End Date — التاريخ الأصلي للانتهاء')

    # ── Financial ─────────────────────────────────────────────────────────────
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id
    )
    contract_value = fields.Monetary(
        'Contract Value — قيمة العقد', currency_field='currency_id', tracking=True
    )
    vat_amount = fields.Monetary(
        'VAT (15%) — ضريبة القيمة المضافة',
        currency_field='currency_id',
        compute='_compute_vat', store=True
    )
    total_with_vat = fields.Monetary(
        'Total incl. VAT — الإجمالي شامل الضريبة',
        currency_field='currency_id',
        compute='_compute_vat', store=True
    )

    advance_percentage = fields.Float('Advance % — نسبة الدفعة المقدمة', default=10.0)
    advance_amount = fields.Monetary(
        'Advance Amount — الدفعة المقدمة',
        currency_field='currency_id',
        compute='_compute_advance', store=True
    )
    retention_percentage = fields.Float('Retention % — نسبة الاستقطاع', default=10.0)

    # ── Computed Financial Summary ─────────────────────────────────────────────
    total_certified = fields.Monetary(
        'Total Certified — إجمالي المعتمد',
        currency_field='currency_id',
        compute='_compute_financial_summary', store=True
    )
    total_paid = fields.Monetary(
        'Total Paid — إجمالي المصروف',
        currency_field='currency_id',
        compute='_compute_financial_summary', store=True
    )
    balance_remaining = fields.Monetary(
        'Balance Remaining — الرصيد المتبقي',
        currency_field='currency_id',
        compute='_compute_financial_summary', store=True
    )
    completion_percentage = fields.Float(
        'Completion % — نسبة الإنجاز',
        compute='_compute_financial_summary', store=True
    )

    # ── People ────────────────────────────────────────────────────────────────
    project_manager_id = fields.Many2one('res.users', 'Project Manager — مدير المشروع', tracking=True)
    contract_officer_id = fields.Many2one('res.users', 'Contract Officer — مسؤول العقد')

    # ── Location ──────────────────────────────────────────────────────────────
    site_location = fields.Char('Site Location — موقع المشروع')
    region = fields.Selection([
        ('riyadh',   'Riyadh Region — منطقة الرياض'),
        ('western',  'Western Region — المنطقة الغربية'),
        ('eastern',  'Eastern Region — المنطقة الشرقية'),
        ('southern', 'Southern Region — المنطقة الجنوبية'),
        ('northern', 'Northern Region — المنطقة الشمالية'),
        ('central',  'Central Region — المنطقة الوسطى'),
    ], string='Region — المنطقة')

    # ── Sub-records ───────────────────────────────────────────────────────────
    payment_certificate_ids = fields.One2many(
        'contract.payment.certificate', 'contract_id', 'Payment Certificates — شهادات الدفع'
    )
    guarantee_ids = fields.One2many(
        'contract.guarantee', 'contract_id', 'Bank Guarantees — الضمانات البنكية'
    )
    amendment_ids = fields.One2many(
        'contract.amendment', 'contract_id', 'Amendments — التعديلات'
    )

    payment_certificate_count = fields.Integer(compute='_compute_counts')
    guarantee_count = fields.Integer(compute='_compute_counts')
    amendment_count = fields.Integer(compute='_compute_counts')

    # ── Misc ──────────────────────────────────────────────────────────────────
    description = fields.Text('Scope / Description — نطاق العمل')
    notes = fields.Text('Internal Notes — ملاحظات داخلية')

    state = fields.Selection([
        ('draft',      'Draft — مسودة'),
        ('active',     'Active — سارٍ'),
        ('suspended',  'Suspended — موقوف'),
        ('completed',  'Completed — منتهٍ'),
        ('terminated', 'Terminated — مُنهى'),
    ], default='draft', tracking=True, string='Status')

    # ── Compute ───────────────────────────────────────────────────────────────
    @api.depends('contract_value')
    def _compute_vat(self):
        for rec in self:
            rec.vat_amount = rec.contract_value * 0.15
            rec.total_with_vat = rec.contract_value * 1.15

    @api.depends('contract_value', 'advance_percentage')
    def _compute_advance(self):
        for rec in self:
            rec.advance_amount = rec.contract_value * rec.advance_percentage / 100

    @api.depends(
        'payment_certificate_ids.net_payable',
        'payment_certificate_ids.state',
        'contract_value'
    )
    def _compute_financial_summary(self):
        for rec in self:
            approved = rec.payment_certificate_ids.filtered(
                lambda c: c.state in ('approved', 'paid')
            )
            paid = rec.payment_certificate_ids.filtered(lambda c: c.state == 'paid')
            rec.total_certified = sum(approved.mapped('net_payable'))
            rec.total_paid = sum(paid.mapped('net_payable'))
            rec.balance_remaining = rec.contract_value - rec.total_certified
            rec.completion_percentage = (
                rec.total_certified / rec.contract_value * 100
                if rec.contract_value else 0.0
            )

    @api.depends('payment_certificate_ids', 'guarantee_ids', 'amendment_ids')
    def _compute_counts(self):
        for rec in self:
            rec.payment_certificate_count = len(rec.payment_certificate_ids)
            rec.guarantee_count = len(rec.guarantee_ids)
            rec.amendment_count = len(rec.amendment_ids)

    # ── ORM ───────────────────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'New') == 'New':
                vals['reference'] = (
                    self.env['ir.sequence'].next_by_code('contract.contract') or 'New'
                )
            if not vals.get('original_end_date') and vals.get('end_date'):
                vals['original_end_date'] = vals['end_date']
        return super().create(vals_list)

    # ── State Actions ─────────────────────────────────────────────────────────
    def action_activate(self):
        self.write({'state': 'active'})

    def action_suspend(self):
        self.write({'state': 'suspended'})

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_terminate(self):
        self.write({'state': 'terminated'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    # ── Smart Button Actions ───────────────────────────────────────────────────
    def action_view_certificates(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Payment Certificates'),
            'res_model': 'contract.payment.certificate',
            'view_mode': 'list,form',
            'domain': [('contract_id', '=', self.id)],
            'context': {'default_contract_id': self.id},
        }

    def action_view_guarantees(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Bank Guarantees'),
            'res_model': 'contract.guarantee',
            'view_mode': 'list,form',
            'domain': [('contract_id', '=', self.id)],
            'context': {'default_contract_id': self.id},
        }

    def action_view_amendments(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Amendments'),
            'res_model': 'contract.amendment',
            'view_mode': 'list,form',
            'domain': [('contract_id', '=', self.id)],
            'context': {'default_contract_id': self.id},
        }
