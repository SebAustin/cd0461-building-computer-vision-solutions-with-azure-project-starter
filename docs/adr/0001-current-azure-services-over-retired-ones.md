# 1. Build on current Azure AI services, not the retired ones the brief names

- Status: Accepted
- Date: 2026-11-05

## Context

The course brief (written around 2022) names services that have since been retired or renamed:

| Brief says | Status | We use |
|---|---|---|
| Azure Video Analyzer | Retired Dec 2022 | Azure AI Video Indexer |
| Form Recognizer | Renamed | Azure AI Document Intelligence (`prebuilt-idDocument`, custom template model) |
| FOTT labeling site (fott-2-1.azurewebsites.net) | Superseded | Document Intelligence Studio (still writes `*.labels.json` / `*.ocr.json` to Blob) |
| Face API | Still exists; verify/identify is Limited Access | Azure AI Face, if the lab subscription has access |
| Custom Vision | Still exists | Azure AI Custom Vision (object detection) |

Following the brief literally would mean building against endpoints that no longer exist.

## Decision

Implement against the current services and SDKs. The write-up includes a "service name mapping" table so a reviewer can trace each rubric item (e.g. "upload video to Azure Video Analyzer") to the service that fulfils it.

## Consequences

- Rubric wording and screenshots will show different product names. The mapping table explains the difference.
- **Probe result (2026-11-05), subscription `Udacity-GenAI-Subscription-14`:** we cannot create resource groups. In the existing group `Regroup_1aqrpsihqh`, Storage, Document Intelligence and AI Services can be created and work. The policy "Restrict Vision and Speech AI services" denies Face, Custom Vision and Computer Vision. Face calls through AI Services return 401. `Microsoft.VideoIndexer` cannot be registered. Face, Custom Vision and Video Indexer therefore need a different subscription.
- Face verification may be blocked by Limited Access in the Udacity lab subscription. This is checked before any face code is written. Only 3 of 5 Validations need to pass, so Name, DoB and Boarding Pass Validations do not depend on it.
