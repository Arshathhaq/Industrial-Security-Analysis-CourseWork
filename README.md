# AQUASHIELD: Water Monitoring System

AQUASHIELD is a virtual industrial water-tank monitoring and control environment developed as a semester project in **Security Aspects in Industrial Areas**. The implementation demonstrates an industrial OT/SCADA architecture with network segmentation, firewall enforcement, simulated PLC control, HMI/SCADA operation, intrusion detection, centralized security monitoring, and security-control assessment.

> **Project scope:** This README describes the individual implementation contribution documented in the semester project report. The wider project was completed by four students; the IT firewall, MQTT broker, and external Internet network were implemented by teammates.

## Overview

The system models a virtual industrial water-tank process and separates its components into dedicated network zones. Communication between zones is controlled by an OT pfSense firewall using explicit allow rules.

The implemented environment includes:

- OT network segmentation
- pfSense OT firewall with default-deny policies
- Nginx reverse proxy in an industrial DMZ
- Python-based PLC simulator using `pymodbus`
- Modbus TCP process communication
- FUXA HMI/SCADA
- Role-based HMI access
- Alarm management
- SQLite historian and trend visualization
- Suricata IDS
- Wazuh agent and centralized alert pipeline
- Modbus TCP and MQTT traffic monitoring
- MITRE ATT&CK for ICS mapping
- IEC 62443-oriented security assessment

## Architecture

The implemented network is organized as follows:

| Zone / Component | Address | Purpose |
|---|---|---|
| IT Network | `10.21.1.0/24` | Enterprise-side network |
| OT Firewall WAN | `10.21.1.12` | Upstream OT boundary |
| Industrial DMZ | `10.21.2.0/24` | Controlled external-facing services |
| Nginx Reverse Proxy | `10.21.2.20` | Controlled access path to FUXA |
| HMI Network | `10.21.3.0/24` | SCADA/HMI environment |
| FUXA SCADA/HMI | `10.21.3.30` | Process operation and monitoring |
| PLC Network | `10.21.4.0/24` | Virtual controller network |
| Python PLC Simulator | `10.21.4.40:5020` | Modbus TCP process controller |
| Wazuh Manager | `10.21.1.100` | Central security-event management |
| MQTT Broker | Team component | Integrated broker path |

### Purdue Model Mapping

The architecture maps to the Purdue model approximately as:

- **Level 5:** External / Internet
- **Level 4:** Enterprise IT
- **Level 3.5:** Industrial DMZ / Nginx reverse proxy
- **Level 3:** Operations / FUXA, historian, SQLite, Wazuh agent
- **Level 2:** Control / Python PLC simulator and Modbus TCP
- **Level 1:** Sensors and actuators / virtual pump, valve, tank, emergency stop
- **Level 0:** Industrial process / virtual water-tank process

## Communication Paths

The OT firewall uses default-deny policies and permits only required conduits, including:

- HTTP access to the DMZ reverse proxy
- Reverse proxy access to FUXA on port `1881`
- Modbus TCP from FUXA to the PLC simulator on port `5020`
- Wazuh agent forwarding on ports `1514–1515`

This design limits unnecessary cross-zone communication and reduces direct reachability of OT assets.

## PLC Simulator

The PLC is implemented as a Python service using `pymodbus`.

### Process Variables

| Type | Address | Tag | Description |
|---|---:|---|---|
| Holding Register | `40001` | `tank_level` | Virtual tank level as a percentage |
| Coil | `00001` | `pump` | Pump command |
| Coil | `00002` | `valve` | Inlet/outlet valve state |
| Coil | `00003` | `automatic` | Automatic control mode |
| Coil | `00004` | `emergency_stop` | Safety stop overriding normal control |

The simulator uses TCP port `5020` instead of privileged port `502` and is deployed as a `systemd` service so it can restart after service interruption or host reboot.

## FUXA HMI / SCADA

FUXA runs on `10.21.3.30` and port `1881`.

The HMI provides:

### Water Control
Available to **Admin** users:

- Pump control
- Valve control
- Automatic mode
- Emergency stop

### Water Monitor
Provides observation of:

- Tank state
- Process indicators

### Alarm & Trends
Provides:

- Alarm list
- Trend graphs
- High-level alarm
- Low-level alarm
- Emergency-stop state

### Historian
Uses SQLite to retain process values and event states for later review.

