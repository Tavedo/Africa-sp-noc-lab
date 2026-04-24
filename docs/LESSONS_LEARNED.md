
---

## Session 2 — Real lab troubleshooting findings

### Lesson 10 — CE-DIA Loopback0 loses IP when ip vrf forwarding removed
- **Symptom**: ping source 192.168.50.1 → Invalid source address
- **Cause**: IOS clears IP when ip vrf forwarding removed from interface
- **Fix**: re-apply ip address 192.168.50.1 255.255.255.0 on Loopback0
- **Rule**: CE routers NEVER have VRF config — VRFs only on PE routers

### Lesson 11 — Null0 route blackholes traffic (more specific wins)
- **Symptom**: UPSTREAM-ISP ping 8.8.8.8 → 0% even with default route present
- **Cause**: ip route 8.8.8.0/24 Null0 more specific than default — longest match wins
- **Fix**: no ip route 8.8.8.0 255.255.255.0 Null0
- **Rule**: Null0 routes for BGP network statements block real traffic if a real path exists

### Lesson 12 — DHCP default route not reliable in CML
- **Symptom**: ip route 0.0.0.0 0.0.0.0 dhcp — no gateway installed
- **Cause**: CML ext-conn DHCP provides IP but not default-router option
- **Fix**: ip route 0.0.0.0 0.0.0.0 192.168.254.128 (static CML bridge gateway)

### Lesson 13 — Plain GRE DMVPN does not form on IOSv without IPsec
- **Symptom**: show dmvpn → spokes stuck in INTF state never Up
- **Cause**: IOSv requires tunnel protection ipsec profile for DMVPN to negotiate
- **Fix**: Add crypto isakmp policy + pre-shared key + transform set + profile
         Apply: tunnel protection ipsec profile DMVPN-IPSEC-PROFILE on all Tunnel0
- **Verify**: show crypto isakmp sa → QM_IDLE
             show dmvpn → Up
             ping spoke-to-spoke → !!!!!

### Lesson 14 — NHRP multicast dynamic missing blocks OSPF over tunnel
- **Symptom**: IKE up but OSPF never forms over overlay
- **Cause**: ip nhrp map multicast dynamic missing on hub — OSPF hellos not forwarded
- **Fix**: Add ip nhrp map multicast dynamic to SDWAN-HUB Tunnel0 only
