from odoo import fields
from datetime import timedelta
def tryit(label, fn):
    try:
        with env.cr.savepoint():
            r = fn(); print('OK', label, r); return r
    except Exception as e:
        print('FAIL', label, type(e).__name__, str(e)[:400])
imd=env['ir.model.data'].search([('model','=','res.groups'),('module','like','ls_%')])
ls_groups=env['res.groups'].browse(imd.mapped('res_id'))
def mkuser(login,name):
    u=env['res.users'].with_context(active_test=False).search([('login','=',login)])
    if not u:
        u=env['res.users'].create({'name':name,'login':login,'password':login,'email':login+'@example.com'})
    u.write({'group_ids':[(4,g.id) for g in ls_groups]+[(4,env.ref('base.group_user').id)]})
    if not u.employee_ids and 'hr.employee' in env:
        env['hr.employee'].create({'name':name,'user_id':u.id})
    return u
UA=mkuser('demo.analyst','QC Analyst (demo)')
UB=mkuser('demo.reviewer','QA Reviewer (demo)')
UC=mkuser('demo.manager','QA Manager (demo)')
ADMIN=env.ref('base.user_admin')
def product(name, tracking='lot'):
    p=env['product.product'].search([('name','=',name)],limit=1)
    if not p:
        p=env['product.product'].create({'name':name,'is_storable':True,'tracking':tracking})
    return p
TAB=product('Tablets 10 mg')
def lot(p,name):
    l=env['stock.lot'].search([('name','=',name),('product_id','=',p.id)],limit=1)
    return l or env['stock.lot'].create({'name':name,'product_id':p.id})
