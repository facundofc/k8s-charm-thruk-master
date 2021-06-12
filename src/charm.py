#!/usr/bin/env python3
# Copyright 2021 Facundo Ciccioli
# See LICENSE file for licensing details.

import logging

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus

logger = logging.getLogger(__name__)

REQUIRED_THRUK_AGENT_FIELDS = {
    "url",
    "nagios_context",
    "thruk_key",
    "thruk_id",
}

class SidecarCharmThrukCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.thruk_pebble_ready, self._on_thruk_pebble_ready)
        self.framework.observe(self.on['thruk-agent'].relation_changed, self._on_thruk_agent_relation_changed)

    def _on_thruk_pebble_ready(self, event):
        # Get a reference the container attribute on the PebbleReadyEvent
        container = event.workload
        # Define an initial Pebble layer configuration
        pebble_layer = {
            "summary": "thruk layer",
            "description": "pebble config layer for thruk",
            "services": {
                "thruk": {
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
        # Learn more about statuses in the SDK docs:
        # https://juju.is/docs/sdk/constructs#heading--statuses
        self.unit.status = ActiveStatus()

    def _on_thruk_agent_relation_changed(self, event):
        agent_fields = {
            field: event.relation.data[event.unit].get(field)
            for field in REQUIRED_THRUK_AGENT_FIELDS
        }

        # if any required fields are missing, warn the user and return
        missing_fields = [
            field
            for field in REQUIRED_THRUK_AGENT_FIELDS
            if agent_fields.get(field) is None
        ]
        if len(missing_fields) > 0:
            logger.error(
                "Missing required data fields for related agent "
                "relation: {}".format(missing_fields)
            )
            return
        logger.error("I'd be writing the config file now...")
        for f in REQUIRED_THRUK_AGENT_FIELDS:
            logger.error(f"{f} = {event.relation.data[event.unit][f]}")

    def _update_thruk_local_conf(self, peers):
        pass



if __name__ == "__main__":
    main(SidecarCharmThrukCharm)
