# NOC Scenario 03 — High Latency on Dakar Link

## 🎫 Incident Ticket

```
Ticket ID:     INC-2024-0134
Priority:      P3 - Medium
Category:      Performance - Latency
Reported By:   CE-SENEGAL Customer (phone call)
Time:          2024-05-10 09:30 UTC
Shift:         Day Shift

Description:
  CE-SENEGAL customer reports slow application performance since 08:00 UTC.
  Connectivity is not down — they can reach other sites.
  Round-trip time to CE-NIGERIA is reported as 280ms (normally ~40ms).
  No alarms on BGP sessions. No interface errors visible.
```

---

## 🔍 Diagnosis Steps

### Step 1 — Baseline Measurement (Confirm the Complaint)

From the SP side, test latency via VRF:

```
SP-PE2-DAKAR# ping vrf CUSTOMER 192.168.10.1 repeat 20 source 10.2.2.1
Type escape sequence to abort.
Sending 20, 100-byte ICMP Echos to 192.168.10.1, timeout is 2 seconds:
!!!!!!!!!!!!!!!!!!!!
Success rate is 100 percent (20/20), round-trip min/avg/max = 195/268/310 ms
```

**Finding:** Confirmed — latency is ~268ms average, far above the expected ~35ms baseline.

---

### Step 2 — Path Trace to Identify the Latency Source

```
SP-PE2-DAKAR# traceroute vrf CUSTOMER 192.168.10.1 source 10.2.2.1
  1  10.1.3.1 (P1-CORE)    2 msec   2 msec   1 msec
  2  10.1.5.2 (P2-CORE)  195 msec  198 msec  202 msec   ← SPIKE HERE
  3  10.1.2.1 (PE1-LAGOS) 268 msec  271 msec  269 msec
  4  192.168.10.1         269 msec  269 msec  270 msec
```

**Finding:** The latency spike occurs on the **P1-CORE → P2-CORE** link (10.1.5.x subnet).

---

### Step 3 — Check Interface Utilization

On **SP-P1-CORE**, inspect Gi0/2 (link to P2-CORE):

```
SP-P1-CORE# show interfaces GigabitEthernet0/2
GigabitEthernet0/2 is up, line protocol is up
  Description: TO_SP-P2-CORE
  Hardware is PQUAD_GIGE, address is fa16.3e4a.1234
  Internet address is 10.1.5.1/30
  MTU 1500 bytes, BW 1000000 Kbit/sec, DLY 10 usec,
     reliability 255/255, txload 240/255, rxload 198/255
  ...
  Input queue: 0/75/0/0 (size/max/drops/flushes); Total output drops: 14523
  Output queue: 74/1000 (size/max)
  5 minute input rate 940000000 bits/sec, ...
  5 minute output rate 940000000 bits/sec, ...
```

**Finding:** Interface is at **~94% utilization in both directions** with output queue drops (14,523 drops). This is causing queuing delay and packet drops.

---

### Step 4 — Traffic Analysis

Identify what's causing the congestion:

```
SP-P1-CORE# show ip cache flow
...
SrcIf      SrcIPaddress   DstIf      DstIPaddress   Pr SrcP DstP  Pkts
Gi0/0      10.2.2.x       Gi0/2      10.2.1.x       11 xxxx 5004  48273
Gi0/0      10.2.2.x       Gi0/2      10.2.1.x       11 xxxx 5004  51109
```

```
SP-P1-CORE# show interface GigabitEthernet0/2 | include rate
  5 minute input rate 940,000,000 bits/sec, 78000 packets/sec
  5 minute output rate 942,000,000 bits/sec, 79500 packets/sec
```

**Finding:** Heavy UDP traffic (port 5004) — likely a video stream or backup transfer consuming almost all available bandwidth on the P1-P2 core link.

---

### Step 5 — Identify Source and Escalate

The traffic originates from **CE-SENEGAL** (10.2.2.x) destined to CE-NIGERIA. Contact the customer:

- Customer confirms: their IT team started a **full DR data backup** at 08:00 UTC using UDP-based transfer (no QoS/rate limiting).
- The backup is saturating the 1G core link.

---

## ✅ Resolution Actions

**Immediate (L1 NOC):**
- Inform customer of the situation and request they pause or rate-limit the backup.
- Escalate to L2 for QoS policy review.

**Short-term (L2/L3):**
Apply a traffic shaping policy on CE-SENEGAL facing interface:

```
SP-PE2-DAKAR# conf t
SP-PE2-DAKAR(config)# policy-map BACKUP-LIMIT
SP-PE2-DAKAR(config-pmap)# class class-default
SP-PE2-DAKAR(config-pmap-c)# police rate 200000000 bps  ! Limit to 200Mbps
SP-PE2-DAKAR(config)# interface GigabitEthernet0/1
SP-PE2-DAKAR(config-if)# service-policy input BACKUP-LIMIT
```

**Long-term:**
- Customer SLA review for bulk transfer windows (off-peak hours)
- Core link capacity upgrade planning
- QoS DSCP marking and queuing on P-links

---

## 📊 Impact Summary

| Field               | Detail                                        |
|---------------------|-----------------------------------------------|
| **Affected Service**| MPLS L3VPN — all traffic transiting P1-P2    |
| **Cause**           | Bandwidth saturation from uncontrolled backup |
| **Duration**        | ~1.5 hours (08:00 – 09:30 UTC)               |
| **Resolution**      | Customer paused backup + interim rate-limit   |
| **Next Action**     | QoS policy + capacity planning review         |

---

## 🔑 Key Commands Reference

```bash
show interfaces [int] | include rate|drops|queue  # Utilization and drops
show ip cache flow                                 # NetFlow traffic summary (if enabled)
show policy-map interface [int]                    # QoS statistics
show mpls traffic-eng tunnels                      # If TE tunnels exist
traceroute vrf CUSTOMER [ip] source [ip]           # VRF traceroute
```
