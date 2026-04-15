# NOC Scenario 02 — MPLS LSP Black-Holing

## 🎫 Incident Ticket

```
Ticket ID:     INC-2024-0089
Priority:      P1 - Critical
Category:      MPLS / Data Plane
Reported By:   Multiple customers + Auto-alert
Time:          2024-04-02 14:15 UTC
Shift:         Day Shift

Description:
  Multiple customer sites (Senegal and South Africa) cannot reach each other.
  Traffic from CE-SENEGAL to CE-SOUTHAFRICA is being dropped silently (black-hole).
  BGP sessions are UP on all PE routers. Routes appear in routing tables.
  No ICMP unreachables received by customers — packets are disappearing.
```

---

## 🔍 Diagnosis Steps

### Step 1 — Verify BGP Control Plane (Appears Healthy)

```
SP-PE2-DAKAR# show bgp vpnv4 unicast vrf CUSTOMER summary
Neighbor        V     AS  MsgRcvd MsgSent  TblVer InQ OutQ Up/Down  State/PfxRcd
10.2.2.2        4  65002      245     241       8   0    0 02:04:22  1

SP-PE2-DAKAR# show ip route vrf CUSTOMER
B  192.168.30.0/24 [200/0] via 10.0.0.3, 02:04:00
```

**Finding:** BGP routes look correct. Routes ARE present. Control plane is fine.

---

### Step 2 — Test Data Plane (Reproduce the Black-Hole)

```
CE-SENEGAL# ping 192.168.30.1 repeat 100
!!!!!!!!!!!!!!!!!!!.......................
Success rate is 20 percent (20/100) — intermittent drops
```

```
SP-PE2-DAKAR# traceroute vrf CUSTOMER 192.168.30.1 source 10.2.2.1
 1  10.1.3.1 (SP-P1-CORE)    1 msec
 2  *  *  *
 3  *  *  *
```

**Finding:** Traceroute stops at P1-CORE. Traffic enters MPLS but doesn't exit correctly.

---

### Step 3 — Check MPLS Forwarding Tables

On **SP-P1-CORE**:

```
SP-P1-CORE# show mpls forwarding-table
Local  Outgoing    Prefix              Bytes Label   Outgoing   Next Hop
Label  Label or VC or Tunnel Id        Switched      interface
16     Pop Label   10.0.0.2/32         0             Gi0/1      10.1.3.2
17     18          10.0.0.3/32         0             Gi0/2      10.1.5.2   ← should forward to P2
18     Pop Label   10.0.0.4/32         0             (local)
...
```

```
SP-P1-CORE# show mpls ldp neighbor
    Peer LDP Ident: 10.0.0.5:0; Local LDP Ident 10.0.0.4:0
    TCP connection: 10.0.0.5.646 - 10.0.0.4.40212
    State: Oper; Msgs sent/rcvd: 234/229; Downstream
    Up time: 02:05:44
```

LDP is up. But check label bindings more carefully:

```
SP-P1-CORE# show mpls ldp bindings 10.0.0.3 32
  lib entry: 10.0.0.3/32, rev 20
    local binding:  label: 17
    remote binding: lsr: 10.0.0.5:0, label: imp-null  ← PROBLEM!
```

**Finding:** P2-CORE is advertising **implicit-null** (PHP) for PE3-JHB's loopback — but P1 still has a forwarding entry with label 18. There is a **label mismatch** after a recent LDP session reset.

---

### Step 4 — Identify Root Cause

Check P2-CORE:

```
SP-P2-CORE# show mpls ldp bindings 10.0.0.3 32
  lib entry: 10.0.0.3/32, rev 8
    local binding:  label: imp-null    ← P2 is directly connected to PE3, so PHP
    remote binding: lsr: 10.0.0.4:0, label: 17
```

```
SP-P2-CORE# show interfaces GigabitEthernet0/1
GigabitEthernet0/1 is up, line protocol is up
  Description: TO_SP-PE3-JHB
  ...
  Last clearing of "show interface" counters: 00:00:45
```

**Root Cause:** Interface counters were recently cleared (maintenance task). After a brief OSPF/LDP reconvergence caused by a `shutdown/no shutdown` on this interface, LDP re-advertised label bindings, but the MPLS forwarding table on P1 still had a **stale label 18** instead of the new **imp-null** binding. The data plane was forwarding with wrong labels — packets arriving at PE3-JHB with an unexpected label were dropped.

---

## ✅ Resolution

**Option A (Soft):** Force LDP to re-sync by clearing LDP neighbor:

```
SP-P1-CORE# clear mpls ldp neighbor 10.0.0.5
```

After ~30 seconds, LDP re-establishes and forwarding table is updated:

```
SP-P1-CORE# show mpls forwarding-table 10.0.0.3 32 detail
Local      Outgoing   Prefix            Bytes Label   Outgoing     Next Hop
Label      Label      or Tunnel Id      Switched      interface
17         No Label   10.0.0.3/32       0             Gi0/2        10.1.5.2
```

**Verify end-to-end:**

```
CE-SENEGAL# ping 192.168.30.1 repeat 100
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
Success rate is 100 percent (100/100)
```

---

## 📊 Impact Summary

| Field               | Detail                                      |
|---------------------|---------------------------------------------|
| **Affected Service**| MPLS L3VPN — all sites via P1-CORE path    |
| **Duration**        | ~20 minutes                                 |
| **Root Cause**      | Stale MPLS forwarding table after LDP churn |
| **Trigger**         | Interface counter clear on P2-CORE          |
| **Resolution**      | LDP neighbor reset on P1-CORE               |
| **Lesson Learned**  | Avoid maintenance on core during business hours; use LDP graceful-restart |

---

## 🔑 Key Commands Reference

```bash
show mpls forwarding-table                    # MPLS LFIB
show mpls ldp neighbor                        # LDP sessions
show mpls ldp bindings [prefix] [mask]        # Label bindings (LIB)
show mpls ldp bindings detail                 # Full label distribution detail
traceroute mpls ipv4 10.0.0.3/32             # MPLS LSP traceroute
ping mpls ipv4 10.0.0.3/32                   # MPLS LSP ping
clear mpls ldp neighbor [ip]                  # Reset LDP (use with caution!)
```
