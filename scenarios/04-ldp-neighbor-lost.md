# NOC Scenario 04 — LDP Neighbor Lost on Core Link

## 🎫 Incident Ticket

```
Ticket ID:     INC-2024-0201
Priority:      P2 - High
Category:      MPLS / Protocol
Reported By:   NOC Monitoring System (Auto-Alert)
Time:          2024-06-18 03:15 UTC
Shift:         Night Shift

Description:
  Auto-alert: LDP neighbor 10.0.0.5 (P2-CORE) lost on SP-P1-CORE.
  MPLS LSPs to PE3-JHB (South Africa) may be affected.
  CE-SOUTHAFRICA connectivity impact possible.
```

---

## 🔍 Diagnosis Steps

### Step 1 — Confirm LDP Session Status

```
SP-P1-CORE# show mpls ldp neighbor
    Peer LDP Ident: 10.0.0.2:0; Local LDP Ident 10.0.0.4:0
    TCP connection: 10.0.0.2.646 - 10.0.0.4.52341
    State: Oper; Msgs sent/rcvd: 1200/1198; Downstream
    Up time: 04:22:11
    LDP discovery sources:
      GigabitEthernet0/1, Src IP addr: 10.1.3.2

! Note: 10.0.0.5 (P2-CORE) is MISSING from the list
```

**Finding:** LDP session with P2-CORE (10.0.0.5) is gone.

---

### Step 2 — Check OSPF for Underlying Connectivity

```
SP-P1-CORE# show ip ospf neighbor
Neighbor ID     Pri  State     Dead Time  Address     Interface
10.0.0.1          1  FULL/  -  00:00:31   10.1.1.2    Gi0/0
10.0.0.2          1  FULL/  -  00:00:38   10.1.3.1    Gi0/1
10.0.0.6          1  FULL/  -  00:00:29   10.1.6.2    Gi0/3
! 10.0.0.5 (P2-CORE) is also MISSING from OSPF!
```

```
SP-P1-CORE# show interfaces GigabitEthernet0/2
GigabitEthernet0/2 is up, line protocol is DOWN
  Description: TO_SP-P2-CORE
  ...
  Last input 00:04:22, Last output 00:04:21
  Last clearing of "show interface" counters never
```

**Finding:** The physical interface to P2-CORE is **line protocol DOWN** — carrier lost. Both OSPF and LDP dropped because the link is physically down.

---

### Step 3 — Check Logs for Interface Events

```
SP-P1-CORE# show logging | include Gi0/2|P2-CORE
Jun 18 03:11:04: %LINEPROTO-5-UPDOWN: Line protocol on Interface GigabitEthernet0/2,
  changed state to down
Jun 18 03:11:04: %OSPF-5-ADJCHG: Process 1, Nbr 10.0.0.5 on GigabitEthernet0/2
  from FULL to DOWN, Neighbor Down: Interface down or detached
Jun 18 03:11:06: %LDP-5-NBRCHG: LDP Neighbor 10.0.0.5:0 (2), is DOWN
  Dead: Link down
```

**Finding:** Clear sequence — interface went down at 03:11, triggering OSPF and LDP loss.

---

### Step 4 — Assess Traffic Impact (Has OSPF Converged Around?)

```
SP-P1-CORE# show ip route 10.0.0.3
Routing entry for 10.0.0.3/32
  Known via "ospf 1", distance 110, metric 3
  Last update from 10.1.5.2 on GigabitEthernet0/2
  
! Wait... Gi0/2 is down, but route is still pointing there?
! Check again after OSPF convergence:

SP-P1-CORE# show ip route 10.0.0.3
% Network not in table
```

**Finding:** After OSPF reconverge, PE3-JHB (10.0.0.3) is unreachable from P1-CORE because P2-CORE was the only path — **there is no redundant path** from P1 to PE3-JHB. All South Africa traffic is black-holed.

---

### Step 5 — Check P2-CORE Side

```
SP-P2-CORE# show interfaces GigabitEthernet0/2
GigabitEthernet0/2 is up, line protocol is DOWN
  Description: TO_SP-P1-CORE
  ...
```

Both ends show line protocol down. This is a **physical link failure** between P1 and P2.

---

## ✅ Resolution

**Immediate (L1 NOC):**
1. Open physical alarm investigation — check if this is a fiber cut, transceiver failure, or cable issue.
2. Check physical layer: SFP status, fiber patch, cross-connect.
3. Escalate to on-site tech or NOC L2.

**If Remote Hands Available:**

```
! Check SFP on both ends:
SP-P1-CORE# show interfaces GigabitEthernet0/2 transceiver
  GigabitEthernet0/2
    Transceiver is present
    Transceiver type: 1000BASE-LX/LH
    Rx Power (dBm): -38.2  ← Below minimum threshold (~-23dBm)!
```

**Finding:** Fiber receive power is too low — likely a fiber break or dirty connector.

**Resolution:** Physical cleaning of fiber connectors or fiber patch replacement by on-site technician restored the link.

```
Jun 18 04:45:30: %LINEPROTO-5-UPDOWN: Line protocol on Interface GigabitEthernet0/2,
  changed state to up
Jun 18 04:45:32: %OSPF-5-ADJCHG: Process 1, Nbr 10.0.0.5 on GigabitEthernet0/2
  from LOADING to FULL
Jun 18 04:45:34: %LDP-5-NBRCHG: LDP Neighbor 10.0.0.5:0 (2), is UP
```

**Verify South Africa reachability:**

```
SP-PE2-DAKAR# ping vrf CUSTOMER 192.168.30.1 source 10.2.2.1
!!!!!
Success rate is 100 percent (5/5), round-trip min/avg/max = 42/45/48 ms
```

---

## 📊 Impact Summary

| Field               | Detail                                      |
|---------------------|---------------------------------------------|
| **Affected Sites**  | CE-SOUTHAFRICA (full loss), CE-SENEGAL to SA |
| **Duration**        | 1h 34min (03:11 – 04:45 UTC)               |
| **Root Cause**      | Fiber physical failure P1↔P2 core link      |
| **Resolution**      | Fiber cleaned/replaced by on-site tech       |
| **Gap Identified**  | No redundant P1→PE3 path (single point of failure) |
| **Next Action**     | Network design review for path redundancy   |

---

## 🔑 Key Commands Reference

```bash
show mpls ldp neighbor                         # LDP adjacencies
show ip ospf neighbor                          # OSPF adjacencies
show interfaces [int]                          # Physical/protocol state
show interfaces [int] transceiver              # SFP optical levels
show logging | include LINEPROTO|OSPF|LDP     # Event correlation in logs
show ip route [ip]                             # Check routing after convergence
```
