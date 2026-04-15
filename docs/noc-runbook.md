# NOC Runbook — Africa SP Network v2

> Quick reference for NOC L1 engineers. Use during incident response for
> common tasks and verification commands. Updated for 15-device lab.

---

## 1. Initial Triage Checklist

When an alert fires or a customer call arrives, work through this order:

```
[ ] 1. Check monitoring dashboard — identify the alert type
[ ] 2. Verify the alarm is real (not a false positive)
[ ] 3. Identify affected customer(s) and service(s)
[ ] 4. Check if there are related alarms (correlated events)
[ ] 5. Log into the relevant PE/P router
[ ] 6. Confirm connectivity or service impact
[ ] 7. Open a ticket if not auto-created
[ ] 8. Begin diagnosis per the relevant runbook section
[ ] 9. Escalate to L2 if not resolved within SLA time
[ ] 10. Update the ticket with each action taken
```

---

## 2. Connectivity Verification — Run in This Order

IMPORTANT: each layer depends on the one below. Never check BGP before OSPF.

```
# Step 1 — OSPF backbone (foundation of everything)
show ip ospf neighbor           # all SP routers — must show FULL/-
show ip ospf interface brief    # Loopback0 MUST appear in this list

# Step 2 — MPLS LDP
show mpls ldp neighbor          # all Oper state
show mpls forwarding-table      # labels for all 10.0.0.x/32 loopbacks

# Step 3 — BGP control plane
show bgp vpnv4 unicast all summary          # on RR1 — PE1/PE2/PE3 all Estab
show bgp ipv4 unicast summary               # on PE1 — upstream Estab

# Step 4 — VRF routing tables
show ip route vrf CUSTOMER                  # on PE2 or PE3
show ip route vrf NIGERIA-ISP               # on PE1
show ip route vrf NIGER-MPLS                # on PE1
show ip route vrf DIA-CUSTOMER              # on PE1 — S* 0.0.0.0/0 present?

# Step 5 — End-to-end service tests
ping vrf CUSTOMER [dst] source [src]
traceroute vrf CUSTOMER [dst] source [src]
```

---

## 3. BGP Troubleshooting Decision Tree

```
BGP Session Down?
    │
    ├─► Check OSPF first: show ip ospf neighbor
    │       └─► If neighbors missing: Loopback0 not in OSPF
    │           Fix: interface Loopback0 / ip ospf 1 area 0
    │
    ├─► Check LDP: show mpls ldp neighbor
    │       └─► If empty: OSPF loopback issue (fix above first)
    │
    ├─► Check interface state: show interfaces [int]
    │       └─► If DOWN: physical issue → check fiber/transceiver
    │
    ├─► Check IP reachability: ping [neighbor-ip] source [loopback-ip]
    │       └─► If fails: check OSPF routing table
    │
    ├─► Check BGP logs: show logging | include BGP|[neighbor-ip]
    │       └─► Hold timer: CE not sending keepalives → check CE config
    │       └─► Active state: TCP to loopback failing
    │
    └─► Verify BGP config: show run | section router bgp
            └─► IOSv note: no peer-group in address-family
                Use individual neighbor IPs for activate/route-reflector-client
```

---

## 4. MPLS Troubleshooting Decision Tree

```
MPLS / VPN Traffic Not Working?
    │
    ├─► Check BGP routes exist: show ip route vrf CUSTOMER
    │       └─► Routes missing: BGP issue (see Section 3)
    │
    ├─► Check MPLS labels: show mpls forwarding-table
    │       └─► Stale/No Label: clear mpls ldp neighbor [ip]
    │           Also check: show bgp vpnv4 unicast all labels
    │           nolabel = add Loopback0 to OSPF then clear ip bgp * soft
    │
    ├─► Check LDP sessions: show mpls ldp neighbor
    │       └─► LDP down: check OSPF loopback reachability first
    │
    ├─► Test LSP: ping mpls ipv4 [loopback/32]
    │       └─► LSP ping fails but IP ping works: MPLS data plane issue
    │
    ├─► VRF-aware traceroute: traceroute vrf CUSTOMER [dst]
    │       └─► Find which hop drops traffic
    │
    └─► Always source CE pings from Loopback0 (/24)
            NOT from PE-CE link (/30) — /30 not in BGP
```

---

## 5. DIA Troubleshooting

```
CE-DIA cannot reach internet?
    │
    ├─► Check CE: show ip route
    │       └─► B* 0.0.0.0/0 present? If not: BGP session issue
    │
    ├─► Check PE1: show ip route vrf DIA-CUSTOMER
    │       └─► S* 0.0.0.0/0 present? If not:
    │           Run: ip route vrf DIA-CUSTOMER 0.0.0.0 0.0.0.0 203.0.113.1 global
    │           NOTE: next-hop IP must come BEFORE the 'global' keyword
    │
    ├─► Check PE1 G0/6: show interfaces GigabitEthernet0/6
    │       └─► Must be up/up. If down/down: link not drawn in CML UI
    │
    └─► Check upstream: ping 203.0.113.1 from PE1
```

