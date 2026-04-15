# NOC Scenario 05 — VRF Route Leaking: Wrong Customer Prefix

## 🎫 Incident Ticket

```
Ticket ID:     INC-2024-0287
Priority:      P1 - Critical (Security Concern)
Category:      Routing / Security
Reported By:   CE-SENEGAL Customer
Time:          2024-07-22 11:05 UTC
Shift:         Day Shift

Description:
  CE-SENEGAL reports receiving unexpected traffic from an unknown network
  192.168.10.x — they should ONLY have connectivity to 192.168.20.x (their own)
  and 192.168.30.x (South Africa site).

  Customer is concerned about potential traffic from unauthorized third parties.
  This is a SECURITY-SENSITIVE ticket — immediate investigation required.

  UPDATE: CE-SOUTHAFRICA also reports they can now ping 192.168.20.x
  which should be the Senegal network — this is UNEXPECTED per their SLA.
```

---

## 🔍 Diagnosis Steps

### Step 1 — Verify Current VRF Routing Tables

```
SP-PE2-DAKAR# show ip route vrf CUSTOMER
...
B  192.168.10.0/24 [200/0] via 10.0.0.1, 00:45:11    ← CE-NIGERIA route
B  192.168.20.0/24 [20/0]  via 10.2.2.2, 00:45:08    ← Local CE-SENEGAL
B  192.168.30.0/24 [200/0] via 10.0.0.3, 00:45:09    ← CE-SOUTHAFRICA route
```

**Finding:** CE-NIGERIA prefix (192.168.10.0/24) IS present in VRF CUSTOMER on PE2. This is CORRECT — all three CE sites are in the same VRF `CUSTOMER` and share the same RT. However, customer says they should NOT see CE-NIGERIA traffic.

---

### Step 2 — Check the VRF Definition (RT Configuration)

On PE1-LAGOS, check the VRF:

```
SP-PE1-LAGOS# show vrf detail CUSTOMER
VRF CUSTOMER (VRF Id = 1); default RD 65100:1
  No interfaces
  Address family ipv4 (Table ID = 1 (0x1)):
    Export VPN route-target communities
      RT:65100:1
    Import VPN route-target communities
      RT:65100:1
    ...
```

Now check what the customer's contract says in their documentation...

After checking ticket notes: **CE-NIGERIA is a different customer than CE-SENEGAL and CE-SOUTHAFRICA!**

- **VRF CUSTOMER** was supposed to be two separate VRFs:
  - `VRF TELCO-AFRICA` — for CE-SENEGAL and CE-SOUTHAFRICA (same enterprise)
  - `VRF NIGERIA-ISP` — for CE-NIGERIA (different, unrelated company)

**Root Cause: A misconfiguration placed all three CEs into the same VRF**, leaking routes between unrelated customers — a **data breach risk**.

---

### Step 3 — Confirm the Misconfiguration

```
SP-PE1-LAGOS# show run interface GigabitEthernet0/3
interface GigabitEthernet0/3
 description TO_CE-NIGERIA (VRF CUSTOMER)
 ip vrf forwarding CUSTOMER    ← Should be VRF NIGERIA-ISP!
 ip address 10.2.1.1 255.255.255.252
```

```
SP-PE3-JHB# show run interface GigabitEthernet0/1
interface GigabitEthernet0/1
 description TO_CE-SOUTHAFRICA (VRF CUSTOMER)
 ip vrf forwarding CUSTOMER    ← This is CORRECT for TELCO-AFRICA
```

**Confirmed:** CE-NIGERIA should be in a separate VRF with a different Route Target.

---

## ✅ Resolution

### Phase 1 — Immediate Isolation (Service Impact Accepted)

On **SP-PE1-LAGOS**, move CE-NIGERIA to its own VRF immediately:

```
SP-PE1-LAGOS# conf t

! 1. Create the correct VRF for Nigeria customer
SP-PE1-LAGOS(config)# ip vrf NIGERIA-ISP
SP-PE1-LAGOS(config-vrf)# rd 65100:2
SP-PE1-LAGOS(config-vrf)# route-target export 65100:2
SP-PE1-LAGOS(config-vrf)# route-target import 65100:2
SP-PE1-LAGOS(config-vrf)# exit

! 2. Move the interface to the correct VRF (WARNING: causes brief outage on CE-NIGERIA)
SP-PE1-LAGOS(config)# interface GigabitEthernet0/3
SP-PE1-LAGOS(config-if)# ip vrf forwarding NIGERIA-ISP   ! This clears the IP address!
SP-PE1-LAGOS(config-if)# ip address 10.2.1.1 255.255.255.252
SP-PE1-LAGOS(config-if)# no shutdown
SP-PE1-LAGOS(config-if)# exit

! 3. Fix BGP for CE-NIGERIA in new VRF
SP-PE1-LAGOS(config)# router bgp 65100
SP-PE1-LAGOS(config-router)# address-family ipv4 vrf NIGERIA-ISP
SP-PE1-LAGOS(config-router-af)#  neighbor 10.2.1.2 remote-as 65001
SP-PE1-LAGOS(config-router-af)#  neighbor 10.2.1.2 activate
SP-PE1-LAGOS(config-router-af)#  neighbor 10.2.1.2 as-override
SP-PE1-LAGOS(config-router-af)#  exit-address-family

! OPTIONAL: Remove old VRF CUSTOMER BGP AF for Nigeria (if it was configured)
SP-PE1-LAGOS(config)# end
SP-PE1-LAGOS# write memory
```

### Phase 2 — Verify Isolation

```
SP-PE2-DAKAR# show ip route vrf CUSTOMER
B  192.168.20.0/24 [20/0]  via 10.2.2.2, 00:01:15
B  192.168.30.0/24 [200/0] via 10.0.0.3, 00:01:15
! 192.168.10.0/24 is GONE — isolation confirmed ✓
```

```
SP-PE1-LAGOS# show ip route vrf NIGERIA-ISP
B  192.168.10.0/24 [20/0] via 10.2.1.2, 00:01:22
! CE-NIGERIA routes now isolated in their own VRF ✓
```

### Phase 3 — Verify CE-SENEGAL Cannot Reach CE-NIGERIA

```
CE-SENEGAL# ping 192.168.10.1
.....
Success rate is 0 percent (0/5) — CORRECT, isolation restored ✓
```

---

## 📊 Impact Summary

| Field               | Detail                                              |
|---------------------|-----------------------------------------------------|
| **Security Risk**   | Two unrelated customers shared same VRF for ~45min |
| **Root Cause**      | Incorrect VRF assigned during PE1 provisioning      |
| **Resolution**      | Separate VRF NIGERIA-ISP created and corrected      |
| **Customer Impact** | CE-NIGERIA brief BGP reset during VRF migration     |
| **Next Action**     | Provisioning template audit; change management review |
| **Escalation**      | Security team notified per data breach protocol     |

---

## 🔑 Key Commands Reference

```bash
show vrf detail [vrf-name]                    # VRF RD and RT details
show ip route vrf [vrf-name]                  # Routes in a specific VRF
show run interface [int]                      # Check VRF assignment on interface
show bgp vpnv4 unicast vrf [vrf] summary      # BGP in VRF
show bgp vpnv4 unicast rd [rd]                # Routes with specific RD
show mpls forwarding-table vrf [vrf]          # MPLS forwarding per VRF
```

## ⚠️ Lesson Learned

> VRF provisioning must follow a strict change management process with a **peer review** step. Route Target misconfiguration can cause customer data to leak between tenants — a critical security event that must be reported per GDPR/data protection policies.
