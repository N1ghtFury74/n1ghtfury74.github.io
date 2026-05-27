---
date: 2025-01-01
authors:
  - n1ghtfury
tags:
  - Threat Hunting
  - Hypothesis-Driven
  - Behavioral Analytics
  - C2 Detection
  - Endpoint
  - Network
  - Identity
  - SPL
  - KQL
  - Sigma
  - Anomaly Detection
  - Baseline
categories:
  - DFIR & Threat Hunting
---

# [Hunt Name] — [Target Behavior or Threat Actor]

Replace this with a 2–3 sentence hunt summary. Describe the hypothesis, the telemetry used,
and the key outcome. This text appears on the blog index card.

<!-- more -->

!!! abstract "Hunt Summary"
    - **Hypothesis:** Attacker using [technique] to [objective]
    - **Data Sources:** Endpoint EDR · Network · Identity
    - **Hunt Type:** Hypothesis-Driven / Intelligence-Led / Baseline / Anomaly
    - **Outcome:** X confirmed findings · Y false positives · Z visibility gaps

---

## Hunt Hypothesis

!!! quote ""
    *"If [threat actor / technique] is active in our environment, we would expect to
    see [specific observable indicator] in [data source] because [reasoning]."*

**Hypothesis source:**

=== "Threat Intel"
    Link to CTI report, IOC feed, or peer notification that prompted this hunt.

=== "Previous Incident"
    Reference a prior DFIR investigation that revealed a detection gap worth hunting.

=== "Baseline Deviation"
    Describe the anomaly or alert that triggered this proactive investigation.

---

## ATT&CK Coverage

| ATT&CK ID | Technique | Tactic | Hunt Focus |
|-----------|-----------|--------|------------|
| TXXXX.XXX | Technique Name | Execution | Primary |
| TXXXX.XXX | Technique Name | Persistence | Secondary |
| TXXXX.XXX | Technique Name | Defense Evasion | Evasion variant |

---

## Environment & Telemetry

| Source | Platform | Coverage | Retention |
|--------|----------|----------|-----------|
| Endpoint EDR | CrowdStrike / Defender | Process, network, file, registry | 90 days |
| SIEM | Splunk / Elastic / Sentinel | Auth, DNS, proxy, firewall | 1 year |
| Network | NDR / Zeek / Suricata | NetFlow, DNS, TLS metadata | 30 days |
| Identity | AD / Entra ID | Auth events, privilege changes | 90 days |

!!! warning "Telemetry Gaps Identified Pre-Hunt"
    Document any missing log sources before starting. This defines what the hunt can and cannot confirm.

---

## Hunt Methodology

### Step 1 — Establish Baseline

=== "Splunk SPL"
    ```spl
    index=* sourcetype=WinEventLog EventCode=4688
    earliest=-30d latest=-7d
    | stats count by ParentProcessName, NewProcessName
    | sort -count
    | head 100
    ```

=== "Sentinel KQL"
    ```kusto
    DeviceProcessEvents
    | where Timestamp between (ago(30d) .. ago(7d))
    | summarize count() by InitiatingProcessFileName, FileName
    | order by count_ desc
    | take 100
    ```

### Step 2 — Identify Anomalies

=== "Splunk SPL"
    ```spl
    index=* sourcetype=WinEventLog EventCode=4688
    earliest=-7d
    | stats count by ParentProcessName, NewProcessName
    | where count < 5
    | sort count
    ```

=== "Sentinel KQL"
    ```kusto
    DeviceProcessEvents
    | where Timestamp > ago(7d)
    | summarize count() by InitiatingProcessFileName, FileName
    | where count_ < 5
    | order by count_ asc
    ```

=== "Sigma"
    ```yaml
    title: Rare Child Process of Suspicious Parent
    logsource:
      product: windows
      category: process_creation
    detection:
      selection:
        ParentImage|endswith: '\suspicious_parent.exe'
      filter_known_good:
        Image|endswith:
          - '\known_good.exe'
      condition: selection and not filter_known_good
    ```

### Step 3 — Triage & Validation

- [ ] Is the parent/child relationship expected for this host and user?
- [ ] Is the binary signed by a trusted authority?
- [ ] Does the hash match known-good or known-bad (VirusTotal)?
- [ ] Was this activity during business hours?
- [ ] Does it appear on other hosts (lateral spread indicator)?

### Step 4 — Pivot & Expand

```spl
index=* host="WORKSTATION-01"
earliest="2025-01-01T14:00:00" latest="2025-01-01T20:00:00"
| table _time, EventCode, host, user, CommandLine, ParentProcessName
| sort _time
```

---

## Findings

### Confirmed Findings

!!! success "Confirmed Malicious Activity"
    - **Host:** `WORKSTATION-01`
    - **User:** `jdoe@corp.com`
    - **Behavior:** [Describe the confirmed finding]
    - **ATT&CK:** `TXXXX.XXX`

### Notable False Positives

!!! info "False Positive"
    **Pattern:** `admin_tool.exe` spawning `cmd.exe` for scheduled maintenance.
    **Distinguish by:** Binary is code-signed + correlates with known maintenance window.

### Visibility Gaps

!!! warning "Visibility Gap"
    Describe any missing log sources that prevented full hunt coverage.

---

## Detection Rules Derived

```yaml
title: Behavior Confirmed During Hunt
id: 00000000-0000-0000-0000-000000000000
status: experimental
logsource:
  product: windows
  category: process_creation
detection:
  selection:
    CommandLine|contains:
      - 'indicator_from_hunt'
  condition: selection
level: high
tags:
  - attack.tXXXX
```

---

## Recommendations

| Priority | Action | Owner | ETA |
|----------|--------|-------|-----|
| Critical | Enable [missing log source] | SOC Eng | 1 week |
| High | Deploy rule for confirmed finding | Detection Eng | 2 weeks |
| Medium | Review [policy or control] | Security Arch | 1 quarter |

- [ ] Convert hunt queries to persistent scheduled detection rules
- [ ] Update ATT&CK Navigator heatmap for confirmed coverage
- [ ] Open tracking tickets for visibility gaps

---

## References

- [MITRE ATT&CK](https://attack.mitre.org/)
- [TaHiTI Threat Hunting Methodology](https://www.betaalvereniging.nl/en/safety/tahiti/)
