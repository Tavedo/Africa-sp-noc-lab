"""Africa SP NOC - control-plane health: OSPF FULL, LDP Oper, BGP VPNv4 Established.

Checks the foundation first: if OSPF is down nothing above it works, so the
testcases run IGP -> MPLS label distribution -> BGP VPNv4 in that order.
"""
import re
from pyats import aetest

CORE = ["SP-PE1-LAGOS", "SP-PE2-DAKAR", "SP-PE3-JHB",
        "SP-P1-CORE", "SP-P2-CORE", "SP-RR1"]


class CommonSetup(aetest.CommonSetup):
    @aetest.subsection
    def connect(self, testbed):
        for name in CORE:
            testbed.devices[name].connect(log_stdout=False, learn_hostname=True)


class OSPF_Adjacencies(aetest.Testcase):
    """Every OSPF neighbor on every core device must be FULL."""
    @aetest.test
    def all_full(self, testbed, steps):
        for name in CORE:
            dev = testbed.devices[name]
            with steps.start(f"{name} OSPF FULL", continue_=True) as step:
                out = dev.execute("show ip ospf neighbor")
                full = re.findall(r"\bFULL\b", out)
                bad = re.findall(r"\b(INIT|EXSTART|EXCHANGE|LOADING|2WAY|DOWN|ATTEMPT)\b", out)
                if not full:
                    step.failed(f"{name}: no FULL neighbors")
                elif bad:
                    step.failed(f"{name}: non-FULL states {set(bad)}")
                else:
                    step.passed(f"{name}: {len(full)} FULL")


class LDP_Sessions(aetest.Testcase):
    """LDP neighbors must be operational - no MPLS transport without them."""
    @aetest.test
    def all_oper(self, testbed, steps):
        for name in CORE:
            dev = testbed.devices[name]
            with steps.start(f"{name} LDP Oper", continue_=True) as step:
                out = dev.execute("show mpls ldp neighbor")
                opers = out.count("State: Oper")
                peers = out.count("Peer LDP Ident")
                if peers == 0:
                    step.failed(f"{name}: no LDP peers")
                elif opers < peers:
                    step.failed(f"{name}: {opers}/{peers} Oper")
                else:
                    step.passed(f"{name}: {opers} LDP Oper")


class BGP_VPNv4(aetest.Testcase):
    """All BGP/VPNv4 neighbors must be Established (P routers correctly have 0)."""
    @aetest.test
    def all_established(self, testbed, steps):
        for name in CORE:
            dev = testbed.devices[name]
            with steps.start(f"{name} BGP VPNv4", continue_=True) as step:
                out = dev.execute("show bgp vpnv4 unicast all summary")
                down = re.findall(r"^\S+\s+\d+\s+\d+.*\b(Idle|Active|Connect|OpenSent|OpenConfirm)\b", out, re.M)
                est = re.findall(r"^\S+\s+4\s+\d+.*\s+\d+\s*$", out, re.M)
                if down:
                    step.failed(f"{name}: not established {down}")
                elif not est and "Neighbor" in out:
                    step.passx(f"{name}: no VPNv4 neighbors (P router)")
                else:
                    step.passed(f"{name}: {len(est)} VPNv4 established")


class CommonCleanup(aetest.CommonCleanup):
    @aetest.subsection
    def disconnect(self, testbed):
        for name in CORE:
            d = testbed.devices[name]
            if d.is_connected():
                d.disconnect()
