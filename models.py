from odoo import tools, models, fields, api, _
from datetime import datetime

class SaleStageStat(models.Model):
    _name = "sale.stage.stat"
    _description = "sale.stage.stat"

    order_id = fields.Many2one('sale.order',string='Order')
    state_from = fields.Char(string='Estado desde')
    state_to = fields.Char(string='Estado hasta')
    date = fields.Datetime('Fecha')
    diff_days = fields.Integer('Dias')

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        for rec in res:
            vals = {
                'order_id': rec.id,
                'state_from': '',
                'state_to': 'draft',
                'date': str(datetime.now())[:19],
                'diff_days': 0,
               }
            stat_id = self.env['sale.stage.stat'].create(vals)
        return res

    def write(self, vals):
        state_from = state_to = ''
        if 'state' in vals:
            for rec in self:
                state_from = rec.state
                state_to = vals.get('state')
        res = super(SaleOrder, self).write(vals)
        if state_from and state_to:
            for rec in self:
                prev_stage = self.env['sale.stage.stat'].search([('order_id','=',rec.id)],order='id desc',limit=1)
                if prev_stage:
                    diff_days = (datetime.now() - prev_stage.date).days
                else:
                    diff_days = (datetime.now() - rec.create_date).days
                vals = {
                        'order_id': rec.id,
                        'state_from': state_from,
                        'state_to': state_to,
                        'date': str(datetime.now())[:19],
                        'diff_days': diff_days,
                        }
                stat_id = self.env['sale.stage.stat'].create(vals)
        return res

    stage_stat_ids = fields.One2many(comodel_name='sale.stage.stat',inverse_name='order_id',string='Stage stats')
