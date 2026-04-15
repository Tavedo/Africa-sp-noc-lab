# Africa SP NOC Lab — Cisco CML Portfolio

> Portfolio lab simulating a Service Provider Network Operations Center (NOC) for an African telecom operator providing MPLS L3VPN, IP Transit, DIA, and SD-WAN services across Nigeria, Senegal, South Africa, Niger, Burkina Faso, and Mali.

Built as a practical showcase for NOC/SP engineer roles requiring hands-on knowledge of BGP, MPLS L3VPN, VRF, WAN troubleshooting, and incident management — aligned with real telecom operator environments.

---

## Table of Contents

- [Lab Overview](#lab-overview)
- [Network Topology](#network-topology)
- [Device Inventory](#device-inventory)
- [IP Addressing Plan](#ip-addressing-plan)
- [VRF and Service Design](#vrf-and-service-design)
- [Services Simulated](#services-simulated)
- [Connectivity Matrix](#connectivity-matrix)
- [Lab Setup (CML)](#lab-setup-cml)
- [Verification Commands](#verification-commands)
- [NOC Scenarios](#noc-scenarios)
- [Key Lessons from the Build](#key-lessons-from-the-build)
- [Skills Demonstrated](#skills-demonstrated)
- [File Structure](#file-structure)
- [About This Lab](#about-this-lab)

---

## Lab Overview

| Parameter     | Detail                                                         |
|---------------|----------------------------------------------------------------|
| Platform      | Cisco Modeling Labs (CML) 2.x                                  |
| Nodes         | 15 IOSv routers                                                |
| Protocols     | OSPF Area 0, LDP, MP-BGP VPNv4, iBGP/eBGP, DMVPN/NHRP        |
| Services      | MPLS L3VPN (4 VRFs), DIA, IP Transit, SD-WAN (DMVPN Phase 2)  |
| Countries     | Nigeria, Senegal, South Africa, Niger                          |
| Focus         | NOC monitoring, L1 fault diagnosis, incident management        |
| Verified      | CE-SENEGAL to SE-SOUTHAFRICA ping = 100% via MPLS backbone     |

---

## Network Topology

```
                         INTERNET
                    ┌─────────────────────┐
                    │   ext-conn-0        │
                    │  (CML bridge to     │
                    │   real network)     │
                    └────────┬────────────┘
                             │ DHCP
                    ┌────────┴────────────┐
                    │   UPSTREAM-ISP      │  AS 65000
                    │   10.0.0.10/32      │  203.0.113.1
                    │                     │  G0/2→SDWAN-HUB
                    └────────┬────────────┘  G0/3→SDWAN-SPOKE1
                             │ eBGP            G0/4→SDWAN-SPOKE2
                             │ 203.0.113.0/30
                    ┌────────┴────────────┐
                    │   SP-PE1-LAGOS      │  AS 65100 · Lo0: 10.0.0.1/32
                    │   Nigeria PoP       │  4 VRFs · G0/0-G0/6
                    └──┬──┬──┬───────────┘
          G0/2 (OSPF)  │  │  │ G0/3 (OSPF)    G0/4→RR1  G0/5→CE-NIGER  G0/6→CE-DIA
                       │  │  │
            ┌──────────┘  │  └──────────┐
            │             │             │
   ┌────────┴───────┐      │    ┌────────┴───────┐
   │  SP-P1-CORE    │      │    │  SP-P2-CORE    │
   │  10.0.0.4/32   │◄─────┘    │  10.0.0.5/32   │
   │  LSR only      │           │  LSR only       │
   └──┬─────────┬───┘           └──┬──────────────┘
      │         │                  │
   G0/1      G0/3               G0/1
      │         │                  │
      │      ┌──┴──────────┐       │
      │      │  SP-RR1     │       │
      │      │  10.0.0.6   │       │
      │      │  iBGP RR    │◄──G0/5─┘
      │      └─────────────┘
      │
   ┌──┴──────────┐              ┌───────────────────┐
   │ SP-PE2-DAKAR│              │  SP-PE3-JHB       │
   │ 10.0.0.2/32 │              │  10.0.0.3/32      │
   │ Senegal PoP │              │  South Africa PoP  │
   └──────┬──────┘              └─────────┬──────────┘
   G0/0   │                               │ G0/0
          │                               │
   ┌──────┴──────┐              ┌──────────┴──────────┐
   │ CE-SENEGAL  │              │  SE-SOUTHAFRICA     │
   │ AS 65002    │              │  AS 65003            │
   │192.168.20.1 │              │  192.168.30.1        │
   └─────────────┘              └─────────────────────┘

   PE1-LAGOS additional connections:
   G0/1 → CE-NIGERIA  (AS 65001 · VRF NIGERIA-ISP)
   G0/5 → CE-NIGER    (AS 65004 · VRF NIGER-MPLS)
   G0/6 → CE-DIA      (AS 65005 · VRF DIA-CUSTOMER)

   SD-WAN simulation (DMVPN over internet):
   SDWAN-HUB    (172.16.0.1) ← Nigeria hub  → UPSTREAM-ISP G0/2
   SDWAN-SPOKE1 (172.16.1.1) ← Senegal      → UPSTREAM-ISP G0/3
   SDWAN-SPOKE2 (172.16.2.1) ← South Africa → UPSTREAM-ISP G0/4
```

---

## Device Inventory

| # | Device          | Role                             | AS     | Loopback      | VRF(s)                        |
|---|-----------------|----------------------------------|--------|---------------|-------------------------------|
| 1 | UPSTREAM-ISP    | Internet upstream peer           | 65000  | 10.0.0.10/32  | Global only                   |
| 2 | SP-PE1-LAGOS    | Provider Edge — Nigeria hub      | 65100  | 10.0.0.1/32   | NIGERIA-ISP · NIGER-MPLS · DIA-CUSTOMER |
| 3 | SP-P1-CORE      | Core LSR — no BGP, no VRF        | —      | 10.0.0.4/32   | None                          |
| 4 | SP-P2-CORE      | Core LSR — no BGP, no VRF        | —      | 10.0.0.5/32   | None                          |
| 5 | SP-RR1          | iBGP Route Reflector             | 65100  | 10.0.0.6/32   | None                          |
| 6 | SP-PE2-DAKAR    | Provider Edge — Senegal          | 65100  | 10.0.0.2/32   | CUSTOMER                      |
| 7 | SP-PE3-JHB      | Provider Edge — South Africa     | 65100  | 10.0.0.3/32   | CUSTOMER                      |
| 8 | CE-NIGERIA      | Customer Edge — Nigeria          | 65001  | 192.168.10.1  | VRF NIGERIA-ISP on PE1        |
| 9 | CE-SENEGAL      | Customer Edge — Senegal          | 65002  | 192.168.20.1  | VRF CUSTOMER on PE2           |
| 10| SE-SOUTHAFRICA  | Customer Edge — South Africa     | 65003  | 192.168.30.1  | VRF CUSTOMER on PE3           |
| 11| CE-NIGER        | Customer Edge — Niger            | 65004  | 192.168.40.1  | VRF NIGER-MPLS on PE1         |
| 12| CE-DIA          | DIA internet customer            | 65005  | 192.168.50.1  | VRF DIA-CUSTOMER on PE1       |
| 13| SDWAN-HUB       | DMVPN hub — Nigeria              | —      | 172.16.0.1    | OSPF process 2, GRE tunnel    |
| 14| SDWAN-SPOKE1    | DMVPN spoke — Senegal            | —      | 172.16.1.1    | OSPF process 2, GRE tunnel    |
| 15| SDWAN-SPOKE2    | DMVPN spoke — South Africa       | —      | 172.16.2.1    | OSPF process 2, GRE tunnel    |

---

## IP Addressing Plan

### Loopback addresses (router IDs)

| Device          | Loopback0        |
|-----------------|------------------|
| SP-PE1-LAGOS    | 10.0.0.1/32      |
| SP-PE2-DAKAR    | 10.0.0.2/32      |
| SP-PE3-JHB      | 10.0.0.3/32      |
| SP-P1-CORE      | 10.0.0.4/32      |
| SP-P2-CORE      | 10.0.0.5/32      |
| SP-RR1          | 10.0.0.6/32      |
| UPSTREAM-ISP    | 10.0.0.10/32     |

### SP backbone point-to-point links

| Link                          | Subnet          |
|-------------------------------|-----------------|
| PE1-LAGOS G0/2 ↔ P1-CORE G0/2 | 10.1.1.0/30    |
| PE1-LAGOS G0/3 ↔ P2-CORE G0/3 | 10.1.2.0/30    |
| PE2-DAKAR G0/1 ↔ P1-CORE G0/1 | 10.1.3.0/30    |
| PE3-JHB G0/1   ↔ P2-CORE G0/1 | 10.1.4.0/30    |
| P1-CORE G0/0   ↔ P2-CORE G0/0 | 10.1.5.0/30    |
| P1-CORE G0/3   ↔ RR1 G0/3     | 10.1.6.0/30    |
| PE1-LAGOS G0/4 ↔ RR1 G0/4     | 10.1.7.0/30    |
| PE2-DAKAR G0/2 ↔ RR1 G0/2     | 10.1.8.0/30    |
| PE3-JHB G0/5   ↔ RR1 G0/5     | 10.1.9.0/30    |
| PE1-LAGOS G0/0 ↔ UPSTREAM-ISP | 203.0.113.0/30 |

### Customer VRF links

| Customer        | PE Interface   | Subnet         | CE Loopback (LAN) |
|-----------------|----------------|----------------|-------------------|
| CE-NIGERIA      | PE1 G0/1       | 10.2.1.0/30    | 192.168.10.0/24   |
| CE-SENEGAL      | PE2 G0/0       | 10.2.2.0/30    | 192.168.20.0/24   |
| SE-SOUTHAFRICA  | PE3 G0/0       | 10.2.3.0/30    | 192.168.30.0/24   |
| CE-NIGER        | PE1 G0/5       | 10.2.4.0/30    | 192.168.40.0/24   |
| CE-DIA          | PE1 G0/6       | 10.2.5.0/30    | 192.168.50.0/24   |

### SD-WAN (DMVPN) addressing

| Device          | Underlay (internet) | Tunnel overlay    |
|-----------------|---------------------|-------------------|
| SDWAN-HUB       | 100.64.1.1/30       | 10.100.0.1/24     |
| SDWAN-SPOKE1    | 100.64.2.1/30       | 10.100.0.2/24     |
| SDWAN-SPOKE2    | 100.64.3.1/30       | 10.100.0.3/24     |
| UPSTREAM-ISP G0/2 | 100.64.1.2/30     | —                 |
| UPSTREAM-ISP G0/3 | 100.64.2.2/30     | —                 |
| UPSTREAM-ISP G0/4 | 100.64.3.2/30     | —                 |

---

## VRF and Service Design

| VRF Name       | PE Router(s)        | RD       | RT (export/import) | CE Device(s)                    | Service                    |
|----------------|---------------------|----------|--------------------|---------------------------------|----------------------------|
| CUSTOMER       | PE2-DAKAR + PE3-JHB | 65100:1  | 65100:1 / 65100:1  | CE-SENEGAL + SE-SOUTHAFRICA     | MPLS L3VPN — shared VPN    |
| NIGERIA-ISP    | PE1-LAGOS only      | 65100:2  | 65100:2 / 65100:2  | CE-NIGERIA                      | MPLS L3VPN — isolated      |
| NIGER-MPLS     | PE1-LAGOS only      | 65100:3  | 65100:3 / 65100:3  | CE-NIGER                        | MPLS L3VPN — isolated      |
| DIA-CUSTOMER   | PE1-LAGOS only      | 65100:4  | 65100:4 / 65100:4  | CE-DIA                          | DIA — internet via default route leak |

---

## Services Simulated

### 1. MPLS L3VPN

VRF CUSTOMER provides private MPLS VPN between CE-SENEGAL and SE-SOUTHAFRICA. Both PE2-DAKAR and PE3-JHB share RT 65100:1 — routes are exchanged via MP-BGP VPNv4 through the Route Reflector. CE-NIGERIA and CE-NIGER are separate isolated enterprises with different Route Targets — they cannot reach any other customer VRF.

Verified working:
```
CE-SENEGAL# ping 192.168.30.1 source 192.168.20.1
!!!!! Success rate is 100 percent (5/5)
```

### 2. DIA (Dedicated Internet Access)

CE-DIA receives internet access via a default route leaked from PE1-LAGOS global routing table into VRF DIA-CUSTOMER:

```
ip route vrf DIA-CUSTOMER 0.0.0.0 0.0.0.0 203.0.113.1 global
```

CE-DIA receives B* 0.0.0.0/0 via BGP and can reach 1.1.1.0/24 and 8.8.8.0/24 through UPSTREAM-ISP. CE-DIA cannot reach any other customer VRF.

### 3. IP Transit

UPSTREAM-ISP (AS 65000) simulates an internet transit provider — advertising 1.1.1.0/24 and 8.8.8.0/24 to PE1-LAGOS via eBGP. PE1-LAGOS redistributes a default route into the global table used by the DIA service.

### 4. SD-WAN simulation (DMVPN Phase 2)

Three IOSv routers simulate an SD-WAN overlay using DMVPN Phase 2 over a simulated internet transport:

- SDWAN-HUB (Nigeria) — mGRE interface, NHRP server
- SDWAN-SPOKE1 (Senegal) — registers with hub via NHRP
- SDWAN-SPOKE2 (South Africa) — registers with hub via NHRP
- OSPF process 2 runs over the tunnel overlay (equivalent to OMP in real Cisco SD-WAN)
- After initial NHRP resolution, spokes communicate directly without traversing the hub

Verified working:
```
SDWAN-SPOKE1# ping 172.16.2.1 source 172.16.1.1
!!!!! Success rate is 100 percent (5/5)
```

### 5. iBGP Route Reflector

SP-RR1 eliminates full-mesh iBGP between PE routers. Each PE has a single iBGP session to RR1. RR1 reflects both IPv4 unicast and VPNv4 prefixes between PE1, PE2 and PE3.

Note: On Cisco IOSv, peer-groups cannot be activated in address-family context. All route-reflector-client, activate and send-community extended commands must be applied per-neighbor IP — not via peer-group name.

---

## Connectivity Matrix

| Source              | Destination         | Result | Reason                                       |
|---------------------|---------------------|--------|----------------------------------------------|
| CE-SENEGAL          | SE-SOUTHAFRICA      | YES    | Same VRF CUSTOMER, RT 65100:1 on PE2 + PE3   |
| SE-SOUTHAFRICA      | CE-SENEGAL          | YES    | Same VRF — bidirectional                     |
| CE-SENEGAL          | CE-NIGERIA          | NO     | Different VRFs — RT:1 vs RT:2                |
| CE-SENEGAL          | CE-NIGER            | NO     | Different VRFs — RT:1 vs RT:3                |
| CE-SENEGAL          | CE-DIA              | NO     | Different VRFs — RT:1 vs RT:4                |
| CE-NIGERIA          | CE-NIGER            | NO     | Both isolated enterprises — different RTs    |
| CE-DIA              | Internet 1.1.1.1    | YES    | Default route leaked from global table       |
| CE-DIA              | CE-SENEGAL          | NO     | DIA VRF has no VPN customer routes           |
| SDWAN-SPOKE1        | SDWAN-SPOKE2        | YES    | DMVPN Phase 2 direct spoke-to-spoke          |
| Any CE              | SP backbone 10.0.0.x| NO     | SP loopbacks are in global table — invisible from VRF |

Important: always source CE pings from Loopback0 (the /24 prefix) — not from the PE-CE link (/30). The /30 is not advertised in BGP so remote CE has no return path.

---

## Lab Setup (CML)

### Prerequisites

- Cisco Modeling Labs 2.x (Personal or Enterprise)
- IOSv image (15.x or higher)
- Minimum 8 GB RAM allocated to CML

### Import the lab

```bash
git clone https://github.com/YOUR_USERNAME/africa-sp-noc-lab.git
cd africa-sp-noc-lab
```

In CML Web UI: File → Import Lab → Upload `topology.yaml`

Start all nodes and wait for boot (approximately 3-4 minutes).

### Apply configurations

Copy-paste each config from the `configs/` folder into the corresponding node console. Configs must be applied in this order to avoid dependency issues:

1. UPSTREAM-ISP
2. SP-P1-CORE and SP-P2-CORE (no BGP dependencies)
3. SP-RR1
4. SP-PE1-LAGOS, SP-PE2-DAKAR, SP-PE3-JHB
5. CE-NIGERIA, CE-SENEGAL, SE-SOUTHAFRICA, CE-NIGER, CE-DIA
6. SDWAN-HUB, SDWAN-SPOKE1, SDWAN-SPOKE2

---

## Verification Commands

Run in this order — each layer depends on the one below it:

```bash
# Step 1 — OSPF backbone (foundation of everything)
show ip ospf neighbor                     # all SP routers — must show FULL/-
show ip ospf interface brief              # Loopback0 MUST appear in this list

# Step 2 — MPLS LDP
show mpls ldp neighbor                    # all Oper state
show mpls forwarding-table                # labels for all 10.0.0.x/32 loopbacks

# Step 3 — BGP control plane
show bgp vpnv4 unicast all summary        # on RR1 — PE1/PE2/PE3 all Estab
show bgp ipv4 unicast summary             # on PE1 — upstream session Estab

# Step 4 — VRF routing tables
show ip route vrf CUSTOMER                # on PE2 or PE3 — both customer prefixes present
show ip route vrf DIA-CUSTOMER            # on PE1 — S* 0.0.0.0/0 present

# Step 5 — End-to-end service tests
CE-SENEGAL# ping 192.168.30.1 source 192.168.20.1   # VPN — must return !!!!!
CE-SENEGAL# ping 192.168.10.1 source 192.168.20.1   # isolation — must return .....
CE-DIA#     ping 1.1.1.1                             # DIA internet — must return !!!!!

# Step 6 — SD-WAN verification
SDWAN-HUB#    show dmvpn                             # both spokes Up
SDWAN-SPOKE1# ping 172.16.2.1 source 172.16.1.1     # spoke-to-spoke !!!!!
```

---

## NOC Scenarios

Realistic incident scenarios with step-by-step diagnosis and resolution — as handled in a 24x7 NOC:

| # | Scenario                              | Service   | Priority |
|---|---------------------------------------|-----------|----------|
| 1 | BGP session down — Nigeria customer   | MPLS VPN  | P2       |
| 2 | MPLS LSP black-holing                 | Data plane| P1       |
| 3 | High latency — Dakar link congestion  | Performance| P3      |
| 4 | LDP neighbor lost — core link failure | Protocol  | P2       |
| 5 | VRF route leak — security breach      | Security  | P1       |

See `scenarios/` folder for full diagnosis steps and sample ticket documentation.

---

## Key Lessons from the Build

These are real errors encountered and resolved during the lab build — each one is a valuable lesson for SP NOC work:

1. `ip ospf 1 area 0` on `Loopback0` is mandatory on every SP router. Without it LDP cannot form TCP sessions (no loopback reachability), iBGP sessions fail (update-source unreachable), and all VPN services break. This single missing command caused 90% of all failures during the build.

2. On Cisco IOSv, `remote-as` must be declared at the top-level `router bgp` block before any `address-family` can activate that neighbor.

3. `route-reflector-client` must be inside `address-family` — not at the top-level BGP block.

4. On Cisco IOSv, peer-group names cannot be activated in `address-family` context — use individual neighbor IPs for `activate`, `route-reflector-client`, and `send-community extended`.

5. `passive-interface` only works on global-table interfaces enrolled in OSPF. VRF interfaces are invisible to OSPF process 1 — applying `passive-interface` to them causes: `% Interface does not belong to this process`.

6. For DIA default route leak: `ip route vrf NAME 0.0.0.0 0.0.0.0 NEXTHOP global` — the next-hop IP must come before the `global` keyword.

7. Both ends of a point-to-point link must have different IPs from the same /30. RR1 G0/5 and PE3-JHB G0/5 originally had the same IP — OSPF showed 0/0 neighbors on that interface until corrected.

8. Always source CE-to-CE pings from `Loopback0` — the PE-CE /30 link is not in BGP so the remote CE has no return path to it.

---

## Skills Demonstrated

| Skill                      | Relevance to NOC Role                                |
|----------------------------|------------------------------------------------------|
| MPLS L3VPN design          | Core SP service delivered to African enterprise customers |
| BGP — iBGP/eBGP/VPNv4      | IP Transit, DIA, inter-site VPN, Route Reflector      |
| OSPF IGP                   | SP backbone reachability and LDP transport dependency |
| VRF and RT isolation       | Customer separation, multi-tenant SP architecture     |
| LDP and MPLS forwarding    | Label-switched path verification and troubleshooting  |
| DIA via default route leak | Dedicated internet access service configuration       |
| SD-WAN via DMVPN Phase 2   | Overlay/underlay concept, NHRP, spoke-to-spoke tunnels|
| NOC incident diagnosis     | L1 troubleshooting methodology for 5 realistic scenarios |
| Ticket documentation       | Structured incident logging aligned to P1/P2/P3 SLAs |
| Traffic analysis           | Interface utilisation, drops, bandwidth saturation    |
| Real IOS error diagnosis   | Every error in Key Lessons was encountered and resolved on live IOS |

---

## File Structure

```
africa-sp-noc-lab/
├── README.md
├── topology.yaml
├── configs/
│   ├── upstream/
│   │   └── UPSTREAM-ISP.txt
│   ├── pe/
│   │   ├── SP-PE1-LAGOS.txt
│   │   ├── SP-PE2-DAKAR.txt
│   │   └── SP-PE3-JHB.txt
│   ├── p/
│   │   ├── SP-P1-CORE.txt
│   │   └── SP-P2-CORE.txt
│   ├── rr/
│   │   └── SP-RR1.txt
│   ├── ce/
│   │   ├── CE-NIGERIA.txt
│   │   ├── CE-SENEGAL.txt
│   │   ├── SE-SOUTHAFRICA.txt
│   │   ├── CE-NIGER.txt
│   │   └── CE-DIA.txt
│   └── sdwan/
│       ├── SDWAN-HUB.txt
│       ├── SDWAN-SPOKE1.txt
│       └── SDWAN-SPOKE2.txt
├── scenarios/
│   ├── 01-bgp-session-down.md
│   ├── 02-mpls-blackhole.md
│   ├── 03-high-latency-dakar.md
│   ├── 04-ldp-neighbor-lost.md
│   └── 05-vrf-route-leak.md
└── docs/
    ├── ip-addressing.md
    ├── vrf-design.md
    └── noc-runbook.md
```

---

## About This Lab

This lab was built to demonstrate practical Service Provider and NOC skills relevant to telecom operators running connectivity services across Sub-Saharan and West Africa. It reflects the real environment of a NOC engineer responsible for monitoring, diagnosing and resolving incidents on an MPLS/BGP network.

All configurations were manually applied and debugged on live IOS consoles in Cisco CML. AI-assisted configuration generation was used as a study aid alongside Cisco documentation and CCNP SP study materials. All troubleshooting was hands-on — every error in the Key Lessons section was encountered and resolved during the build.

Technologies: Cisco IOS · MPLS · BGP · OSPF · LDP · VRF · MP-BGP VPNv4 · DMVPN · NHRP · GRE

---

*Built with Cisco Modeling Labs (CML) | Aligned with CCNP Service Provider*
