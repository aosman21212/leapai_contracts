# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import models, fields, api, _


class ContractAmendment(models.Model):
    _name = 'contract.amendment'
    _description = 'Contract Amendment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_submitted desc'
    _rec_name = 'reference'

    reference = fields.Char(
        'Amendment No. — رقم التعديل', readonly=True, default='New', copy=False
    )
    name = fields.Char('Title — العنوان', required=True)
    contract_id = fields.Many2one(
        'contract.contract', 'Contract — العقد',
        required=True, ondelete='cascade', tracking=True
    )

    amendment_type = fields.Selection([
        ('value',    'Value Change — تغيير في القيمة'),
        ('time',     'Time Extension — تمديد الفترة'),
        ('scope',    'Scope Change — تغيير في النطاق'),
        ('combined', 'Value + Time — قيمة وفترة'),
        ('other',    'Other — أخرى'),
    ], string='Amendment Type — نوع التعديل', required=True,
        default='time', tracking=True)

    reason = fields.Text('Reason / Justification — المبرر', required=True)
    description = fields.Text('Description of Changes — وصف التعديلات')

    # ── Value ─────────────────────────────────────────────────────────────────
    currency_id = fields.Many2one(
        'res.currency', related='contract_id.currency_id', store=True
    )
    original_value = fields.Monetary(
        'Original Value — القيمة الأصلية',
        currency_field='currency_id',
        related='contract_id.contract_value', readonly=True
    )
    value_change = fields.Monetary(
        'Value Change — التغيير في القيمة', currency_field='currency_id'
    )
    new_contract_value = fields.Monetary(
        'New Contract Value — القيمة الجديدة',
        currency_field='currency_id',
        compute='_compute_new_value', store=True
    )

    # ── Time ──────────────────────────────────────────────────────────────────
    original_end_date = fields.Date(
        'Original End Date — تاريخ الانتهاء الأصلي',
        related='contract_id.end_date', readonly=True
    )
    time_extension_days = fields.Integer('Extension (Days) — الأيام الإضافية')
    new_end_date = fields.Date(
        'New End Date — تاريخ الانتهاء الجديد',
        compute='_compute_new_end_date', store=True
    )

    # ── Approval ──────────────────────────────────────────────────────────────
    date_submitted = fields.Date(
        'Submitted Date — تاريخ التقديم', default=fields.Date.today
    )
    date_approved = fields.Date('Approved Date — تاريخ الاعتماد')
    approved_by = fields.Many2one('res.users', 'Approved By — المعتمد')

    notes = fields.Text('Notes — ملاحظات')

    state = fields.Selection([
        ('draft',     'Draft — مسودة'),
        ('submitted', 'Submitted — مقدّم'),
        ('approved',  'Approved — معتمد'),
        ('rejected',  'Rejected — مرفوض'),
    ], default='draft', tracking=True, string='Status')

    # ── Compute ───────────────────────────────────────────────────────────────
    @api.depends('contract_id.contract_value', 'value_change')
    def _compute_new_value(self):
        for rec in self:
            rec.new_contract_value = rec.original_value + rec.value_change

    @api.depends('contract_id.end_date', 'time_extension_days')
    def _compute_new_end_date(self):
        for rec in self:
            if rec.contract_id.end_date and rec.time_extension_days:
                rec.new_end_date = rec.contract_id.end_date + timedelta(
                    days=rec.time_extension_days
                )
            else:
                rec.new_end_date = False

    # ── ORM ───────────────────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'New') == 'New':
                vals['reference'] = (
                    self.env['ir.sequence'].next_by_code('contract.amendment') or 'New'
                )
        return super().create(vals_list)

    # ── Actions ───────────────────────────────────────────────────────────────
    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        today = fields.Date.today()
        self.write({
            'state': 'approved',
            'approved_by': self.env.user.id,
            'date_approved': today,
        })
        for rec in self:
            update_vals = {}
            if rec.amendment_type in ('value', 'combined') and rec.value_change:
                update_vals['contract_value'] = rec.new_contract_value
            if rec.amendment_type in ('time', 'combined') and rec.time_extension_days:
                update_vals['end_date'] = rec.new_end_date
            if update_vals:
                rec.contract_id.write(update_vals)

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})
