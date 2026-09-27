C=env.company.id
def em():
    G=env['ls.env.grade']
    gA=G.create({'name':'Grade A','code':'A','sequence':1,'reference_document':'EU GMP Annex 1'})
    gB=G.create({'name':'Grade B','code':'B','sequence':2,'reference_document':'EU GMP Annex 1'})
    gC=G.create({'name':'Grade C','code':'C','sequence':3,'reference_document':'EU GMP Annex 1'})
    P=env['ls.env.parameter']
    pAA=P.create({'name':'Active air (viable)','code':'AA','parameter_type':'viable_air_active','result_type':'quantitative','uom_label':'CFU/m3','incubation_required':True})
    pSP=P.create({'name':'Settle plate 4 h','code':'SP','parameter_type':'viable_air_passive','result_type':'quantitative','uom_label':'CFU/4h','incubation_required':True})
    pDP=P.create({'name':'Differential pressure','code':'DP','parameter_type':'differential_pressure','result_type':'quantitative','uom_label':'Pa'})
    Mm=env['ls.env.method']
    mAA=Mm.create({'name':'Active air sampler 1 m3, TSA','code':'M-AA','parameter_id':pAA.id,'media_type':'TSA','sample_volume':1000,'sample_volume_uom_label':'L'})
    mSP=Mm.create({'name':'Settle plate 90 mm TSA, 4 h','code':'M-SP','parameter_id':pSP.id,'media_type':'TSA','exposure_duration_minutes':240})
    A=env['ls.env.area']
    site=A.create({'name':'Sterile block','code':'STB'})
    fill=A.create({'name':'Filling room F-1','code':'F1','parent_id':site.id,'grade_id':gB.id})
    cor=A.create({'name':'Corridor C-2','code':'C2','parent_id':site.id,'grade_id':gC.id})
    S=env['ls.env.sampling_point']
    a01=S.create({'name':'Needle area (RABS)','code':'A-01','area_id':fill.id,'grade_id':gA.id,'is_critical':True,'position_description':'Inside RABS, 20 cm from filling needles','selection_rationale':'Critical zone where open containers are exposed; smoke study 2026-03 shows first air at this position.'})
    c12=S.create({'name':'Corridor near material airlock','code':'C-12','area_id':cor.id,'grade_id':gC.id,'position_description':'1 m from airlock door, floor level','selection_rationale':'Worst case for ingress from the material airlock (traffic study).'})
    return locals()
d=tryit('em ref',em)
def plan_limits():
    pl=env['ls.env.plan'].with_user(UA).create({'name':'EM programme - sterile block','code':'EMP-STB','version':1,'area_id':d['site'].id,'effective_date':fields.Date.today(),'rationale':'Based on risk assessment RA-EM-2026-01 and EU GMP Annex 1 section 9.',
        'line_ids':[(0,0,{'sampling_point_id':d['a01'].id,'parameter_id':d['pAA'].id,'method_id':d['mAA'].id,'occupancy_state':'in_operation','frequency_interval':1,'frequency_unit':'day','start_date':fields.Date.today()}),
                    (0,0,{'sampling_point_id':d['c12'].id,'parameter_id':d['pSP'].id,'method_id':d['mSP'].id,'occupancy_state':'in_operation','frequency_interval':1,'frequency_unit':'week','start_date':fields.Date.today()})]})
    pl.with_user(UB).action_approve()
    L=env['ls.env.limit']
    l1=L.with_user(UA).create({'sampling_point_id':d['a01'].id,'parameter_id':d['pAA'].id,'occupancy_state':'in_operation','direction':'upper','action_value':1,'action_set':True,'justification':'Grade A limit per EU GMP Annex 1 (in operation).','source_reference':'EU GMP Annex 1 table 6'})
    l1.with_user(UB).action_approve()
    l2=L.with_user(UA).create({'sampling_point_id':d['c12'].id,'parameter_id':d['pSP'].id,'occupancy_state':'in_operation','direction':'upper','alert_value':25,'alert_set':True,'action_value':50,'action_set':True,'escalate_alert':True,'justification':'Grade C settle plate action level; alert at 50 % of action from 2025 history.','source_reference':'EU GMP Annex 1 table 6; trend report 2025'})
    l2.with_user(UB).action_approve()
    return pl
pl=tryit('plan & limits',plan_limits)
def samples():
    out=[]
    for pt,par,val,name in [(d['c12'],d['pSP'],31,'EMS-2026-0918'),(d['a01'],d['pAA'],0,'EMS-2026-0919'),(d['c12'],d['pSP'],12,'EMS-2026-0920')]:
        s=env['ls.env.sample'].with_user(UA).create({'name':name,'sampling_point_id':pt.id,'occupancy_state':'in_operation','scheduled_date':fields.Date.today(),'plan_id':pl.id,'batch_reference':'26F044' if pt==d['a01'] else False,
            'result_ids':[(0,0,{'parameter_id':par.id,'method_id':(d['mSP'] if par==d['pSP'] else d['mAA']).id})]})
        s.with_user(UA).action_schedule(); s.with_user(UA).write({'collection_datetime':fields.Datetime.now()-timedelta(days=3),'collected_by_id':UA.id}); s.with_user(UA).action_collect(); s.with_user(UA).action_start_analysis()
        s.result_ids.with_user(UA).write({'value_numeric':val,'value_set':True})
        s.with_user(UA).action_enter_results()
        if name!='EMS-2026-0920':
            s.with_user(UB).action_review(); s.with_user(UB).action_approve()
        out.append(s)
    return out
ss=tryit('samples',samples)
def exc():
    e=env['ls.env.excursion'].search([],limit=1,order='id desc')
    if not e: return 'none'
    e.with_user(UB).write({'owner_id':UB.id,'immediate_actions':'Corridor resampled; airlock door interlock checked - found faulty.','severity':'minor'})
    e.with_user(UB).action_start_assessment()
    e.with_user(UB).write({'impact_assessment':'Grade C corridor, no open product; filling room pressure cascade maintained (DP records reviewed).','product_impact':'none'})
    return e.name, e.state
tryit('excursion',exc)
env.cr.commit()
