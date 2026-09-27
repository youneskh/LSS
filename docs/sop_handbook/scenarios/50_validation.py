W=env['ls.validation.sign.wizard']
def sign(rec, user, action):
    res=getattr(rec.with_user(user), action)()
    ctx=res.get('context',{}) if isinstance(res,dict) else {}
    vals={k[8:]:v for k,v in ctx.items() if k.startswith('default_')}
    vals.update({'login':user.login,'password':user.login})
    w=W.with_user(user).with_context(**ctx).create(vals)
    return w.action_sign()
vmp=env['ls.validation.master.plan'].browse(1); prot=env['ls.validation.protocol'].browse(1)
def do_vmp():
    if not vmp.scope: vmp.write({'scope':'<p>All GxP equipment, utilities, processes, cleaning and computerised systems of the sterile block.</p>','strategy':'<p>Risk-based V-model; direct impact: IQ/OQ/PQ.</p>'} if 'strategy' in vmp._fields else {'scope':'<p>All GxP equipment of the sterile block.</p>'})
    vmp.with_user(UA).action_submit_review(); sign(vmp, UC, 'action_approve'); vmp.with_user(UC).action_activate(); return vmp.state
def do_prot():
    if not prot.test_ids:
        prot.write({'test_ids':[(0,0,{'code':'OQ-%02d'%i,'name':n,'acceptance_criteria':a,'is_critical':c,'sequence':i}) for i,(n,a,c) in enumerate([
            ('Alarm and interlock checks','All alarms trigger and interlocks prevent door opening during cycle.',True),
            ('Chamber temperature uniformity, empty chamber','All probes 121.0-124.0 °C during the 15 min plateau.',True),
            ('Vacuum leak test','Leak rate <= 1.3 mbar/min.',False)],1)]})
    prot.with_user(UA).action_submit_review(); sign(prot, UC, 'action_approve'); return prot.state
tryit('vmp', do_vmp)
tryit('protocol', do_prot)
env.cr.commit()
def do_exec():
    res=prot.with_user(UA).action_create_execution()
    ex=env['ls.validation.execution'].search([('protocol_id','=',prot.id)],limit=1,order='id desc')
    ex.with_user(UA).action_regenerate_results(); ex.with_user(UA).action_start()
    print('RESULTS', [(r.code, r.name) for r in ex.result_ids])
    for r in ex.result_ids:
        if r == ex.result_ids.sorted('sequence')[min(1,len(ex.result_ids)-1)]:
            r.with_user(UA).write({'actual_result':'Probe 7 reached 124.6 °C for 40 s at minute 6 of the plateau.','verdict':'fail','performed_by_id':UA.id,'performed_on':fields.Datetime.now()})
        else:
            r.with_user(UA).write({'actual_result':'Conforms.','verdict':'pass','performed_by_id':UA.id,'performed_on':fields.Datetime.now()})
    bad=ex.result_ids.filtered(lambda r:r.verdict=='fail')
    bad.with_user(UA).action_create_discrepancy()
    d=bad.discrepancy_id
    if d: d.with_user(UA).write({'description':'Probe 7 above 124.0 °C for 40 s.','immediate_action':'Probe positions checked; probe 7 found touching chamber wall.'})
    return ex.state, d.reference if d else None
tryit('execution', do_exec)
env.cr.commit()
