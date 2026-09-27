def cos():
    I=env['ls.cosmetic.ingredient']
    ing=[I.create(v) for v in [
        {'inci_name':'Aqua','cas_number':'7732-18-5','technical_function':'Solvent','regulatory_category':'none'},
        {'inci_name':'Glycerin','cas_number':'56-81-5','technical_function':'Humectant','regulatory_category':'none'},
        {'inci_name':'Caprylic/Capric Triglyceride','technical_function':'Emollient','regulatory_category':'none'},
        {'inci_name':'Cetearyl Alcohol','technical_function':'Emulsion stabiliser','regulatory_category':'none'},
        {'inci_name':'Phenoxyethanol','cas_number':'122-99-6','technical_function':'Preservative','regulatory_category':'preservative'},
        {'inci_name':'Parfum','technical_function':'Perfuming','regulatory_category':'none','is_perfume_component':True,'perfume_term':'parfum'},
        {'inci_name':'CI 77891','technical_function':'Colorant','regulatory_category':'colorant','colour_index':'77891'}]]
    conc=[78.3,6.0,8.0,6.0,0.9,0.3,0.5]
    f=env['ls.cosmetic.formulation'].with_user(UA).create({'code':'FC-120','name':'Hydrating face cream','version':1,'intended_use':'Leave-on face cream, twice daily, adult consumers.','target_population':'Adults, general population',
        'line_ids':[(0,0,{'ingredient_id':i.id,'concentration':c,'sequence':k*10}) for k,(i,c) in enumerate(zip(ing,conc))]})
    f.with_user(UA).action_submit_review(); f.with_user(UB).action_approve(); return f.state, f.total_percentage
tryit('cosmetics',cos)
def mp():
    comp_p=product('Syringe plunger SP-5', tracking='lot')
    g=env['ls.mp.material.grade'].create({'name':'PP homopolymer medical grade','code':'PP-MG-01','polymer_type':'pp','drug_contact':True,'master_file_reference':'DMF 12345 (example)','change_notification_agreement':True,'melt_flow_index':12,'melt_flow_index_uom':'g/10 min','default_quantity_uom':'kg'})
    g.action_set_under_evaluation(); g.write({'qualification_date':fields.Date.today()-timedelta(days=200),'requalification_date':fields.Date.today()+timedelta(days=530)}); g.action_qualify()
    c=env['ls.mp.component'].create({'name':'Syringe plunger SP-5','code':'SP-5','product_id':comp_p.id,'category':'syringe_plunger','is_primary_packaging':True,'criticality':'critical','drug_contact':True,'material_grade_ids':[(6,0,[g.id])],'primary_material_grade_id':g.id,'nominal_part_weight':1.25,'part_weight_tolerance':0.03,'part_weight_uom':'g','drawing_reference':'DRW-SP5','drawing_revision':'C'})
    c.action_release()
    t=env['ls.mp.tool'].create({'name':'Mould T-032 (8 cavities)','code':'T-032','tool_type':'injection_mold','cavity_count':8,'component_ids':[(6,0,[c.id])],'serial_no':'TM-2025-0457','steel_grade':'1.2083 stainless','maintenance_interval_shots':250000,'maintenance_interval_months':6,'requalification_interval_months':36,'opening_shot_count':0})
    t.write({'qualification_date':fields.Date.today()-timedelta(days=120)}); t.action_qualify(); t.action_place_in_service()
    s=env['ls.mp.molding_parameter'].with_user(UA).create({'name':'SP-5 on T-032','component_id':c.id,'tool_id':t.id,'version':1,'author_id':UA.id,'review_interval_months':24,
        'line_ids':[(0,0,v) for v in [
           {'name':'Melt temperature','code':'MT','parameter_uom':'°C','value_type':'numeric','target_value':230,'min_value':220,'max_value':240,'is_critical':True,'monitoring_frequency':'hourly','record_required':True},
           {'name':'Injection pressure','code':'IP','parameter_uom':'bar','value_type':'numeric','target_value':850,'min_value':800,'max_value':900,'is_critical':True,'monitoring_frequency':'continuous','record_required':True},
           {'name':'Cooling time','code':'CT','parameter_uom':'s','value_type':'numeric','target_value':8,'min_value':7,'max_value':9,'is_critical':False,'monitoring_frequency':'per_shift','record_required':True},
           {'name':'Visual aspect','code':'VA','parameter_uom':'-','value_type':'qualitative','expected_text':'No flash','is_critical':False,'monitoring_frequency':'per_lot','record_required':True}]]})
    s.with_user(UA).action_submit_for_review(); s.with_user(UB).action_review(); s.with_user(UC).action_approve()
    return c,t,s,g
res=tryit('plastics',mp)
env.cr.commit()
