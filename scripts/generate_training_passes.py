"""Generate synthetic Training Boarding Passes from the starter .docx template.

They share the real passes' layout so the custom extraction model learns it. They never
belong to a Passenger on the Flight Manifest and are never validated.

Usage: python -m scripts.generate_training_passes [count]
Requires LibreOffice (`soffice`) for the .docx -> .pdf conversion.
"""

from __future__ import annotations

import copy
import json
import logging
import random
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from docx import Document
from docx.table import _Cell

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "starter/boarding_pass_template/boarding_pass_template.docx"
OUTPUT_DIR = ROOT / "data/training_boarding_passes"
SEED = 20261105

FIRST = ["Maria", "Kenji", "Aisha", "Lucas", "Priya", "Tomás", "Grace", "Omar", "Elena", "Noah", "Zara", "Ivan"]
LAST = ["Garcia", "Tanaka", "Okafor", "Martin", "Nair", "Silva", "Lee", "Haddad", "Novak", "Brown", "Ahmed", "Petrov"]
CITIES = ["Seattle", "New York", "Boston", "Denver", "Austin", "Miami", "Chicago", "San Francisco", "Atlanta", "Phoenix"]
CARRIERS = ["UA", "AA", "DL", "AS", "B6"]
CLASSES = ["E", "B", "F"]
MONTHS = ["January", "February", "March", "May", "June", "July", "August", "September", "October", "November"]


@dataclass(frozen=True)
class PassData:
    name: str
    carrier: str
    flight_no: str
    travel_class: str
    origin: str
    destination: str
    date: str
    baggage: str
    seat: str
    gate: str
    boarding_time: str
    ticket: str


def random_pass(rng: random.Random, index: int) -> PassData:
    origin, destination = rng.sample(CITIES, 2)
    hour, minute = rng.randint(1, 12), rng.choice(["00", "15", "30", "45"])
    return PassData(
        name=f"{rng.choice(FIRST)} {rng.choice(LAST)}",
        carrier=rng.choice(CARRIERS),
        flight_no=str(rng.randint(100, 999)),
        travel_class=rng.choice(CLASSES),
        origin=origin,
        destination=destination,
        date=f"{rng.choice(MONTHS)} {rng.randint(1, 28)}, {rng.choice([2022, 2023])}",
        baggage=rng.choice(["YES", "NO"]),
        seat=f"{rng.randint(1, 40)}{rng.choice('ABCDEF')}",
        gate=f"{rng.choice('ABCDG')}{rng.randint(1, 30)}",
        boarding_time=f"{hour}:{minute} {rng.choice(['AM', 'PM'])} {rng.choice(['PST', 'EST', 'CST', 'MST'])}",
        ticket=f"ETK-{50000000 + index * 7919}E",
    )


def _set(cell: _Cell, text: str, mode: str = "replace") -> None:
    """Write text into a cell, copying the formatting of the cell's first run when there is one.

    mode: "replace" the last paragraph's text, "inline" append to it, or "newline" add a paragraph.
    """
    template_run = next((r for p in cell.paragraphs for r in p.runs), None)
    paragraph = cell.add_paragraph() if mode == "newline" else cell.paragraphs[-1]
    if mode == "replace":
        for old in list(paragraph.runs):
            old._r.getparent().remove(old._r)
    run = paragraph.add_run(f" {text}" if mode == "inline" else text)
    if template_run is not None and template_run._r.rPr is not None:
        run._r.insert(0, copy.deepcopy(template_run._r.rPr))
    run.bold = False


def fill(data: PassData) -> Document:
    doc = Document(str(TEMPLATE))
    rows = doc.tables[0].rows
    _set(rows[0].cells[0], f"\n{data.ticket}")
    for col, value in {1: data.name, 3: data.carrier, 4: data.flight_no, 5: data.travel_class, 6: data.name}.items():
        _set(rows[2].cells[col], value)
    _set(rows[3].cells[7], data.origin)
    _set(rows[4].cells[7], data.destination)
    _set(rows[5].cells[1], data.origin, mode="inline")
    _set(rows[6].cells[1], data.destination, mode="inline")
    for col, value in {3: data.date, 4: data.baggage, 5: data.seat, 6: data.seat, 7: data.date}.items():
        _set(rows[6].cells[col], value)
    _set(rows[9].cells[1], data.gate)
    _set(rows[9].cells[2], data.boarding_time)
    _set(rows[8].cells[6], data.gate, mode="newline")
    _set(rows[8].cells[7], data.boarding_time, mode="newline")
    return doc


def to_pdf(docx_path: Path, out_dir: Path) -> Path:
    soffice = shutil.which("soffice")
    if soffice is None:
        raise RuntimeError("LibreOffice 'soffice' not found on PATH")
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(out_dir), str(docx_path)], check=True, capture_output=True)
    return out_dir / f"{docx_path.stem}.pdf"


def main(count: int = 10) -> None:
    rng = random.Random(SEED)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    truth: dict[str, dict[str, str]] = {}
    with tempfile.TemporaryDirectory() as tmp:
        for index in range(1, count + 1):
            data = random_pass(rng, index)
            docx_path = Path(tmp) / f"training-pass-{index:02d}.docx"
            fill(data).save(str(docx_path))
            pdf = to_pdf(docx_path, OUTPUT_DIR)
            truth[pdf.name] = asdict(data)
            logging.info("%s  %s %s%s %s->%s", pdf.name, data.name, data.carrier, data.flight_no, data.origin, data.destination)
    (OUTPUT_DIR / "values.json").write_text(json.dumps(truth, indent=2))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 10)
