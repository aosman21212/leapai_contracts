# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ContractPaymentCertificate(models.Model):
    _name = 'contract.payment.certificate'
    _description = 'Payment Certificate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'period_to desc'
    _rec_name = 'name'

    name = fields.Char(
        'Certificate No. — رقم الشهادة', readonly=True, default='New', copy=False
    )
    contract_id = fields.Many2one(
        'contract.contract', 'Contract — العقد',
        required=True, ondelete='cascade', tracking=True
    )
    certificate_type = fields.Selection([
        ('interim', 'Interim Payment Certificate (IPC) — شهادة دفع مرحلي'),
        ('final',   'Final Payment Certificate (FPC) — شهادة دفع نهائي'),
    ], required=True, default='interim', tracking=True,
        string='Certificate Type — نوع الشهادة')

    # ── Period ────────────────────────────────────────────────────────────────
    period_from = fields.Date('Period From — من تاريخ', required=True)
    period_to = fields.Date('Period To — إلى تاريخ', required=True)

    # ── Contract context (readonly) ───────────────────────────────────────────
    currency_id = fields.Many2one(
        'res.currency', related='contract_id.currency_id', store=True
    )
    contract_value = fields.Monetary(
        'Contract Value — قيمة العقد',
        currency_field='currency_id',
        related='contract_id.contract_value', readonly=True
    )
    retention_percentage = fields.Float(
        'Retention % — نسبة الاستقطاع',
        related='contract_id.retention_percentage', readonly=True
    )

    # ── Work Done ─────────────────────────────────────────────────────────────
    total_work_done_to_date = fields.Monetary(
        'Total Work Done to Date — إجمالي الأعمال المنجزة حتى الآن',
        currency_field='currency_id', tracking=True
    )
    previous_certified_amount = fields.Monetary(
        'Previously Certified — المبلغ المعتمد سابقاً',
        currency_field='currency_id', tracking=True
    )
    this_period_gross = fields.Monetary(
        'This Period Gross — مبلغ الفترة الإجمالي',
        currency_field='currency_id',
        compute='_compute_this_period', store=True
    )

    # ── Deductions ────────────────────────────────────────────────────────────
    retention_deduction = fields.Monetary(
        'Retention Deduction — الاستقطاع',
        currency_field='currency_id',
        compute='_compute_deductions', store=True
    )
    advance_recovery = fields.Monetary(
        'Advance Recovery — استرداد الدفعة المقدمة',
        currency_field='currency_id', tracking=True
    )
    other_deductions = fields.Monetary(
        'Other Deductions — خصومات أخرى', currency_field='currency_id'
    )
    other_deductions_note = fields.Char('Deductions Note — ملاحظة الخصومات')
    total_deductions = fields.Monetary(
        'Total Deductions — إجمالي الخصومات',
        currency_field='currency_id',
        compute='_compute_deductions', store=True
    )

    # ── Net ───────────────────────────────────────────────────────────────────
    net_before_vat = fields.Monetary(
        'Net Before VAT — الصافي قبل الضريبة',
        currency_field='currency_id',
        compute='_compute_net', store=True
    )
    vat_amount = fields.Monetary(
        'VAT (15%) — ضريبة القيمة المضافة',
        currency_field='currency_id',
        compute='_compute_net', store=True
    )
    net_payable = fields.Monetary(
        'Net Payable incl. VAT — المبلغ المستحق شامل الضريبة',
        currency_field='currency_id',
        compute='_compute_net', store=True, tracking=True
    )

    # ── BOQ Lines ─────────────────────────────────────────────────────────────
    line_ids = fields.One2many(
        'contract.payment.certificate.line', 'certificate_id',
        'BOQ Lines — بنود جدول الكميات'
    )

    # ── Approval ──────────────────────────────────────────────────────────────
    prepared_by = fields.Many2one(
        'res.users', 'Prepared By — أعده',
        default=lambda self: self.env.user
    )
    checked_by = fields.Many2one('res.users', 'Checked By — راجعه')
    approved_by = fields.Many2one('res.users', 'Approved By — اعتمده')
    date_submitted = fields.Date('Submitted Date — تاريخ التقديم')
    date_approved = fields.Date('Approved Date — تاريخ الاعتماد')
    date_paid = fields.Date('Payment Date — تاريخ الدفع')

    notes = fields.Text('Notes / Remarks — ملاحظات')

    state = fields.Selection([
        ('draft',     'Draft — مسودة'),
        ('submitted', 'Submitted — مقدّم'),
        ('approved',  'Approved — معتمد'),
        ('paid',      'Paid — مدفوع'),
        ('rejected',  'Rejected — مرفوض'),
    ], default='draft', tracking=True, string='Status')

    # ── Compute ───────────────────────────────────────────────────────────────
    @api.depends('total_work_done_to_date', 'previous_certified_amount')
    def _compute_this_period(self):
        for rec in self:
            rec.this_period_gross = (
                rec.total_work_done_to_date - rec.previous_certified_amount
            )

    @api.depends(
        'this_period_gross', 'retention_percentage',
        'advance_recovery', 'other_deductions'
    )
    def _compute_deductions(self):
        for rec in self:
            rec.retention_deduction = (
                rec.this_period_gross * rec.retention_percentage / 100
            )
            rec.total_deductions = (
                rec.retention_deduction
                + rec.advance_recovery
                + rec.other_deductions
            )

    @api.depends('this_period_gross', 'total_deductions')
    def _compute_net(self):
        for rec in self:
            rec.net_before_vat = rec.this_period_gross - rec.total_deductions
            rec.vat_amount = rec.net_before_vat * 0.15
            rec.net_payable = rec.net_before_vat + rec.vat_amount

    # ── ORM ───────────────────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code(
                        'contract.payment.certificate'
                    ) or 'New'
                )
        return super().create(vals_list)

    # ── Actions ───────────────────────────────────────────────────────────────
    def action_submit(self):
        self.write({'state': 'submitted', 'date_submitted': fields.Date.today()})

    def action_approve(self):
        self.write({
            'state': 'approved',
            'approved_by': self.env.user.id,
            'date_approved': fields.Date.today(),
        })

    def action_mark_paid(self):
        self.write({'state': 'paid', 'date_paid': fields.Date.today()})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})


