# Validation rules (spec)

Decisions from the design session on 2026-11-05. Terms are defined in [GLOSSARY.md](../GLOSSARY.md).

## Flight Manifest

- Columns: all starter flight columns (Carrier, Flight No., Class, From, To, Date, Baggage, Seat, Gate, Boarding Time, Ticket No.), plus `FirstName`, `LastName`, `DateOfBirth`, `Sex`, plus `NameValidation`, `DoBValidation`, `PersonValidation`, `BoardingPassValidation`, `LuggageValidation`. The last five all start FALSE.
- `Passanger Name` is split into first and last name. Radha's row becomes `Radha S.` / `Kumar`.
- `DateOfBirth` and `Sex` are entered by hand from each Digital ID (ground truth).
- **Planted mismatch:** James Webb's `DateOfBirth` is off by one day, to show a failed DoB Validation and the ID-error Kiosk Message.

## Lookup

- The Kiosk finds the Manifest row by the **Ticket Number** on the Boarding Pass. If no row has that Ticket Number, Boarding Pass Validation is FALSE.

## Matching

| Validation | Rule |
|---|---|
| Name | Boarding Pass name and Digital ID name each match the Manifest. Comparison ignores case and punctuation, and checks the **first word of the given name** and the **last word of the surname** only. (The Digital IDs put middle initials in the surname field, e.g. LN "S Kumar", and sometimes the full name in the given-name field, e.g. FN "AVKASH CHAUHAN".) A Boarding Pass carries one full-name string: its first word is the given name and its last word is the surname. |
| DoB | The Digital ID date and the Manifest date are the same calendar date after parsing. |
| Boarding Pass | Flight number (carrier and number together, whitespace ignored), seat, class, origin, destination, flight date (calendar date) and boarding time (HH:MM, timezone label ignored) all match. Gate, baggage and ticket number are not compared. |
| Person | Face-match confidence between the Digital ID face and the Identity Video face is **≥ 0.65**. Tried in order: Face verify, then Video Indexer person recognition (Person model built from the ID photo). If neither is available, FALSE. A Passenger with no Identity Video is FALSE. |
| Luggage | From a simulated Luggage Scan: the 5 test images are assigned to the first 5 Passengers. TRUE when the highest lighter probability is **< 0.5**. The 6th Passenger is Not Scanned (stored FALSE, shown as "not scanned"). |

## Kiosk Message selection

1. Boarding Pass Validation FALSE → "boarding pass does not match" (Sir/Madam).
2. Otherwise, Name or DoB Validation FALSE → "ID does not match" (Sir/Madam).
3. Otherwise → welcome (Mr./Ms. from `Sex`, flight, boarding time, origin → destination, seat), then:
   - luggage sentence: no lighter / lighter flagged for removal / left out if Not Scanned
   - identity sentence: verified, please board / could not be verified, see a representative

## Passenger Feedback

- Video Indexer emotions and sentiment plus a positive/negative label (from the dominant sentiment), stored as JSON in `kiosk-results`. Not a Manifest column.

## Operations

- Secrets live in a git-ignored `.env`. A committed `.env.example` has blank values. The repo is scanned for secrets before every commit (it is public).
- Tests come first, in pytest, for normalization, the five matchers, Kiosk Message selection and Manifest updates. Target 80%+ coverage. Azure calls sit behind thin wrapper functions that tests replace with recorded JSON fixtures.
- Python 3.11 in a project `.venv` with pinned `requirements.txt`. The pinned file is also the rubric's library list.
- First build step: probe Face verify, Video Indexer, Document Intelligence and Custom Vision in the lab subscription before writing face code.
- Free (F0) tiers where offered. `scripts/teardown.sh` runs only after the Service Consumption Report screenshots are taken.

## Blob containers

`manifest`, `digital-ids`, `boarding-passes`, `training-boarding-passes` (synthetic PDFs plus `.labels.json`/`.ocr.json`), `identity-videos`, `luggage-scans`, `kiosk-results`.
