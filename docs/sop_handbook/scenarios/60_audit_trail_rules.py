M=env['ir.model']
def rules():
    out=[]
    for model,note in [('ls.deviation','GxP record: deviation decisions and dates (data risk assessment DRA-2026-01).'),('ls.lab.test_result','GxP record: laboratory results used for release (DRA-2026-01).'),('ls.pharma.batch','GxP record: batch status, yields and dates (DRA-2026-01).')]:
        r=env['ls.audit_trail.rule'].with_user(UC).create({'name':'Audit '+model,'model_id':M._get_id(model),'log_create':True,'log_write':True,'log_unlink':True,'note':note})
        out.append(r)
    return out
tryit('rules',rules)
env.cr.commit()
