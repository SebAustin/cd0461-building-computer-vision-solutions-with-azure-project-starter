# Glossary — Automated Passenger Boarding Kiosk

## People and documents

**Passenger**
A person listed on the Flight Manifest who is expected to board the flight. Identified by first name, last name, date of birth and sex.
_Avoid_: customer, traveller, user.

**Flight Manifest**
The authoritative table of every Passenger on one flight, holding their Flight Details, demographic details and Validation Statuses. All Validations compare evidence *against* the Flight Manifest; the Manifest is never corrected from the evidence.
_Avoid_: passenger list, roster.

**Flight Details**
The flight-specific facts of a Passenger's booking: carrier, flight number, class, origin, destination, flight date, boarding time, gate, seat, baggage and ticket number. Most are shared by every Passenger on the flight; seat, class, baggage and ticket number are per-Passenger.

**Digital ID**
A government identity card image (here, a California Driver License) showing a Passenger's name, date of birth, sex and face picture.
_Avoid_: ID card, license (when meaning the general concept).

**Boarding Pass**
The document a Passenger presents at the Kiosk, showing their name and Flight Details. Always belongs to exactly one Passenger on the Flight Manifest.

**Ticket Number**
The number printed on a Boarding Pass that uniquely identifies one Passenger's row on the Flight Manifest. The Kiosk finds the Passenger by Ticket Number, never by name.

**Training Boarding Pass**
A synthetic Boarding Pass used only to teach the extraction model its layout. It does not belong to any Passenger and is never validated.

**Identity Video**
A short video of one Passenger's face, captured at the Kiosk, used for face matching and for Passenger Feedback.

## Validation

**Validation**
A single yes/no check of one kind of evidence against the Flight Manifest for one Passenger. There are exactly five: Name Validation, DoB Validation, Boarding Pass Validation, Person Validation and Luggage Validation.

**Validation Status**
The recorded TRUE/FALSE outcome of one Validation for one Passenger. Every Validation Status starts as FALSE and turns TRUE only when the Validation succeeds.

**Name Validation**
The three-way Validation that the name on the Boarding Pass and the name on the Digital ID both match the Passenger's name on the Flight Manifest. Names are matched on first given name and last name only.

**DoB Validation**
The Validation that the date of birth on the Digital ID matches the Flight Manifest.

**Boarding Pass Validation**
The Validation that the Flight Details on the Boarding Pass (flight number, seat, class, origin, destination, flight date, boarding time) match the Flight Manifest.
_Avoid_: flight details validation.

**Person Validation**
The Validation that the face on the Digital ID and the face in the Identity Video belong to the same person. A Passenger with no Identity Video cannot pass it.
_Avoid_: face validation, identity validation (ambiguous with the whole process).

**Luggage Validation**
The Validation that a Passenger's carry-on items contain no prohibited item (a lighter). Performed outside the Kiosk, from a Luggage Scan.

**Luggage Scan**
An image of a Passenger's carry-on items, checked for lighters. A Passenger may be **Not Scanned**: that is different from a failed Luggage Validation, and the Kiosk Message must not claim a lighter was found.

## Kiosk

**Kiosk**
The self-service boarding station that reads a Passenger's Digital ID, Boarding Pass and Identity Video and tells them whether they may board.

**Kiosk Message**
The text shown to a Passenger at the end of the Kiosk process, chosen from their Validation Statuses.

**Passenger Feedback**
The emotions and sentiment read from the Identity Video, recorded as positive or negative feedback about the boarding experience.
