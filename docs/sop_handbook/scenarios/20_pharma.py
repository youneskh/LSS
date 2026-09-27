UO=mkuser('demo.operator','Production Operator (demo)')
UO2=mkuser('demo.operator2','Production Operator 2 (demo)')
API=product('API X lot-tracked'); EXC=product('Microcrystalline cellulose PH-102')
uom=TAB.uom_id
def batch_pharma(name, release=False):
    L=lot(TAB,name)
    b=env['ls.pharma.batch'].with_user(UO).create({'name':name,'batch_type':'finished','product_id':TAB.id,'lot_id':L.id,'uom_id':uom.id,'planned_qty':120000,'theoretical_yield_qty':120000,'yield_min_percentage':96,'yield_max_percentage':101,'shelf_life_months':36,'date_manufacture':fields.Date.today(),'date_expiry':fields.Date.today()+timedelta(days=3*365)})
    r=env['ls.pharma.batch_record'].with_user(UO).create({'name':'BR-'+name,'batch_id':b.id,'record_type':'manufacturing','master_record_reference':'MR-TAB10','master_record_version':'7',
        'step_ids':[(0,0,{'sequence':i*10,'name':n,'instruction':ins,'is_significant':sig}) for i,(n,ins,sig) in enumerate([
            ('Dispensing verification','Verify identity and quantity of all dispensed components.',True),
            ('Dry mixing','Mix 10 min at 15 rpm.',False),
            ('Dry granulation','Roller compaction, gap 2.0 mm, 12 min.',True),
            ('Blending with lubricant','Add magnesium stearate, blend 3 min.',True),
            ('Compression','Target weight 200 mg, hardness 60-90 N.',True)])],
        'control_ids':[(0,0,{'name':'Tablet weight (mean of 20)','control_type':'in_process','result_type':'numeric','specification_text':'194-206 mg','specification_min':194,'specification_max':206,'has_minimum':True,'has_maximum':True}),
                       (0,0,{'name':'Hardness','control_type':'in_process','result_type':'numeric','specification_text':'60-90 N','specification_min':60,'specification_max':90,'has_minimum':True,'has_maximum':True})],
        'clearance_ids':[(0,0,{'moment':'before','area':'Compression room C-3 / press TP-02','date_performed':fields.Datetime.now(),'performed_by_user_id':UO.id,'verified_by_user_id':UO2.id,'result':'pass','previous_product':'Capsules 20 mg'})],
        'labeling_ids':[(0,0,{'name':'Bulk container label','label_version':'2','label_code':'LBL-BULK-TAB10','quantity_issued':30,'quantity_used':28,'quantity_returned':0,'quantity_destroyed':2,'tolerance':0})]})
    r.with_user(UO2).write({'master_checked_by_user_id':UO2.id,'master_checked_date':fields.Datetime.now()})
    b.with_user(UO).action_start(); r.with_user(UO).action_start_execution()
    for s in r.step_ids:
        s.with_user(UO).write({'performed_by_user_id':UO.id,'checked_by_user_id':UO2.id if s.is_significant else False,'date_performed':fields.Datetime.now(),'recorded_value':'done'})
        s.with_user(UO).action_done()
    for c,v in zip(r.control_ids,[199.4,74.0]):
        c.with_user(UO).write({'result_value':v,'performed_by_user_id':UO.id,'date_performed':fields.Datetime.now()})
    env['ls.pharma.batch.component'].with_user(UO).create({'batch_id':b.id,'product_id':API.id,'component_lot_reference':'A2210','quantity':5.012,'uom_id':API.uom_id.id,'assay_percentage':99.6,'is_active_ingredient':True,'charged_by_user_id':UO.id,'verified_by_user_id':UO2.id,'date_charged':fields.Datetime.now()})
    r.with_user(UO).action_complete_execution()
    b.with_user(UO).write({'actual_yield_qty':118320,'date_start':fields.Datetime.now()-timedelta(hours=9),'date_end':fields.Datetime.now()})
    b.with_user(UO).action_complete()
    r.with_user(UO).action_submit_review()
    b.with_user(UO).action_quarantine()
    if release:
        r.with_user(UB).write({'review_conclusion':'Record complete, no discrepancy, controls conform.'})
        r.with_user(UB).action_approve()
        b.with_user(UO).action_submit_review()
        w=env['ls.pharma.batch.release.wizard'].with_user(UB).create({'batch_id':b.id,'decision':'released','statement':'All checks verified; QC results approved (LS-2026-0412).','check_record_reviewed':True,'check_discrepancies_closed':True,'check_yield_within_limits':True,'check_components_verified':True,'check_qc_conform':True,'check_labeling_reconciled':True,'check_reserve_samples':True,'check_stability_programme':True})
        w.with_user(UB).action_confirm()
    return b.state
tryit('batch 26T018', lambda: batch_pharma('26T018', release=True))
tryit('batch 26T021', lambda: batch_pharma('26T021'))
env.cr.commit()
