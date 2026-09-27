def capa():
    c=env['ls.capa.issue'].search([('state','=','identified')],limit=1)
    c.with_user(UB).write({'impact_assessment':'Potential impact on product quality for batches filled after maintenance; no patient impact identified (batches quarantined).','immediate_action':'Alarm routing restored; affected units quarantined.','quality_impact':True})
    c.with_user(UB).action_assess(); c.with_user(UB).action_start_investigation()
    rc=env['ls.capa.root_cause'].with_user(UB).create({'name':'RCA-1','issue_id':c.id,'method':'five_whys','description':'No step to restore alarm routing after maintenance interventions.','is_primary':True,'analyst_id':UB.id,'date_analysis':fields.Date.today(),
        'why_1':'Why was the alarm not seen? Routing to the pager was disabled.','why_2':'Why disabled? Muted during maintenance.','why_3':'Why not restored? No restore step in the work order.','why_4':'Why no step? Template written before BMS alarms were routed.','why_5':'Why not updated? No change control link between BMS and maintenance templates.'})
    rc.with_user(UB).action_confirm()
    c.with_user(UB).action_start_action_planning()
    for i,(t,dsc,days) in enumerate([('corrective','Add alarm-restore checklist to the maintenance work order template.',30),('corrective','Train maintenance technicians on the new checklist.',45),('preventive','Weekly automatic test of alarm routing.',45)]):
        env['ls.capa.action'].with_user(UB).create({'name':'ACT-%d'%(i+1),'issue_id':c.id,'root_cause_id':rc.id,'action_type':t,'description':dsc,'responsible_id':UC.id,'date_planned':fields.Date.today()+timedelta(days=days)})
    c.with_user(UB).action_start_progress()
    a=c.action_ids[:1]; a.with_user(UC).action_start(); a.with_user(UC).write({'completion_evidence':'Work order template WO-TPL-07 rev 3 published.'}); a.with_user(UC).action_done()
    return c.state
tryit('capa',capa)
def training():
    s=env['ls.training.session'].search([('state','=','draft')],limit=1)
    emps=env['hr.employee'].search([],limit=4)
    s.write({'attendance_ids':[(0,0,{'employee_id':e.id}) for e in emps if e not in s.attendance_ids.mapped('employee_id')]})
    s.with_user(UC).action_confirm(); s.with_user(UC).action_start()
    for i,a in enumerate(s.attendance_ids):
        a.with_user(UC).write({'attended':True,'score':100.0 if i<3 else 80.0})
    s.with_user(UC).action_close()
    return s.state, len(s.certification_ids)
tryit('training',training)
env.cr.commit()
