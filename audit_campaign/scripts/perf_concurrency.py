# Run with:  odoo shell -c /etc/odoo/odoo.conf -d <scratch db>  < perf_concurrency.py
# Measures the cost of the ls_audit_trail hooks on stock validation and checks
# concurrent validation for deadlocks / serialization failures (finding F-10).
# It COMMITS data: use a scratch database only.
import functools
import threading
import time
import traceback

from odoo import SUPERUSER_ID, api
from odoo.service.model import retrying

N_SEQ = 30          # pickings per sequential timing run
N_PER_THREAD = 15   # pickings per thread in the concurrency run

env = env(context=dict(env.context, tracking_disable=True))  # noqa: F821  (provided by odoo shell)
cr = env.cr
company = env.company
wh = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
customer = env.ref("stock.stock_location_customers")
vals = {"name": "PERF product", "type": "consu"}
if "is_storable" in env["product.template"]._fields:
    vals["is_storable"] = True
product = env["product.product"].create(vals)
env["stock.quant"]._update_available_quantity(product, wh.lot_stock_id, 100000)
partner = env["res.partner"].create({"name": "PERF customer"})
cr.commit()
print("PERF setup done: product", product.id)


def make_pickings(e, n):
    ids = []
    for _ in range(n):
        p = e["stock.picking"].create({
            "picking_type_id": wh.out_type_id.id,
            "location_id": wh.lot_stock_id.id,
            "location_dest_id": customer.id,
            "partner_id": partner.id,
        })
        e["stock.move"].create({
            "product_id": product.id, "product_uom_qty": 1, "product_uom": product.uom_id.id,
            "picking_id": p.id, "location_id": wh.lot_stock_id.id, "location_dest_id": customer.id,
        })
        p.action_confirm()
        p.action_assign()
        ids.append(p.id)
    e.cr.commit()
    return ids


def validate(e, pid):
    p = e["stock.picking"].browse(pid)
    p.move_ids.picked = True
    p.button_validate()


def sequential(label):
    ids = make_pickings(env, N_SEQ)
    t0 = time.perf_counter()
    for pid in ids:
        validate(env, pid)
        cr.commit()
    dt = time.perf_counter() - t0
    print(f"PERF sequential [{label}] {N_SEQ} pickings: {dt:.2f}s total, {1000 * dt / N_SEQ:.0f} ms/picking")
    return dt


def concurrent(label, server_retry=False):
    """Validate 2 x N pickings from two threads.

    With ``server_retry``, each validation runs through
    ``odoo.service.model.retrying``, the loop the Odoo server applies to
    every RPC and HTTP request: serialization failures are rolled back and
    replayed (up to 5 attempts), unique violations are not.
    """
    ids_a = make_pickings(env, N_PER_THREAD)
    ids_b = make_pickings(env, N_PER_THREAD)
    errors = []
    done = [0]

    def worker(ids):
        with env.registry.cursor() as tcr:
            tenv = api.Environment(tcr, SUPERUSER_ID, {"tracking_disable": True})
            for pid in ids:
                try:
                    if server_retry:
                        retrying(functools.partial(validate, tenv, pid), tenv)
                    else:
                        validate(tenv, pid)
                    tcr.commit()
                    done[0] += 1
                except Exception as error:  # noqa: BLE001
                    tcr.rollback()
                    errors.append(f"{type(error).__name__}: {str(error).splitlines()[0][:160]}")

    t0 = time.perf_counter()
    threads = [threading.Thread(target=worker, args=(ids,)) for ids in (ids_a, ids_b)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    dt = time.perf_counter() - t0
    print(f"PERF concurrent [{label}] 2 threads x {N_PER_THREAD}: {dt:.2f}s, validated={done[0]}, errors={len(errors)}")
    for err in sorted(set(errors)):
        print(f"PERF concurrent [{label}] error: {err} (x{errors.count(err)})")


try:
    t_plain = sequential("no audit rule")
    concurrent("no audit rule")
    concurrent("no audit rule, server retry", server_retry=True)
    rules = env["ls.audit_trail.rule"]
    for model in ("stock.picking", "stock.move", "stock.move.line", "stock.quant"):
        model_id = env["ir.model"]._get(model).id
        # One rule per model and company (F-38): reuse the rule of an
        # earlier run, archived at the end of that run, when it exists.
        existing = rules.with_context(active_test=False).search(
            [("model_id", "=", model_id), ("company_id", "=", False)], limit=1
        )
        values = {"log_create": True, "log_write": True, "log_unlink": True}
        if existing:
            existing.write(dict(values, active=True, field_ids=[(5, 0, 0)]))
            rules |= existing
        else:
            rules |= rules.create(dict(values, name=f"PERF rule {model}", model_id=model_id))
    cr.commit()
    t_audit = sequential("audit on 4 stock models")
    print(f"PERF overhead of auditing stock models: x{t_audit / t_plain:.2f}")
    concurrent("audit on 4 stock models")
    concurrent("audit on 4 stock models, server retry", server_retry=True)
    outcome = env["ls.audit_trail.log"]._ls_verify_chain(company)
    print(f"PERF chain verification after concurrent run: passed={outcome['passed']}")
    rules.write({"active": False})
    cr.commit()
except Exception:  # noqa: BLE001
    print("PERF SCRIPT ERROR")
    traceback.print_exc()
print("PERF end")
