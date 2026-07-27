# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ContractBid(models.Model):
    _name = 'contract.bid'
    _description = 'Bid / Offer'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'total_score desc, submission_date desc'
    _rec_name = 'name'

    name = fields.Char('Bid No.', readonly=True, default='New', copy=False)
    tender_id = fields.Many2one(
        'contract.tender', 'Tender — المناقصة', required=True,
        ondelete='cascade', tracking=True
    )
    partner_id = fields.Many2one(
        'res.partner', 'Bidder — المتقدم', required=True, tracking=True
    )

    # Saudi-specific partner details
    cr_number = fields.Char('CR No. — السجل التجاري')
    vat_number = fields.Char('VAT No. — الرقم الضريبي')
    nitaqat_color = fields.Selection([
        ('platinum', 'Platinum — بلاتيني'),
        ('high_green', 'High Green — أخضر مرتفع'),
        ('medium_green', 'Medium Green — أخضر متوسط'),
        ('low_green', 'Low Green — أخضر منخفض'),
        ('yellow', 'Yellow — أصفر'),
        ('red', 'Red — أحمر'),
    ], string='Nitaqat Color — نطاقات')

    # Financial
    currency_id = fields.Many2one(
        'res.currency', related='tender_id.currency_id', store=True
    )
    bid_value = fields.Monetary(
        'Bid Value — قيمة العطاء', currency_field='currency_id', tracking=True
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

    submission_date = fields.Datetime(
        'Submission Date — تاريخ التقديم', default=fields.Datetime.now
    )

    # ── Evaluation ────────────────────────────────────────────────────────────
    technical_weight = fields.Float('Technical Weight % — وزن الفني', default=70.0)
    financial_weight = fields.Float('Financial Weight % — وزن المالي', default=30.0)
    technical_score = fields.Float('Technical Score (0–100) — الدرجة الفنية')
    financial_score = fields.Float('Financial Score (0–100) — الدرجة المالية')
    total_score = fields.Float(
        'Total Score — المجموع', compute='_compute_total_score', store=True
    )

    # ── Bid Bond ──────────────────────────────────────────────────────────────
    bid_bond_submitted = fields.Boolean('Bid Bond Submitted — الضمان الابتدائي مقدم')
    bid_bond_reference = fields.Char('Bond Reference — رقم الضمان')
    bid_bond_amount = fields.Monetary(
        'Bond Amount — قيمة الضمان', currency_field='currency_id'
    )
    bid_bond_expiry = fields.Date('Bond Expiry — انتهاء الضمان')

    # ── Result ────────────────────────────────────────────────────────────────
    is_winner = fields.Boolean('Winner — الفائز', tracking=True)
    disqualification_reason = fields.Text('Disqualification Reason — سبب الاستبعاد')
    notes = fields.Text('Notes — ملاحظات')

    state = fields.Selection([
        ('submitted',    'Submitted — مقدّم'),
        ('under_review', 'Under Review — قيد المراجعة'),
        ('accepted',     'Accepted — مقبول'),
        ('rejected',     'Rejected — مرفوض'),
    ], default='submitted', tracking=True, string='Status')

    # ── Compute ───────────────────────────────────────────────────────────────
    @api.depends('bid_value')
    def _compute_vat(self):
        for rec in self:
            rec.vat_amount = rec.bid_value * 0.15
            rec.total_with_vat = rec.bid_value + rec.vat_amount

    @api.depends('technical_score', 'financial_score', 'technical_weight', 'financial_weight')
    def _compute_total_score(self):
        for rec in self:
            rec.total_score = (
                rec.technical_score * rec.technical_weight / 100
                + rec.financial_score * rec.financial_weight / 100
            )

    # ── ORM ───────────────────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('contract.bid') or 'New'
                )
        return super().create(vals_list)

    # ── Actions ───────────────────────────────────────────────────────────────
    def action_review(self):
        self.write({'state': 'under_review'})

    def action_accept(self):
        self.write({'state': 'accepted'})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_mark_winner(self):
        """Mark this bid as winner and set tender to awarded."""
        self.tender_id.bid_ids.filtered(lambda b: b.id != self.id).write({
            'is_winner': False
        })
        self.write({'is_winner': True, 'state': 'accepted'})
        self.tender_id.write({'state': 'awarded', 'award_date': fields.Date.today()})
