M=env['ls.lab.test_method']
def methods():
    out=[]
    for code,name,tech,rt in [('AM-012','Assay by HPLC','chromatographic','numeric'),('DS-004','Dissolution','physical','numeric'),('AP-001','Appearance','physical','text')]:
        m=M.with_user(UA).create({'name':name,'code':code,'version':'3','technique':tech,'result_type':rt,'validation_status':'validated','validation_reference':'VAL-MV-'+code})
        m.with_user(UA).action_submit_review(); m.with_user(UB).action_approve(); out.append(m)
    return out
ms=tryit('methods',methods)
env.cr.commit()
ms=env['ls.lab.test_method'].search([('code','in',['AM-012','DS-004','AP-001']),('state','=','approved')])
bycode={m.code:m for m in ms}
def spec():
    s=env['ls.lab.specification'].with_user(UA).create({'name':'Tablets 10 mg - finished product','code':'SPEC-TAB10-FP','version':4,'product_id':TAB.id,'spec_type':'finished_product',
        'line_ids':[(0,0,{'test_method_id':bycode['AM-012'].id,'criterion_type':'range','min_value':95.0,'max_value':105.0,'is_mandatory':True,'report_on_coa':True}),
                    (0,0,{'test_method_id':bycode['DS-004'].id,'criterion_type':'min','min_value':80.0,'is_mandatory':True,'report_on_coa':True}),
                    (0,0,{'test_method_id':bycode['AP-001'].id,'criterion_type':'text','text_criterion':'White round tablet','is_mandatory':True,'report_on_coa':True})]})
    s.with_user(UA).action_submit_review(); s.with_user(UB).action_approve(); return s
sp=tryit('spec',spec)
L=lot(TAB,'26T018')
def sample():
    s=env['ls.lab.sample'].with_user(UA).create({'name':'LS-2026-0412','sample_type':'finished_product','product_id':TAB.id,'lot_id':L.id,'batch_reference':'26T018','specification_id':sp.id,'quantity':60,'received_date':fields.Datetime.now(),'sampled_by_id':UA.id,'received_by_id':UA.id,'sampling_point':'Packaging line PK-2'})
    s.with_user(UA).action_start(); s.with_user(UA).action_start_testing()
    vals={'AM-012':99.2,'DS-004':91.0,'AP-001':'White round tablet'}
    for r in s.result_ids:
        v=vals[r.test_method_id.code]
        d={'analyst_id':UA.id,'test_date':fields.Datetime.now(),'instrument_reference':'HPLC-04' if r.test_method_id.code=='AM-012' else 'DISSO-02'}
        if isinstance(v,str): d['result_text']=v
        else: d['result_numeric']=v
        r.with_user(UA).write(d); r.with_user(UA).action_enter()
    s.with_user(UA).action_record_results()
    for r in s.result_ids: r.with_user(UB).action_review()
    s.with_user(UB).action_review()
    return s
smp=tryit('sample',sample)
def approve():
    smp.with_user(UC).action_approve(); return smp.state
tryit('approve sample', approve)
def coa():
    c=env['ls.lab.coa'].with_user(UC).create({'name':'COA-26T018','version':1,'sample_id':smp.id})
    c.with_user(UC).action_issue(); return c.state
tryit('coa',coa)
# second sample with OOS
def sample2():
    s=env['ls.lab.sample'].with_user(UA).create({'name':'LS-2026-0431','sample_type':'finished_product','product_id':TAB.id,'lot_id':lot(TAB,'26T021').id,'batch_reference':'26T021','specification_id':sp.id,'quantity':60,'received_date':fields.Datetime.now()})
    s.with_user(UA).action_start(); s.with_user(UA).action_start_testing()
    for r in s.result_ids:
        c=r.test_method_id.code
        d={'analyst_id':UA.id,'test_date':fields.Datetime.now()}
        if c=='AP-001': d['result_text']='White round tablet'
        elif c=='DS-004': d['result_numeric']=76.0
        else: d['result_numeric']=98.7
        r.with_user(UA).write(d); r.with_user(UA).action_enter()
    bad=s.result_ids.filtered(lambda r:r.test_method_id.code=='DS-004')
    o=env['ls.lab.oos'].with_user(UB).create({'name':'OOS-2026-007','oos_type':'oos','test_result_id':bad.id,'investigator_id':UB.id,'opened_date':fields.Datetime.now(),'description':'Dissolution 76 % at 30 min (NLT 80 %).'})
    o.with_user(UB).action_start_phase1()
    o.with_user(UB).write({'chk_analyst_interview':True,'chk_calculation_verified':True,'chk_instrument_verified':True,'phase1_findings':'Vessel 4 paddle height out of tolerance at post-test check (27 mm, requirement 25 +/- 2 mm).'})
    return o
tryit('oos',sample2)
env.cr.commit()
