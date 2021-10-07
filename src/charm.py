#!/usr/bin/env python3
# Copyright 2021 Facundo Ciccioli
# See LICENSE file for licensing details.

import logging
import yaml
import io
import hashlib
import contextlib

from ops.charm import CharmBase, RelationCreatedEvent, RelationChangedEvent, RelationJoinedEvent
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, ModelError

import templating

logger = logging.getLogger(__name__)

REQUIRED_PEER_KEYS = {
    "url",
    "nagios_context",
    "thruk_key",
}

THRUK_SERVICE = 'thruk'

def file_hash(container, filename):
    f = container.pull(filename, encoding=None)
    return hashlib.md5(f.read()).hexdigest()

class ThrukMasterCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.thruk_pebble_ready, self._on_thruk_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on['thruk-agent'].relation_changed, self._on_thruk_agent_relation_changed)
        self.framework.observe(self.on['thruk-agent'].relation_departed, self._on_thruk_agent_relation_departed)

    def _on_thruk_agent_relation_changed(self, event):
        missing_keys = REQUIRED_PEER_KEYS - event.relation.data[event.unit].keys()
        if missing_keys:
            self.unit.status = BlockedStatus(f"Waiting for thruk-agent relation to complete, missing keys: {', '.join(missing_keys)}")
            return

        self._render_config_files()
        self.unit.status = ActiveStatus()

    def _render_config_files(self):
        container = self.unit.get_container(THRUK_SERVICE)
        context = {
            'config': self.config,
            'peers': self._peers,
        }
        with self.restart_if_changed(container, '/etc/thruk/log4perl.conf', '/etc/thruk/thruk_local.conf'):
            container.push("/etc/thruk/log4perl.conf", templating.render(self.charm_dir, "log4perl.conf", context))
            container.push("/etc/thruk/thruk_local.conf", templating.render(self.charm_dir, "thruk_local.conf", context))

    @property
    def _peers(self):
        ret = []
        for relation in self.model.relations['thruk-agent']:
            for unit in relation.units:
                relation_data = relation.data[unit]
                ret.append({
                    'url': relation_data['url'],
                    'nagios_context': relation_data['nagios_context'],
                    'thruk_key': relation_data['thruk_key'],
                    'thruk_id': relation_data['thruk_id'],
                })
        return ret

    def _on_thruk_agent_relation_departed(self, event):
        self._render_config_files()

    def _on_config_changed(self, event):
        self._render_config_files()

    def _on_thruk_pebble_ready(self, event):
        # Get a reference the container attribute on the PebbleReadyEvent
        container = event.workload
        # Define an initial Pebble layer configuration
        pebble_layer = {
            "summary": "thruk layer",
            "description": "pebble config layer for thruk",
            "services": {
                THRUK_SERVICE: {
                    "override": "replace",
                    "summary": "thruk",
                    "command": "/usr/src/start.sh",
                    "startup": "enabled",
                }
            },
        }
        # Add intial Pebble config layer using the Pebble API
        container.add_layer("thruk", pebble_layer, combine=True)
        # Autostart any services that were defined with startup: enabled
        container.autostart()

        if not isinstance(self.unit.status, BlockedStatus):
            self.unit.status = ActiveStatus()

    @contextlib.contextmanager
    def restart_if_changed(self, container, *filenames):
        pre_hashes = [file_hash(container, f) for f in filenames]
        yield
        post_hashes = [file_hash(container, f) for f in filenames]

        try:
            service = container.get_service(THRUK_SERVICE)
        except ModelError:
            # NOTE: Most likely the PebbleReadyEvent didn't fire yet, so there's no service to restart.
            return

        if any([pre != post for pre, post in zip(pre_hashes, post_hashes)]) and service.is_running():
            self.unit.status = MaintenanceStatus(f'Restarting {THRUK_SERVICE}')

            container.stop(THRUK_SERVICE)
            container.start(THRUK_SERVICE)

            self.unit.status = ActiveStatus()


if __name__ == "__main__":
    main(ThrukMasterCharm)
