def changes():
    d=env['ls.deviation'].search([('state','=','reported')],limit=1)
    d.with_user(UB).write({'impact_assessment':'Temperature excursion of 2 h at 27 °C; product stability data support up to 30 °C for 1 month; no impact expected.'})
    d.with_user(UB).write({'severity':'major'})
    b=env['ls.pharma.batch'].search([('name','=','26T021')])
    b.with_user(UB).write({'note':'Awaiting QC results before QA review.'})
    return env['ls.audit_trail.log'].search_count([])
tryit('changes',changes)
env.cr.commit()
def verify():
    w=env['ls.audit_trail.verify.wizard'].with_user(UC).create({'company_id':env.company.id,'scope':'full'})
    w.action_verify(); return env['ls.audit_trail.verification'].search([],limit=1,order='id desc').mapped('result')
tryit('verify',verify)
env.cr.commit()
def pack():
    p=env['ls.audit_trail.evidence_pack'].with_user(UC).create({'name':'EP-2026-001','purpose':'Inspection 2026-10, request #7: changes to deviations and batches.','company_id':env.company.id,'date_from':fields.Datetime.now()-timedelta(days=1),'date_to':fields.Datetime.now()+timedelta(minutes=5)})
    p.with_user(UC).action_generate(); return p.state, p.entry_count, p.pack_digest
tryit('pack',pack)
env.cr.commit()