class ContractPaymentCertificateLine(models.Model):
    _name = 'contract.payment.certificate.line'
    _description = 'Payment Certificate Line (BOQ)'
    _order = 'sequence, id'

    certificate_id = fields.Many2one(
        'contract.payment.certificate', required=True, ondelete='cascade'
    )
    sequence = fields.Integer(default=10)
    item_no = fields.Char('Item No. — رقم البند')
    description = fields.Char('Description — الوصف', required=True)
    uom = fields.Char('Unit — الوحدة', default='LS')

    # BOQ Budget
    boq_quantity = fields.Float('BOQ Qty — الكمية', digits=(12, 3))
    unit_rate = fields.Monetary('Unit Rate — سعر الوحدة', currency_field='currency_id')
    boq_amount = fields.Monetary(
        'BOQ Amount — المبلغ', currency_field='currency_id',
        compute='_compute_boq_amount', store=True
    )

    # Progress
    previous_quantity = fields.Float('Previous Qty — الكمية السابقة', digits=(12, 3))
    this_period_quantity = fields.Float(
        'This Period Qty — كمية الفترة', digits=(12, 3)
    )
    cumulative_quantity = fields.Float(
        'Cumulative Qty — الكمية التراكمية', digits=(12, 3),
        compute='_compute_cumulative', store=True
    )
    previous_amount = fields.Monetary(
        'Previous Amount — المبلغ السابق', currency_field='currency_id',
        compute='_compute_amounts', store=True
    )
    this_period_amount = fields.Monetary(
        'This Period Amount — مبلغ الفترة', currency_field='currency_id',
        compute='_compute_amounts', store=True
    )

    currency_id = fields.Many2one(
        'res.currency', related='certificate_id.currency_id'
    )

    # ── Compute ───────────────────────────────────────────────────────────────
    @api.depends('boq_quantity', 'unit_rate')
    def _compute_boq_amount(self):
        for line in self:
            line.boq_amount = line.boq_quantity * line.unit_rate

    @api.depends('previous_quantity', 'this_period_quantity')
    def _compute_cumulative(self):
        for line in self:
            line.cumulative_quantity = line.previous_quantity + line.this_period_quantity

    @api.depends('previous_quantity', 'this_period_quantity', 'unit_rate')
    def _compute_amounts(self):
        for line in self:
            line.previous_amount = line.previous_quantity * line.unit_rate
            line.this_period_amount = line.this_period_quantity * line.unit_rate