---

## 6. SD-WAN / DMVPN Troubleshooting

```
SDWAN spoke-to-spoke not working?
    │
    ├─► Check hub: show dmvpn
    │       └─► Spokes must show Up state
    │
    ├─► Check NHRP: show ip nhrp (on hub)
    │       └─► Spoke tunnel IPs and NBMA addresses registered?
    │
    ├─► Check underlay: ping 100.64.x.x from spoke
    │       └─► Must reach UPSTREAM-ISP to register with hub
    │
    ├─► Check tunnel config:
    │       tunnel key must be 100 on all nodes
    │       ip nhrp network-id must be 1 on all nodes
    │       ip ospf network broadcast on all tunnel interfaces
    │
    └─► Check OSPF process 2: show ip ospf neighbor (on hub)
            └─► Both spokes must be FULL
```

---

## 7. Interface / Physical Layer Checks

```
show interfaces [int]
show interfaces [int] transceiver        # Optical levels (SFP)

# Interpret transceiver output:
# Rx Power > -20 dBm  = Good
# Rx Power -20 to -28 = Warning
# Rx Power < -28 dBm  = Critical (clean/replace fiber)

show interfaces [int] counters errors
show interfaces [int] | include error|drop|reset
show logging | include [interface-name]|LINEPROTO
```

---

## 8. Ticket Documentation Template

```
TICKET: INC-[YEAR]-[NNNN]
Priority: P[1-4]
Time Opened: [UTC]
Time Resolved: [UTC]

CUSTOMER: [Name / ID]
SERVICE: [MPLS L3VPN / IP Transit / DIA / SD-WAN]
SITES AFFECTED: [List of CE sites]

DESCRIPTION:
[What the customer reported]

INVESTIGATION:
[Step by step: command run and output summary]

ROOT CAUSE:
[Single clear sentence]

RESOLUTION:
[Exactly what was done to fix it]

IMPACT:
Duration: [X minutes/hours]
SLA breach: [Yes/No]

NEXT ACTIONS:
[Change request, capacity review, etc.]

NOC ENGINEER: [Your name]
```

---

## 9. Escalation Matrix

| Priority | Response Time | Resolution Target | Escalate To             |
|----------|---------------|-------------------|-------------------------|
| P1       | 15 min        | 2 hours           | L2 + Manager immediately|
| P2       | 30 min        | 4 hours           | L2 within 1 hour        |
| P3       | 2 hours       | 8 hours           | L2 if no progress in 2h |
| P4       | Next business | 24 hours          | L2 if customer escalates|

---

## 10. Key IP Reference — All 15 Devices

| Device          | Loopback / Tunnel IP | Service             |
|-----------------|----------------------|---------------------|
| SP-PE1-LAGOS    | 10.0.0.1/32          | PE — Nigeria hub    |
| SP-PE2-DAKAR    | 10.0.0.2/32          | PE — Senegal        |
| SP-PE3-JHB      | 10.0.0.3/32          | PE — South Africa   |
| SP-P1-CORE      | 10.0.0.4/32          | P-core LSR          |
| SP-P2-CORE      | 10.0.0.5/32          | P-core LSR          |
| SP-RR1          | 10.0.0.6/32          | iBGP RR             |
| UPSTREAM-ISP    | 10.0.0.10/32         | Internet upstream   |
| CE-NIGERIA      | 192.168.10.1         | VRF NIGERIA-ISP     |
| CE-SENEGAL      | 192.168.20.1         | VRF CUSTOMER        |
| SE-SOUTHAFRICA  | 192.168.30.1         | VRF CUSTOMER        |
| CE-NIGER        | 192.168.40.1         | VRF NIGER-MPLS      |
| CE-DIA          | 192.168.50.1         | VRF DIA-CUSTOMER    |
| SDWAN-HUB       | 172.16.0.1 / Tu0: 10.100.0.1 | DMVPN hub  |
| SDWAN-SPOKE1    | 172.16.1.1 / Tu0: 10.100.0.2 | DMVPN spoke|
| SDWAN-SPOKE2    | 172.16.2.1 / Tu0: 10.100.0.3 | DMVPN spoke|

## 11. Connectivity Quick Reference

| Source         | Destination    | Expected | Why                          |
|----------------|----------------|----------|------------------------------|
| CE-SENEGAL     | SE-SOUTHAFRICA | YES      | Same VRF CUSTOMER RT:1       |
| CE-SENEGAL     | CE-NIGERIA     | NO       | Different VRF RT:1 vs RT:2   |
| CE-SENEGAL     | CE-NIGER       | NO       | Different VRF RT:1 vs RT:3   |
| CE-DIA         | 1.1.1.1        | YES      | DIA default route leak       |
| CE-DIA         | CE-SENEGAL     | NO       | DIA has no VPN routes        |
| SPOKE1         | SPOKE2         | YES      | DMVPN Phase 2 direct tunnel  |
| Any CE         | 10.0.0.x       | NO       | SP backbone in global table  |
