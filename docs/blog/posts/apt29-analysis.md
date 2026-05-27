---
date: 2024-12-01
authors:
  - n1ghtfury
tags:
  - Detection Engineering
  - Sigma
  - KQL
  - SPL
  - EQL
  - ATT&CK
  - MITRE
  - Windows
  - SIEM
  - EDR
  - Alert Tuning
  - False Positives
  - Analytics
categories:
  - Detection Engineering
---

# [Technique or Use Case] — Detection Engineering Deep Dive

Replace this with a 2–3 sentence summary. Describe the adversary technique, why it matters
to defenders, and what the detection approach achieves. This appears on the blog index card.

<!-- more -->

!!! abstract "TL;DR"
    - **Technique:** `TXXXX.XXX` — Technique Name
    - **Tactic:** Execution / Persistence / Lateral Movement
    - **Signal Strength:** High fidelity when tuned
    - **Platforms:** Windows · Linux · macOS

---

## Technique Overview

Describe the adversary behavior: how it is executed, what variants exist, which threat actors
abuse it, and what the business impact is.

!!! info "Why This Matters"
    Cite threat intel or real-world incidents that make this a detection priority.
    Link to the ATT&CK page and any relevant threat reports here.

---

## ATT&CK Mapping

| ATT&CK ID | Technique | Sub-technique | Tactic | Platforms |
|-----------|-----------|:-------------:|--------|-----------|
| T1059.001 | Command and Scripting Interpreter | PowerShell | Execution | Windows |
| TXXXX.XXX | Replace with actual technique | — | Tactic | Windows |

---

## Data Requirements

!!! warning "Coverage Prerequisite"
    The detection below will not fire without the log sources in this table.
    Confirm collection is active before deploying the rule to production.

| Log Source | Provider | Minimum Fields | Collection Method |
|------------|----------|---------------|-------------------|
| Windows Security | Microsoft | EventID, SubjectUserName, CommandLine | GPO → SIEM |
| Sysmon | Sysinternals | Image, CommandLine, ParentImage, Hashes | WEF → SIEM |
| EDR Telemetry | CrowdStrike / Defender | ProcessCreate, NetworkConnect | Agent → SIEM |
| PowerShell | Microsoft | ScriptBlockText | ScriptBlock Logging GPO |

---

## Detection Logic

Explain *why* the signal below indicates malicious activity before showing the rule.

### Sigma

```yaml
title: Suspicious PowerShell Encoded Command Execution
id: 00000000-0000-0000-0000-000000000000
status: experimental
description: Detects PowerShell launched with encoded command flags used to hide payloads
references:
  - https://attack.mitre.org/techniques/T1059/001/
author: N1ghtFury
date: YYYY-MM-DD
logsource:
  product: windows
  category: process_creation
detection:
  selection:
    Image|endswith:
      - '\powershell.exe'
      - '\pwsh.exe'
    CommandLine|contains:
      - '-EncodedCommand'
      - ' -enc '
      - ' -e '
  filter_legitimate:
    Image|startswith:
      - 'C:\Program Files\'
      - 'C:\Windows\System32\'
    ParentImage|endswith:
      - '\services.exe'
      - '\svchost.exe'
  condition: selection and not filter_legitimate
falsepositives:
  - Legitimate admin automation using encoded commands
  - Managed software deployment tools (SCCM, Intune, PDQ)
level: high
tags:
  - attack.execution
  - attack.t1059.001
```

### KQL — Sentinel / Elastic

```kusto
DeviceProcessEvents
| where Timestamp > ago(24h)
| where FileName in~ ("powershell.exe", "pwsh.exe")
| where ProcessCommandLine has_any ("-EncodedCommand", " -enc ", " -e ")
| where InitiatingProcessFileName !in~ ("services.exe", "svchost.exe", "msiexec.exe")
| where not(FolderPath startswith @"C:\Program Files\")
| project Timestamp, DeviceName, AccountName, ProcessCommandLine, InitiatingProcessFileName
| order by Timestamp desc
```

### SPL — Splunk

```spl
index=* sourcetype=WinEventLog:Security EventCode=4688
  (CommandLine="*-EncodedCommand*" OR CommandLine="* -enc *")
| where NOT match(ParentProcessName, "sccm|intune|pdqdeploy")
| eval risk=case(match(CommandLine,"-nop.*-w hidden"), 90, match(CommandLine,"-EncodedCommand"), 70, true(), 50)
| table _time, host, user, CommandLine, ParentProcessName, risk
| sort - risk
```

### EQL — Elastic / Microsoft Defender

```eql
process where event.type == "start"
  and process.name : ("powershell.exe", "pwsh.exe")
  and process.args : ("-e", "-enc", "-EncodedCommand")
  and not process.parent.name : ("services.exe", "svchost.exe")
```

---

## Tuning & False Positive Management

!!! warning "Common False Positives"
    - IT automation that uses `-EncodedCommand` for legitimate scheduled tasks
    - Software packaging (SCCM, PDQ Deploy, Intune Win32 apps)
    - Authorized red team / penetration testing activity

**Suppression per platform:**

=== "Sentinel KQL"
    ```kusto
    | where DeviceName !in ("admin-ws-01", "jumpbox-01", "deploy-srv")
    | where InitiatingProcessVersionInfoCompanyName != "Microsoft Corporation"
    ```

=== "Splunk SPL"
    ```spl
    | where NOT (host IN ("admin-ws-01", "jumpbox-01"))
    | where NOT match(ParentProcessName, "sccm|pdqdeploy|intune")
    ```

=== "Sigma Filter Block"
    ```yaml
    filter_admin_hosts:
      ComputerName|endswith:
        - '-admin'
        - '-jumpbox'
    filter_signed_microsoft:
      Company: 'Microsoft Corporation'
      Signed: 'true'
    condition: selection and not 1 of filter_*
    ```

---

## Validation

### Atomic Red Team

```powershell
Invoke-AtomicTest T1059.001 -TestNumbers 1 -GetPrereqs
Invoke-AtomicTest T1059.001 -TestNumbers 1
Invoke-AtomicTest T1059.001 -TestNumbers 1 -Cleanup
```

### Expected Artifacts

| Log Source | Event ID | Key Field | Expected Value |
|------------|----------|-----------|----------------|
| Sysmon | 1 | CommandLine | Contains `-enc` |
| Windows Security | 4688 | NewProcessName | `powershell.exe` |
| PowerShell Operational | 4104 | ScriptBlockText | Decoded payload content |

---

## References

- [MITRE ATT&CK T1059.001](https://attack.mitre.org/techniques/T1059/001/)
- [Sigma Rules Repository](https://github.com/SigmaHQ/sigma)
- [Atomic Red Team T1059.001](https://github.com/redcanaryco/atomic-red-team/tree/master/atomics/T1059.001)
