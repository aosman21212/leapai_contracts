# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ContractTender(models.Model):
    _name = 'contract.tender'
    _description = 'Contract Tender'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_created desc'
    _rec_name = 'name'

    # ── Identity ──────────────────────────────────────────────────────────────
    name = fields.Char('Tender Name', required=True, tracking=True)
    reference = fields.Char(
        'Tender No.', readonly=True, default='New', copy=False, tracking=True
    )
    tender_type = fields.Selection([
        ('open',      'Open Tender — مناقصة عامة'),
        ('limited',   'Limited Tender — مناقصة محدودة'),
        ('direct',    'Direct Purchase — شراء مباشر'),
        ('framework', 'Framework Agreement — اتفاقية إطارية'),
    ], string='Tender Type', required=True, default='open', tracking=True)

    description = fields.Text('Description — الوصف')
    scope_of_work = fields.Text('Scope of Work — نطاق العمل')

    # ── Financial ─────────────────────────────────────────────────────────────
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id
    )
    estimated_value = fields.Monetary(
        'Estimated Value — القيمة التقديرية', currency_field='currency_id'
    )

    # ── Dates ─────────────────────────────────────────────────────────────────
    date_created = fields.Date('Created Date', default=fields.Date.today)
    publish_date = fields.Date('Publication Date — تاريخ الإعلان')
    closing_date = fields.Datetime('Closing Date — موعد الإغلاق', tracking=True)
    award_date = fields.Date('Award Date — تاريخ الترسية')

    # ── Organisation ──────────────────────────────────────────────────────────
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    responsible_id = fields.Many2one(
        'res.users', 'Responsible — المسؤول', default=lambda self: self.env.user
    )
    department = fields.Char('Department / Region — الإدارة')
    region = fields.Selection([
        ('riyadh',   'Riyadh Region — منطقة الرياض'),
        ('western',  'Western Region — المنطقة الغربية'),
        ('eastern',  'Eastern Region — المنطقة الشرقية'),
        ('southern', 'Southern Region — المنطقة الجنوبية'),
        ('northern', 'Northern Region — المنطقة الشمالية'),
        ('central',  'Central Region — المنطقة الوسطى'),
    ], string='Region — المنطقة')
    site_location = fields.Char('Site Location — الموقع')

    # ── Terms ─────────────────────────────────────────────────────────────────
    min_experience_years = fields.Integer('Min. Experience (Years) — سنوات الخبرة')
    nitaqat_required = fields.Boolean('Nitaqat Required — نطاقات', default=True)
    vat_included = fields.Boolean('Prices Inclusive of VAT — شامل الضريبة', default=False)
    bid_bond_percentage = fields.Float('Bid Bond % — الضمان الابتدائي %', default=2.0)
    performance_bond_percentage = fields.Float('Performance Bond % — ضمان التنفيذ %', default=10.0)
    advance_percentage = fields.Float('Advance Payment % — الدفعة المقدمة %', default=10.0)
    retention_percentage = fields.Float('Retention % — نسبة الاستقطاع', default=10.0)

    # ── Related ───────────────────────────────────────────────────────────────
    bid_ids = fields.One2many('contract.bid', 'tender_id', 'Bids — العطاءات')
    bid_count = fields.Integer('Bid Count', compute='_compute_bid_count', store=True)
    contract_id = fields.Many2one('contract.contract', 'Awarded Contract', readonly=True)

    notes = fields.Text('Notes — ملاحظات')

    state = fields.Selection([
        ('draft',      'Draft — مسودة'),
        ('published',  'Published — منشورة'),
        ('closed',     'Bid Closed — مغلقة'),
        ('evaluation', 'Under Evaluation — قيد التقييم'),
        ('awarded',    'Awarded — مرسّاة'),
        ('cancelled',  'Cancelled — ملغاة'),
    ], default='draft', tracking=True, string='Status')

    # ── Compute ───────────────────────────────────────────────────────────────
    @api.depends('bid_ids')
    def _compute_bid_count(self):
        for rec in self:
            rec.bid_count = len(rec.bid_ids)

    # ── ORM ───────────────────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'New') == 'New':
                vals['reference'] = (
                    self.env['ir.sequence'].next_by_code('contract.tender') or 'New'
                )
        return super().create(vals_list)

    # ── Actions ───────────────────────────────────────────────────────────────
    def action_publish(self):
        self.write({'state': 'published'})

    def action_close(self):
        self.write({'state': 'closed'})

    def action_evaluate(self):
        self.write({'state': 'evaluation'})

    def action_award(self):
        self.write({'state': 'awarded'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    def action_view_bids(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Bids — العطاءات'),
            'res_model': 'contract.bid',
            'view_mode': 'list,form',
            'domain': [('tender_id', '=', self.id)],
            'context': {'default_tender_id': self.id},
        }
