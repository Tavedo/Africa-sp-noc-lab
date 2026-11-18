"""
Africa SP NOC - L3VPN service & isolation proof.

Checks VRF route PRESENCE rather than pinging. Route presence is the pure
test of the route-target policy and is immune to the ping source-address
trap (a PE sources from its PE-CE link, which isn't advertised across the
VPN, so a correct VPN can still show 0% ping).

  SAME VPN  (VRF CUSTOMER on both PEs, RT 65100:1):
    PE2-DAKAR imports S.Africa 192.168.30.0/24 over VPNv4 (admin distance 200)
    PE3-JHB   imports Senegal  192.168.20.0/24 over VPNv4 (admin distance 200)

  ISOLATION (VRF NIGER-MPLS on PE1, RT 65100:3):
    PE1-LAGOS holds only its own 192.168.40.0/24 and must NOT see the
    CUSTOMER prefixes. A route here would mean a route-target leak, and
    this test turns RED the moment that happens.
"""
import re
from pyats import aetest

PES = ["SP-PE1-LAGOS", "SP-PE2-DAKAR", "SP-PE3-JHB"]
SENEGAL = "192.168.20.0/24"
SAFRICA = "192.168.30.0/24"
NIGER   = "192.168.40.0/24"


def imported_vpnv4(out, prefix):
    """True if <prefix> is a BGP route learned via iBGP/VPNv4 (admin distance 200)."""
    return re.search(r"B\s+" + re.escape(prefix) + r"\s+\[200/", out) is not None


def route_present(out, prefix):
    return re.search(re.escape(prefix), out) is not None


class CommonSetup(aetest.CommonSetup):
    @aetest.subsection
    def connect(self, testbed):
        for name in PES:
            testbed.devices[name].connect(log_stdout=False, learn_hostname=True)


class SameVPN_Import(aetest.Testcase):
    """Dakar + Johannesburg share VRF CUSTOMER: each must import the other
    site over the MPLS backbone (that's the two-site customer working)."""

    @aetest.test
    def dakar_imports_safrica(self, testbed):
        out = testbed.devices["SP-PE2-DAKAR"].execute("show ip route vrf CUSTOMER")
        if imported_vpnv4(out, SAFRICA):
            self.passed("PE2-DAKAR imports S.Africa via VPNv4 - RT 65100:1 working")
        else:
            self.failed("PE2-DAKAR missing S.Africa route - same-VPN import broken")

    @aetest.test
    def jhb_imports_senegal(self, testbed):
        out = testbed.devices["SP-PE3-JHB"].execute("show ip route vrf CUSTOMER")
        if imported_vpnv4(out, SENEGAL):
            self.passed("PE3-JHB imports Senegal via VPNv4 - RT 65100:1 working")
        else:
            self.failed("PE3-JHB missing Senegal route - same-VPN import broken")


class VPN_Isolation(aetest.Testcase):
    """Headline test: PE1-LAGOS (NIGER-MPLS, RT 65100:3) must not see CUSTOMER.
    Isolation here is the RT import/export policy, not a firewall - so this
    asserts the CUSTOMER prefixes are ABSENT."""

    @aetest.test
    def lagos_has_own_customer(self, testbed):
        out = testbed.devices["SP-PE1-LAGOS"].execute("show ip route vrf NIGER-MPLS")
        if route_present(out, NIGER):
            self.passed("PE1-LAGOS holds its own customer 192.168.40.0/24")
        else:
            self.failed("PE1-LAGOS missing its own customer route - VRF problem")

    @aetest.test
    def lagos_cannot_see_customer_vpn(self, testbed, steps):
        out = testbed.devices["SP-PE1-LAGOS"].execute("show ip route vrf NIGER-MPLS")
        for site, prefix in [("Senegal", SENEGAL), ("S.Africa", SAFRICA)]:
            with steps.start(f"NIGER-MPLS must NOT reach {site} {prefix}", continue_=True) as step:
                if route_present(out, prefix):
                    step.failed(f"LEAK: {prefix} present in NIGER-MPLS - RT isolation BROKEN")
                else:
                    step.passed(f"{prefix} correctly absent - isolation holds")


class CommonCleanup(aetest.CommonCleanup):
    @aetest.subsection
    def disconnect(self, testbed):
        for name in PES:
            d = testbed.devices[name]
            if d.is_connected():
                d.disconnect()
