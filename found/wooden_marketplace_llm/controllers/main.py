from odoo import http
from odoo.http import request

class WoodenMarketplaceController(http.Controller):

    @http.route('/create_product', type='web', auth='user', website=True)
    def create_product(self, **kwargs):
        return request.render('wooden_marketplace.product_form_template')

    @http.route('/save_product', type='json', auth='user', website=True)
    def save_product(self, product_name, sale_price, image_1920=None, vendor_id=None, approval_state='draft'):
        user = request.env.user
        partner = user.partner_id

        # Create a new product template
        product_template = request.env['product.template'].sudo().create({
            'name': product_name,
            'list_price': sale_price,
            'image_1920': image_1920,
            'vendor_id': vendor_id if user.has_group('wooden_marketplace.vendor_group') else False,
            'approval_state': approval_state
        })

        # Create a new product variant
        request.env['product.product'].sudo().create({
            'product_tmpl_id': product_template.id,
            'name': product_name,
            'list_price': sale_price,
            'image_1920': image_1920
        })

        return {
            'message': 'Product created successfully',
            'product_id': product_template.id
        }
