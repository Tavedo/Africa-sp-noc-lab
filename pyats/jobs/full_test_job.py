"""pyATS job - runs the full Africa SP NOC validation suite.

    export PYATS_USERNAME=netauto
    export PYATS_PASSWORD='Cisco123!'
    export PYATS_ENABLE='Cisco123!'
    pyats run job jobs/full_test_job.py --testbed-file testbed/testbed.yaml
"""
import os
from pyats.easypy import run

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = os.path.normpath(os.path.join(HERE, "..", "tests"))


def main(runtime):
    # Control plane first - if the backbone is down, service failures are noise.
    run(testscript=os.path.join(TESTS, "test_control_plane.py"), runtime=runtime)
    # Then the L3VPN services + the isolation proof.
    run(testscript=os.path.join(TESTS, "test_vpn_services.py"), runtime=runtime)
