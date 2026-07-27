# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ContractGuarantee(models.Model):
    _name = 'contract.guarantee'
    _description = 'Bank Guarantee / Bond'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'expiry_date asc'
    _rec_name = 'name'

    name = fields.Char(
        'Guarantee Reference — رقم الضمان', required=True, copy=False
    )
    contract_id = fields.Many2one(
        'contract.contract', 'Contract — العقد',
        required=True, ondelete='cascade', tracking=True
    )
    tender_id = fields.Many2one(
        'contract.tender', 'Tender — المناقصة',
        related='contract_id.tender_id', readonly=True
    )

    guarantee_type = fields.Selection([
        ('bid_bond',    'Bid Bond — ضمان ابتدائي'),
        ('performance', 'Performance Bond — ضمان حسن التنفيذ'),
        ('advance',     'Advance Payment Guarantee — ضمان الدفعة المقدمة'),
        ('retention',   'Retention / Maintenance Bond — ضمان الصيانة'),
        ('other',       'Other — أخرى'),
    ], string='Guarantee Type — نوع الضمان', required=True,
        default='performance', tracking=True)

    partner_id = fields.Many2one(
        'res.partner', 'Contractor — المقاول',
        related='contract_id.partner_id', readonly=True
    )
    bank_name = fields.Char('Issuing Bank — البنك المصدر', required=True)
    bank_reference = fields.Char('Bank Reference — مرجع البنك')
    beneficiary = fields.Char(
        'Beneficiary — المستفيد',
        default='Saudi Electricity Company — شركة الكهرباء السعودية'
    )

    # ── Financial ─────────────────────────────────────────────────────────────
    currency_id = fields.Many2one(
        'res.currency', related='contract_id.currency_id', store=True
    )
    amount = fields.Monetary(
        'Guarantee Amount — قيمة الضمان',
        currency_field='currency_id', required=True, tracking=True
    )

    # ── Dates ─────────────────────────────────────────────────────────────────
    issue_date = fields.Date('Issue Date — تاريخ الإصدار', required=True)
    expiry_date = fields.Date('Expiry Date — تاريخ الانتهاء', required=True, tracking=True)
    days_to_expiry = fields.Integer(
        'Days to Expiry — الأيام المتبقية',
        compute='_compute_days_to_expiry'
    )
    alert_level = fields.Selection([
        ('ok',      'OK — بخير'),
        ('warning', 'Expiring Soon — ينتهي قريباً'),
        ('critical', 'Critical — حرج'),
        ('expired', 'Expired — منتهٍ'),
    ], compute='_compute_days_to_expiry', string='Alert')

    # ── Extension ─────────────────────────────────────────────────────────────
    extended_expiry_date = fields.Date('Extended Expiry Date — تاريخ التجديد')

    # ── Release / Claim ───────────────────────────────────────────────────────
    release_date = fields.Date('Release Date — تاريخ الإفراج')
    claim_date = fields.Date('Claim Date — تاريخ المطالبة')
    claim_amount = fields.Monetary(
        'Claimed Amount — المبلغ المطالب به', currency_field='currency_id'
    )
    claim_reason = fields.Text('Claim Reason — سبب المطالبة')

    notes = fields.Text('Notes — ملاحظات')

    state = fields.Selection([
        ('active',   'Active — سارٍ'),
        ('extended', 'Extended — مجدَّد'),
        ('expired',  'Expired — منتهٍ'),
        ('released', 'Released — مُفرج عنه'),
        ('claimed',  'Claimed — مطالَب به'),
    ], default='active', tracking=True, string='Status')

    # ── Compute ───────────────────────────────────────────────────────────────
    @api.depends('expiry_date')
    def _compute_days_to_expiry(self):
        today = fields.Date.today()
        for rec in self:
            if rec.expiry_date:
                delta = (rec.expiry_date - today).days
                rec.days_to_expiry = delta
                if delta < 0:
                    rec.alert_level = 'expired'
                elif delta <= 14:
                    rec.alert_level = 'critical'
                elif delta <= 30:
                    rec.alert_level = 'warning'
                else:
                    rec.alert_level = 'ok'
            else:
                rec.days_to_expiry = 0
                rec.alert_level = 'ok'

    # ── Actions ───────────────────────────────────────────────────────────────
    def action_extend(self):
        self.write({'state': 'extended'})

    def action_release(self):
        self.write({'state': 'released', 'release_date': fields.Date.today()})

    def action_claim(self):
        self.write({'state': 'claimed', 'claim_date': fields.Date.today()})

    def action_expire(self):
        self.write({'state': 'expired'})
