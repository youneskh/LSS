from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_vendor = fields.Boolean(string='Is Vendor', default=False)
    vendor_shop_name = fields.Char(string='Vendor Shop Name')
    marketplace_commission = fields.Float(string='Marketplace Commission', default=1.0)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    vendor_id = fields.Many2one('res.partner', string='Vendor', ondelete='set null')
    approval_state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
    ], string='Approval State', default='draft')

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    admin_commission_amount = fields.Float(string='Admin Commission Amount', compute='_compute_admin_commission_amount')
    vendor_net_revenue = fields.Float(string='Vendor Net Revenue', compute='_compute_vendor_net_revenue')

    @api.depends('price_subtotal')
    def _compute_admin_commission_amount(self):
        for line in self:
            line.admin_commission_amount = line.price_subtotal * 0.01

    @api.depends('price_subtotal')
    def _compute_vendor_net_revenue(self):
        for line in self:
            line.vendor_net_revenue = line.price_subtotal * 0.99
