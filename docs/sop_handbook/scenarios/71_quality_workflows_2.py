def cc():
    r=env['ls.change_control.request'].search([('state','=','draft')],limit=1)
    areas=env['ls.change_control.impact_area'].search([],limit=3)
    r.with_user(UC).write({'manager_id':UC.id,'impact_area_ids':[(6,0,areas.ids)]})
    r.with_user(UA).action_submit_review()
    r._generate_approvals()
    for ap in r.approval_ids.filtered(lambda a: not a.user_id):
        ap.sudo().write({'user_id':UC.id})
    r.with_user(UC).action_start_assessment()
    a=r.assessment_ids[:1]
    a.with_user(UC).write({'impact':'medium','assessment':'Requires OQ of the press with new tooling; SOP-PRD-014 to be revised.','actions_required':'OQ protocol; SOP revision; operator training.'})
    a.with_user(UC).action_complete()
    return r.state, len(r.assessment_ids), len(r.approval_ids)
tryit('change control', cc)
def cmp():
    c=env['ls.complaint'].search([('state','=','received')],limit=1)
    f=[n for n in env['ls.complaint']._fields if n in ('responsible_id','user_id','owner_id','assigned_to_id')]
    c.write({f[0]:UB.id,'reviewer_id':UC.id} if f else {'reviewer_id':UC.id})
    if not c.product_id: c.write({'product_id':TAB.id})
    c.with_user(UB).action_start_assessment()
    c.with_user(UB).write({'severity':'minor','assessment_summary':'Single broken tablet reported; no safety impact.'})
    c.with_user(UB).action_start_investigation()
    env['ls.complaint.investigation'].with_user(UA).create({'name':'INV-1','complaint_id':c.id,'investigator_id':UA.id,'methodology':'batch_record_review','investigation_plan':'Review batch record, IPC hardness, retained samples and complaints on the same lot.','date_started':fields.Datetime.now()})
    return c.state
tryit('complaint',cmp)
def audit():
    p=env['ls.audit.program'].search([('state','=','draft')],limit=1)
    p.with_user(UC).action_approve(); p.with_user(UC).action_start()
    a=env['ls.audit.schedule'].search([('state','=','planned')],limit=1)
    a.with_user(UC).action_schedule()
    return p.state, a.state
tryit('audit',audit)
env.cr.commit()
