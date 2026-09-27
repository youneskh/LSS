# Odoo 19 Community image of the Life Sciences Suite.
#
# The base image is pinned (audit 2026-09-25, F-05 / F-21). 19.0-20260723 is
# the build the project container was running when it was audited. For a fully
# reproducible build, pin it by digest as well: run
#     docker image inspect odoo:19.0-20260723 --format "{{index .RepoDigests 0}}"
# and set ODOO_IMAGE (docker-compose.yml, build args) to the returned
# "odoo@sha256:..." value.
#
# Odoo core files are NOT modified at build time: the former patch-delivery.sh
# replaced view identifiers that exist unchanged in Odoo 19.0 and made the
# standard "delivery" module impossible to install or upgrade (F-05).
ARG ODOO_IMAGE=odoo:19.0-20260723
FROM ${ODOO_IMAGE}

COPY requirements.txt /tmp/requirements.txt
USER root
RUN pip install --break-system-packages --no-cache-dir -r /tmp/requirements.txt
USER odoo
