from odoo import tools, models, fields, api, _
from datetime import datetime

class SaleStageStat(models.Model):
    _name = "sale.stage.stat"
    _description = "sale.stage.stat"

    user_id = fields.Many2one('res.users',string='Usuario')
    partner_id = fields.Many2one('res.partner',string='Cliente')
    order_id = fields.Many2one('sale.order',string='Pedido')
    state_from = fields.Char(string='Estado desde')
    state_to = fields.Char(string='Estado hasta')
    date = fields.Datetime('Fecha')
    diff_days = fields.Integer('Dias')
    diff_hours = fields.Integer('Horas')
    diff_minutes = fields.Integer('Minutos')

class SaleOrder(models.Model):
    _inherit = 'sale.order'


    def mark_sent(self):
        self.ensure_one()
        if self.state != 'draft':
            raise ValidationError('No se puede marcar como enviado en este estado')
        self.state = 'sent'


    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        for rec in res:
            vals = {
                'order_id': rec.id,
                'user_id': rec.user_id.id,
                'partner_id': rec.partner_id.id,
                'state_from': '',
                'state_to': 'draft',
                'date': str(datetime.now())[:19],
                'diff_days': 0,
                'diff_hours': 0,
                'diff_minutes': 0,
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
                    diff_hours = ((datetime.now() - prev_stage.date).total_seconds() ) / 3600
                    diff_minutes = ((datetime.now() - prev_stage.date).total_seconds() ) / 60
                else:
                    diff_days = (datetime.now() - rec.create_date).days
                    diff_hours = ((datetime.now() - prev_stage.date).total_seconds() ) / 3600
                    diff_minutes = ((datetime.now() - prev_stage.date).total_seconds() ) / 60
                vals = {
                        'order_id': rec.id,
                        'user_id': rec.user_id.id,
                        'partner_id': rec.partner_id.id,
                        'state_from': state_from,
                        'state_to': state_to,
                        'date': str(datetime.now())[:19],
                        'diff_days': diff_days,
                        'diff_hours': diff_hours,
                        'diff_minutes': diff_minutes,
                        }
                stat_id = self.env['sale.stage.stat'].create(vals)
        return res

    stage_stat_ids = fields.One2many(comodel_name='sale.stage.stat',inverse_name='order_id',string='Stage stats')
    picking_state = fields.Char('Estado transferencias')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def update_sale_state(self):
        for rec in self:
            if rec.origin:
                sale_id = self.env['sale.order'].search([('name','=',rec.origin)])
                if sale_id:
                    sale_id.picking_state = rec.state


    def write(self, vals):
        res = super(StockPicking, self).write(vals)
        if 'date_done' in vals:
            self.update_sale_state()
        return res

    @api.model
    def create(self, vals):
        res = super(StockPicking, self).create(vals)
        for rec in res:
            rec.update_sale_state()
        return res

    def action_cancel(self):
        res = super(StockPicking, self).action_cancel()
        self.update_sale_state()
        return res

    def do_unreserve(self):
        res = super(StockPicking, self).do_unreserve()
        self.update_sale_state()
        return res

    def action_assign(self):
        res = super(StockPicking, self).action_assign()
        self.update_sale_state()
        return res
