# sidecar-charm-thruk

## Description

Thruk Master Charm. Multiple Nagios instances aggregator.

## Usage

    juju deploy nagios --config enable_livestatus=true
    juju deploy thruk-agent
    juju deploy thruk-master
    juju add-relation nagios:juju-info thruk-agent:general-info
    juju add-relation thruk-master:thruk-agent thruk-agent:thruk-agent

To access the Web UI visit the url:

    http://<thruk-master-ip>/thruk/

Login with user `thrukadmin`. Its password can be retrieved with

    juju run -u thruk-master/0 "sudo cat /var/lib/thruk/thrukadmin.passwd"

## Developing

Create and activate a virtualenv with the development requirements:

    virtualenv -p python3 venv
    source venv/bin/activate
    pip install -r requirements-dev.txt

## Testing

The Python operator framework includes a very nice harness for testing
operator behaviour without full deployment. Just `run_tests`:

    ./run_tests
