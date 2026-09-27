UO=mkuser('demo.operator','Production Operator (demo)'); UO2=mkuser('demo.operator2','Production Operator 2 (demo)')
R=env['ls.mp.injection_molding.reading']
c=env['ls.mp.component'].search([('code','=','SP-5')]); t=env['ls.mp.tool'].search([('code','=','T-032')]); s=env['ls.mp.molding_parameter'].search([('state','=','approved')],limit=1); g=env['ls.mp.material.grade'].search([('code','=','PP-MG-01')])
def run():
    L=lot(c.product_id,'SP5-2711')
    r=env['ls.mp.injection_molding'].with_user(UO).create({'name':'MR-2027-118','component_id':c.id,'tool_id':t.id,'parameter_spec_id':s.id,'lot_id':L.id,'shift':'shift_1','operator_id':UO.id,'setter_id':UO2.id,'shot_count_start':0})
    r.with_user(UO2).action_start_setup()
    vals={'MT':231,'IP':848,'CT':8.0}
    def rd(rtype, override=None, when=None):
        for ln in s.line_ids:
            d={'run_id':r.id,'parameter_line_id':ln.id,'reading_type':rtype,'capture_date':when or fields.Datetime.now(),'recorded_by_id':UO.id}
            if ln.value_type=='numeric': d['value_numeric']=(override or {}).get(ln.code, vals[ln.code])
            else: d[QF]='No flash'
            R.with_user(UO).create(d)
    rd('setup')
    r.with_user(UO2).action_start_startup_check()
    rd('startup')
    env['ls.mp.injection_molding.material'].with_user(UO).create({'run_id':r.id,'material_grade_id':g.id,'supplier_lot_reference':'R-5531','quantity':150,'quantity_uom':'kg'})
    r.with_user(UO2).action_confirm_startup()
    for h in range(1,4): rd('in_process', override={'IP':905} if h==2 else None, when=fields.Datetime.now()+timedelta(hours=h))
    r.with_user(UO).write({'shot_count_end':96600,'qty_produced':676200,'qty_rejected':1900,'has_deviation':True,'deviation_reference':'DEV/2027/00012'})
    r.with_user(UO).action_complete()
    return r.state
QF=[n for n,f in R._fields.items() if n in ('value_text','observed_value','value_qualitative')][0] if any(n in R._fields for n in ('value_text','observed_value','value_qualitative')) else None
print('QF',QF)
tryit('run',run)
env.cr.commit()
