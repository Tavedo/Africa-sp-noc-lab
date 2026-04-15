# NOC Scenario 01 — BGP Session Down: Nigeria Customer

## Incident Ticket

```
Ticket ID:     INC-2024-0042
Priority:      P2 - High
Category:      Connectivity - BGP
Reported By:   CE-NIGERIA Customer (NOC Auto-Alert)
Time:          2024-03-15 02:47 UTC
Shift:         Night Shift

Description:
  Customer CE-NIGERIA reports loss of connectivity.
  BGP alarm triggered on monitoring system for PE1-LAGOS to CE-NIGERIA session.
  Customer site 192.168.10.0/24 unreachable.
  CE-NIGERIA is in VRF NIGERIA-ISP on PE1-LAGOS — isolated enterprise service.
```

---

## Diagnosis Steps (L1 NOC Methodology)

### Step 1 — Confirm the Alarm

On **SP-PE1-LAGOS**, verify BGP neighbor state in VRF NIGERIA-ISP:

```
SP-PE1-LAGOS# show bgp vpnv4 unicast vrf NIGERIA-ISP summary

Neighbor        V           AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
10.2.1.2        4        65001       0       0        0    0    0 00:03:21 Idle
```

**Finding:** BGP session to CE-NIGERIA (10.2.1.2) is in Idle state — confirmed DOWN.

---

### Step 2 — Check Physical Layer

```
SP-PE1-LAGOS# show interfaces GigabitEthernet0/1
GigabitEthernet0/1 is up, line protocol is up
  Description: TO_CE-NIGERIA (VRF NIGERIA-ISP)
  ...
  Input errors: 0, Output errors: 0
```

**Finding:** Interface G0/1 is physically UP. Problem is at L3 or BGP layer.

---

### Step 3 — Verify L3 Reachability to CE

```
SP-PE1-LAGOS# ping vrf NIGERIA-ISP 10.2.1.2 source 10.2.1.1
!!!!!
Success rate is 100 percent (5/5)
```

**Finding:** L3 reachability is OK. The issue is BGP-specific.

---

### Step 4 — Check BGP Logs

```
SP-PE1-LAGOS# show logging | include BGP|10.2.1.2
Mar 15 02:44:11: %BGP-5-ADJCHANGE: neighbor 10.2.1.2 vpn vrf NIGERIA-ISP Down
  BGP Notification sent: hold time expired
```

**Finding:** Session torn down due to Hold Timer Expiry — CE stopped sending keepalives.

---

### Step 5 — Identify Root Cause on CE Side

```
CE-NIGERIA# show bgp ipv4 unicast summary
% BGP not active

CE-NIGERIA# show run | section router bgp
(empty — BGP process was removed)
```

**Root Cause:** BGP configuration was accidentally removed from CE-NIGERIA.

---

## Resolution

Restore BGP configuration on CE-NIGERIA:

```
CE-NIGERIA(config)# router bgp 65001
CE-NIGERIA(config-router)# bgp router-id 192.168.10.1
CE-NIGERIA(config-router)# bgp log-neighbor-changes
CE-NIGERIA(config-router)# neighbor 10.2.1.1 remote-as 65100
CE-NIGERIA(config-router)# neighbor 10.2.1.1 description eBGP-TO-PE1-LAGOS
CE-NIGERIA(config-router)# address-family ipv4 unicast
CE-NIGERIA(config-router-af)#  neighbor 10.2.1.1 activate
CE-NIGERIA(config-router-af)#  network 192.168.10.0 mask 255.255.255.0
CE-NIGERIA(config-router-af)# end
CE-NIGERIA# write memory
```

Verify recovery:

```
SP-PE1-LAGOS# show bgp vpnv4 unicast vrf NIGERIA-ISP summary
Neighbor        V     AS  MsgRcvd MsgSent  State/PfxRcd
10.2.1.2        4  65001        5       5  1

SP-PE1-LAGOS# show ip route vrf NIGERIA-ISP
B  192.168.10.0/24 [20/0] via 10.2.1.2
```

---

## Impact Summary

| Field           | Detail                              |
|-----------------|-------------------------------------|
| Affected Service| MPLS L3VPN — VRF NIGERIA-ISP        |
| Affected Site   | CE-NIGERIA (192.168.10.0/24)        |
| Duration        | ~4 minutes                          |
| Root Cause      | BGP config removed from CE device   |
| Resolution      | BGP config restored on CE-NIGERIA   |
| Note            | NIGERIA-ISP is an isolated VRF — no cross-customer impact |

---

## Key Commands Reference

```
show bgp vpnv4 unicast vrf NIGERIA-ISP summary   # BGP in VRF NIGERIA-ISP
show ip route vrf NIGERIA-ISP                     # Routing table in VRF
show logging | include BGP                        # BGP events in syslog
ping vrf NIGERIA-ISP 10.2.1.2 source 10.2.1.1   # L3 reachability test
```
