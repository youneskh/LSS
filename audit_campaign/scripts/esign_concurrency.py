# Run with:  odoo shell -c /etc/odoo/odoo.conf -d <scratch db>  < esign_concurrency.py
# Concurrent appends to the electronic-signature chain (finding F-10, second
# chain). Two threads each append N signatures; every transaction first reads
# data (its REPEATABLE READ snapshot starts), waits, then appends, so the two
# transactions overlap. It COMMITS data: use a scratch database only.
import threading
import time

from odoo import SUPERUSER_ID, api, fields

N_PER_THREAD = 15

meaning = env["ls.signature.meaning"].search([], limit=1)  # noqa: F821
if not meaning:
    meaning = env["ls.signature.meaning"].create({"name": "Concurrency", "code": "CONC_PROBE"})  # noqa: F821
partner = env["res.partner"].create({"name": "ESIGN concurrency"})  # noqa: F821
env.cr.commit()  # noqa: F821
errors = []
done = [0]


def append(tenv, index):
    tenv["res.partner"].browse(partner.id).read(["name"])  # snapshot starts here
    time.sleep(0.05)
    user = tenv.user
    payload = '{"probe": %d}' % index
    tenv["ls.signature.log"].create({
        "company_id": tenv.company.id,
        "user_id": user.id,
        "signer_name": user.name,
        "signer_login": user.login,
        "signed_at": fields.Datetime.now(),
        "meaning_id": meaning.id,
        "meaning_code": meaning.code,
        "meaning_name": meaning.name,
        "res_model": "res.partner",
        "res_model_name": "Contact",
        "res_id": partner.id,
        "res_name": partner.name,
        "payload_json": payload,
        "authentication_method": "full",
    })


def worker(offset):
    with env.registry.cursor() as tcr:  # noqa: F821
        tenv = api.Environment(tcr, SUPERUSER_ID, {})
        for index in range(N_PER_THREAD):
            try:
                append(tenv, offset + index)
                tcr.commit()
                done[0] += 1
            except Exception as error:  # noqa: BLE001
                tcr.rollback()
                errors.append(f"{type(error).__name__}: {str(error).splitlines()[0][:160]}")


threads = [threading.Thread(target=worker, args=(offset,)) for offset in (0, 1000)]
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()
print(f"ESIGN concurrent 2 threads x {N_PER_THREAD}: appended={done[0]}, errors={len(errors)}")
for err in sorted(set(errors)):
    print(f"ESIGN error: {err} (x{errors.count(err)})")
outcome = env["ls.signature.log"].verify_chain(env.company)  # noqa: F821
print(f"ESIGN chain verification: passed={outcome['passed']}")