### Roles

| Role | Access |
|---|---|
| Admin | Process control and administrative functions |
| Analyst | Monitoring, alarms, trends, and historian review |

The role separation keeps control functions away from monitoring-only users.

## Security Monitoring

### Suricata IDS

Suricata is deployed on the OT pfSense firewall at `10.21.2.1`.

It monitors industrial traffic crossing the OT boundary and generates structured EVE JSON events. Detection focuses on:

- Modbus TCP traffic between FUXA and the PLC simulator
- MQTT traffic associated with the integrated broker path

### Wazuh

The Wazuh agent runs on the SCADA host and forwards relevant security events to the Wazuh manager at `10.21.1.100` using ports `1514–1515`.

The monitoring pipeline can be summarized as:

```text
Modbus / MQTT Traffic
        |
        v
Suricata IDS
(pfSense OT Firewall)
        |
        v
    EVE JSON
        |
        v
   Wazuh Agent
        |
        v
 Wazuh Manager
        |
        v
   Alert Review
```

## Security Analysis

The project uses MITRE ATT&CK for ICS to structure analysis of potential attack paths. Relevant techniques include unauthorized command messages, manipulation of control, network service scanning, default credentials, blocking reporting messages, loss of view, denial of service, and theft of operational information.

The main defensive mechanisms are:

1. **Network segmentation** — limits reachable services and lateral movement.
2. **Least-privilege firewall rules** — restrict permitted cross-zone communication.
3. **HMI role separation** — separates control from observation.
4. **Protocol monitoring** — provides visibility into Modbus and MQTT traffic.
5. **Historian evidence** — preserves process behavior for investigation.
6. **Centralized security monitoring** — forwards relevant events to Wazuh.

## Verification

The system was evaluated using scenario-based testing rather than installation checks alone.

Tested areas included:

- Network segmentation and reverse-proxy access
- Modbus communication
- Role-based HMI access
- Alarm behavior
- Historian and trend recording
- IDS detection
- Wazuh/SIEM forwarding
- PLC simulator availability and restart behavior

The documented tests passed within the controlled virtual laboratory environment.

## Risk and Limitations

The implementation is a laboratory project and should not be interpreted as a production-ready industrial control system or a formal security certification.

Important residual risks and limitations include:

- **Modbus TCP is unauthenticated and unencrypted.**
- Allowed Modbus conduits still require monitoring because firewall rules cannot determine application intent.
- The reverse proxy was not presented as certificate/TLS hardened.
- MQTT broker hardening was outside the individual implementation scope.
- The PLC is a Python simulator and cannot represent all failure modes of a physical controller.
- The project did not perform a full penetration test or adversary-emulation exercise.
- The IEC 62443 mapping is an assessment against relevant requirements, not an IEC 62443 certification or formal security-level assessment.

## IEC 62443 Alignment

The implementation was assessed against relevant IEC 62443-3-3 concepts, particularly:

- Restricted data flow
- Zone boundary protection
- Human user identification and authentication
- Authorization enforcement
- Least functionality
- Communication integrity
- Audit-log accessibility
- Continuous monitoring support
- Resource availability

The strongest alignment was associated with restricted data flow, use control, event visibility, and operational availability.

## Project Structure

The exact source-code repository structure is not documented in the project report. A practical repository can organize the implementation into components such as:

```text
AQUASHIELD/
├── README.md
├── plc/
│   └── python-modbus-simulator
├── fuxa/
│   ├── hmi/
│   ├── alarms/
│   └── historian/
├── firewall/
│   └── pfsense-rules
├── ids/
│   └── suricata/
├── monitoring/
│   └── wazuh/
├── reverse-proxy/
│   └── nginx/
└── docs/
```

The structure above is a documentation-oriented example; the report does not specify that this exact directory layout was used.

## References

The project report references the following resources:

- IEC 62443 series — Industrial communication networks and network/system security
- NIST SP 800-82 Rev. 3 — *Guide to Operational Technology Security*
- CISA — ICS Recommended Practices
- Suricata User Guide
- Wazuh Documentation
- MITRE ATT&CK for ICS
- IEC 62443-3-3 — System security requirements and security levels

## Author

**Arshathul Mohamed Haq Bahadur Ibrahim Khalifullah**

Semester project: **Security Aspects in Industrial Areas**  
Submission date: **15 July 2026**
