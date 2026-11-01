"""Reference database: merges all docs/references/*.yaml files.

Every file maps reference ids to entries:

    werling2011:
      type: thesis            # paper | report | standard | book | norm | documentation | software | thesis
      authors: [Moritz Werling]
      title: ...
      year: 2011
      publisher: KIT Scientific Publishing

Special files:
    user.yaml    references created by users (GUI "Quellen" tab, add_user_reference())
    links.yaml   links reference -> module / component / concept created by users:
                     links:
                       - {reference: werling2011, target: "component:trajectory_planner/werling", note: "..."}

The database validates entries (required fields, duplicate ids, known types), searches,
formats German citations ("Werling (2011)", "Mitschke und Wallentowitz (2014)",
"Schramm et al. (2018)") and exports BibTeX. Broken files produce issues, never exceptions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .paths import references_dir

REFERENCE_TYPES = ("paper", "report", "standard", "book", "norm", "documentation", "software", "thesis")
TYPE_LABELS = {"paper": "Fachartikel", "report": "Technischer Bericht", "standard": "Industriestandard",
               "book": "Fachbuch", "norm": "Norm", "documentation": "Offizielle Dokumentation",
               "software": "Open-Source-Referenz", "thesis": "Dissertation / Abschlussarbeit"}

# required fields per type; a tuple means "one of them"
REQUIRED_FIELDS = {
    "paper": ("authors", "title", "year", "venue"),
    "report": ("title", "year", ("authors", "institution", "organization")),
    "standard": ("title", ("number", "organization")),
    "norm": ("title", ("number", "organization")),
    "book": ("authors", "title", "year", "publisher"),
    "thesis": ("authors", "title", "year", ("publisher", "institution", "school")),
    "documentation": ("title", ("url", "organization")),
    "software": ("title", "url"),
}
KNOWN_FIELDS = ("type", "authors", "title", "year", "venue", "publisher", "edition", "volume", "number", "pages",
                "organization", "institution", "school", "url", "doi", "isbn", "notes", "keywords", "language",
                "series", "address", "version", "month")
ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_.:\-]*$")
SPECIAL_FILES = ("links.yaml",)
USER_FILE = "user.yaml"
LINKS_FILE = "links.yaml"
_PARTICLES = {"van", "von", "de", "der", "den", "di", "du", "la", "le", "da", "del", "ter", "zu"}


@dataclass
class Issue:
    level: str          # "error" | "warning"
    ref_id: str
    message: str
    file: str = ""

    def __str__(self):
        where = f" ({self.file})" if self.file else ""
        return f"[{self.level}] {self.ref_id}: {self.message}{where}"


@dataclass
class Reference:
    id: str
    type: str = "paper"
    title: str = ""
    authors: list = field(default_factory=list)
    year: object = None
    venue: str = ""
    publisher: str = ""
    edition: str = ""
    volume: str = ""
    number: str = ""
    pages: str = ""
    organization: str = ""
    institution: str = ""
    school: str = ""
    url: str = ""
    doi: str = ""
    isbn: str = ""
    notes: str = ""
    keywords: list = field(default_factory=list)
    language: str = ""
    series: str = ""
    address: str = ""
    version: str = ""
    month: str = ""
    source_file: str = ""
    user: bool = False
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, ref_id, data, source_file="", user=False):
        data = dict(data or {})
        kwargs = {"id": str(ref_id), "source_file": source_file, "user": user}
        extra = {}
        for key, value in data.items():
            if key in KNOWN_FIELDS:
                kwargs[key] = value
            else:
                extra[key] = value
        authors = kwargs.get("authors", [])
        if isinstance(authors, str):
            authors = [a.strip() for a in re.split(r";| and ", authors) if a.strip()]
        kwargs["authors"] = [str(a) for a in (authors or [])]
        keywords = kwargs.get("keywords", [])
        kwargs["keywords"] = [k.strip() for k in keywords.split(",")] if isinstance(keywords, str) else list(keywords or [])
        for key in ("title", "venue", "publisher", "edition", "volume", "number", "pages", "organization",
                    "institution", "school", "url", "doi", "isbn", "notes", "language", "series", "address",
                    "version", "month", "type"):
            if key in kwargs and kwargs[key] is not None:
                kwargs[key] = str(kwargs[key]).strip()
            elif key in kwargs:
                kwargs[key] = ""
        ref = cls(**kwargs)
        ref.extra = extra
        return ref

    def to_dict(self):
        # YAML representation (only non-empty fields, fixed order)
        out = {"type": self.type}
        for key in KNOWN_FIELDS[1:]:
            value = getattr(self, key)
            if value not in (None, "", [], {}):
                out[key] = value
        out.update(self.extra)
        return out

    # ------------------------------------------------------------------ citation
    @property
    def last_names(self):
        return [last_name(a) for a in self.authors]

    @property
    def year_text(self):
        return "" if self.year in (None, "") else str(self.year)

    def short(self, locator=""):
        # German short citation: "Werling (2011)", "Mitschke und Wallentowitz (2014)", "Schramm et al. (2018)"
        names = self.last_names
        if self.type in ("norm", "standard") and self.number:
            who = self.number
        elif not names:
            who = self.organization or self.institution or self.title or self.id
        elif len(names) == 1:
            who = names[0]
        elif len(names) == 2:
            who = f"{names[0]} und {names[1]}"
        else:
            who = f"{names[0]} et al."
        inner = ", ".join(p for p in (self.year_text, locator) if p)
        return f"{who} ({inner})" if inner else who

    def full(self):
        # German bibliography entry
        parts = []
        if self.authors:
            parts.append("; ".join(abbreviate(a) for a in self.authors))
        elif self.organization:
            parts.append(self.organization)
        head = (parts[0] + " " if parts else "") + (f"({self.year_text})" if self.year_text else "")
        head = head.strip()
        title = self.title
        if self.type in ("norm", "standard") and self.number and self.number not in title:
            title = f"{self.number}: {title}"
        text = f"{head}: {title}" if head else title
        tail = []
        if self.venue:
            tail.append(f"In: {self.venue}")
        if self.edition:
            tail.append(f"{self.edition}")
        if self.series:
            tail.append(self.series)
        if self.type == "thesis":
            tail.append("Dissertation")
        if self.type == "report" and self.number:
            tail.append(f"Bericht {self.number}")
        for key in ("institution", "school", "publisher"):
            value = getattr(self, key)
            if value:
                tail.append(value)
        if self.organization and self.authors:
            tail.append(self.organization)
        if self.pages:
            tail.append(f"S. {self.pages}")
        if self.isbn:
            tail.append(f"ISBN {self.isbn}")
        if self.doi:
            tail.append(f"DOI {self.doi}")
        if self.url:
            tail.append(self.url)
        return text + (". " + ". ".join(tail) if tail else "") + "."

    def bibtex(self):
        entry_type = bibtex_type(self)
        fields_ = []
        if self.authors:
            names = ["others" if a.strip().lower() in ("et al.", "et al", "u. a.") else a for a in self.authors]
            fields_.append(("author", " and ".join(names)))
        fields_.append(("title", "{" + self.title + "}"))
        if self.year_text:
            fields_.append(("year", self.year_text))
        if self.venue:
            fields_.append(("booktitle" if entry_type == "inproceedings" else "journal" if entry_type == "article"
                            else "howpublished", self.venue))
        if entry_type in ("phdthesis", "mastersthesis"):
            school = self.school or self.institution or self.publisher
            if school:
                fields_.append(("school", school))
        else:
            if self.publisher:
                fields_.append(("publisher", self.publisher))
            if self.institution or (entry_type == "techreport" and self.organization):
                fields_.append(("institution", self.institution or self.organization))
            elif self.organization:
                fields_.append(("organization", self.organization))
        for key in ("edition", "volume", "number", "pages", "series", "address", "isbn", "doi", "url", "month"):
            value = getattr(self, key)
            if value:
                fields_.append((key, value))
        if self.notes:
            fields_.append(("note", self.notes))
        body = ",\n".join(f"  {k} = {{{_bib_escape(v, keep_braces=(k == 'title'))}}}" for k, v in fields_)
        return f"@{entry_type}{{{self.id},\n{body}\n}}"


def last_name(author):
    author = str(author).strip()
    if "," in author:
        return author.split(",")[0].strip()
    parts = author.split()
    if not parts:
        return author
    last = [parts[-1]]
    for p in reversed(parts[:-1]):
        if p.lower() in _PARTICLES:
            last.insert(0, p)
        else:
            break
    return " ".join(last)


def abbreviate(author):
    # "Moritz Werling" -> "Werling, M."; organizations (no blank) stay unchanged
    author = str(author).strip()
    if "," in author:
        last, first = [p.strip() for p in author.split(",", 1)]
    else:
        ln = last_name(author)
        first = author[: len(author) - len(ln)].strip()
        last = ln
    initials = " ".join(p[0] + "." for p in re.split(r"[\s\-]+", first) if p and p[0].isalpha())
    return f"{last}, {initials}" if initials else last


def bibtex_type(ref):
    if ref.type == "paper":
        venue = ref.venue.lower()
        if any(w in venue for w in ("conference", "proceedings", "symposium", "workshop", "congress", "tagung")):
            return "inproceedings"
        return "article"
    return {"book": "book", "thesis": "phdthesis", "report": "techreport", "standard": "misc", "norm": "misc",
            "documentation": "manual", "software": "misc"}.get(ref.type, "misc")


def _bib_escape(text, keep_braces=False):
    text = str(text)
    if not keep_braces:
        text = text.replace("{", "\\{").replace("}", "\\}")
    for ch in ("&", "%", "#", "_", "$"):
        text = re.sub(r"(?<!\\)" + re.escape(ch), "\\" + ch, text)
    return text


# ---------------------------------------------------------------------------- database
class ReferenceDB:
    def __init__(self, directory=None):
        self.directory = Path(directory) if directory is not None else references_dir()
        self.refs = {}             # id -> Reference
        self.links = []            # [{"reference", "target", "note"}]
        self.issues = []           # load/validation issues
        self.files = []
        self.load()

    # ------------------------------------------------------------------ loading
    def load(self):
        self.refs, self.links, self.issues, self.files = {}, [], [], []
        if not self.directory.is_dir():
            self.issues.append(Issue("warning", "-", f"Referenzordner fehlt: {self.directory.as_posix()}"))
            return self
        files = sorted(p for p in self.directory.glob("*.yaml") if p.name not in SPECIAL_FILES)
        files = [p for p in files if p.name != USER_FILE] + [p for p in files if p.name == USER_FILE]
        for path in files:
            data = self._read(path)
            if data is None:
                continue
            if not isinstance(data, dict):
                self.issues.append(Issue("error", "-", "Datei enthält keine Zuordnung id -> Eintrag", path.name))
                continue
            self.files.append(path.name)
            for ref_id, entry in data.items():
                ref_id = str(ref_id)
                if not isinstance(entry, dict):
                    self.issues.append(Issue("error", ref_id, "Eintrag ist keine Zuordnung", path.name))
                    continue
                if ref_id in self.refs:
                    self.issues.append(Issue("error", ref_id, f"doppelte ID (bereits in {self.refs[ref_id].source_file})",
                                             path.name))
                    continue
                try:
                    self.refs[ref_id] = Reference.from_dict(ref_id, entry, path.name, user=path.name == USER_FILE)
                except Exception as exc:  # malformed entry must not break the database
                    self.issues.append(Issue("error", ref_id, f"nicht lesbar: {exc}", path.name))
        links_path = self.directory / LINKS_FILE
        if links_path.exists():
            data = self._read(links_path) or {}
            for item in (data.get("links") or []) if isinstance(data, dict) else []:
                if isinstance(item, dict) and item.get("reference") and item.get("target"):
                    self.links.append({"reference": str(item["reference"]), "target": str(item["target"]),
                                       "note": str(item.get("note", "") or "")})
                else:
                    self.issues.append(Issue("warning", "-", f"ungültige Verknüpfung {item!r}", LINKS_FILE))
        self.issues.extend(self.validate())
        return self

    def _read(self, path):
        try:
            return yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError, UnicodeDecodeError) as exc:
            self.issues.append(Issue("error", "-", f"YAML nicht lesbar: {str(exc).splitlines()[0]}", path.name))
            return None

    # ------------------------------------------------------------------ validation
    def validate(self):
        issues = []
        for ref_id in sorted(self.refs):
            issues.extend(validate_reference(self.refs[ref_id]))
        for link in self.links:
            if link["reference"] not in self.refs:
                issues.append(Issue("warning", link["reference"], f"Verknüpfung auf unbekannte Referenz "
                                    f"(Ziel {link['target']})", LINKS_FILE))
        return issues

    def check_ids(self, ids):
        # ids that are used somewhere but not defined
        return sorted({str(i) for i in ids if i and str(i) not in self.refs})

    # ------------------------------------------------------------------ access
    def __contains__(self, ref_id):
        return ref_id in self.refs

    def __getitem__(self, ref_id):
        return self.refs[ref_id]

    def __len__(self):
        return len(self.refs)

    def __iter__(self):
        return iter(self.refs[k] for k in sorted(self.refs))

    def get(self, ref_id, default=None):
        return self.refs.get(ref_id, default)

    def cite(self, ref_id, locator="", style="short"):
        ref = self.refs.get(ref_id)
        if ref is None:
            return f"[{ref_id}?]"
        return ref.full() if style == "full" else ref.short(locator)

    def links_for(self, target=None, reference=None):
        out = [l for l in self.links if (target is None or l["target"] == target)
               and (reference is None or l["reference"] == reference)]
        return sorted(out, key=lambda l: (l["reference"], l["target"]))

    def search(self, query, types=None, limit=None):
        # ranked full-text search over id, title, authors, venue, notes, keywords, year
        tokens = [t for t in re.split(r"\s+", str(query).lower().strip()) if t]
        scored = []
        for ref in self:
            if types and ref.type not in types:
                continue
            if not tokens:
                scored.append((0, ref.id, ref))
                continue
            score = 0
            hay = {"id": ref.id.lower(), "title": ref.title.lower(), "authors": " ".join(ref.authors).lower(),
                   "venue": " ".join([ref.venue, ref.publisher, ref.organization, ref.number]).lower(),
                   "notes": " ".join([ref.notes] + ref.keywords).lower(), "year": ref.year_text}
            for tok in tokens:
                hit = 0
                if tok == hay["id"]:
                    hit += 10
                elif tok in hay["id"]:
                    hit += 5
                if tok in hay["title"]:
                    hit += 3
                if tok in hay["authors"]:
                    hit += 3
                if tok in hay["venue"]:
                    hit += 2
                if tok == hay["year"]:
                    hit += 2
                if tok in hay["notes"]:
                    hit += 1
                if hit == 0:
                    score = 0
                    break
                score += hit
            if score > 0:
                scored.append((-score, ref.id, ref))
        scored.sort(key=lambda x: (x[0], x[1]))
        result = [r for _, _, r in scored]
        return result[:limit] if limit else result

    def bibtex(self, ids=None):
        ids = sorted(self.refs) if ids is None else [i for i in ids if i in self.refs]
        return "\n\n".join(self.refs[i].bibtex() for i in ids) + ("\n" if ids else "")

    # ------------------------------------------------------------------ user references and links
    def add_user_reference(self, ref_id, data, overwrite=False):
        # create or update an entry in user.yaml; returns the new Reference (raises ValueError if invalid)
        ref_id = str(ref_id).strip()
        if not ID_PATTERN.match(ref_id):
            raise ValueError(f"ungültige ID '{ref_id}' (Buchstabe am Anfang, dann Buchstaben, Ziffern, _ . : -)")
        existing = self.refs.get(ref_id)
        if existing is not None and not existing.user:
            raise ValueError(f"ID '{ref_id}' ist bereits in {existing.source_file} vergeben")
        if existing is not None and not overwrite:
            raise ValueError(f"ID '{ref_id}' existiert bereits (überschreiben mit overwrite=True)")
        ref = Reference.from_dict(ref_id, data, USER_FILE, user=True)
        errors = [i for i in validate_reference(ref) if i.level == "error"]
        if errors:
            raise ValueError("; ".join(i.message for i in errors))
        user = self._read_user()
        user[ref_id] = ref.to_dict()
        self._write_yaml(self.directory / USER_FILE, user, "Benutzerdefinierte Referenzen (GUI-Reiter „Quellen“ "
                         "oder ReferenceDB.add_user_reference)")
        self.load()
        return self.refs[ref_id]

    def remove_user_reference(self, ref_id):
        user = self._read_user()
        if ref_id not in user:
            return False
        del user[ref_id]
        self._write_yaml(self.directory / USER_FILE, user, "Benutzerdefinierte Referenzen")
        self.load()
        return True

    def link(self, ref_id, target, note=""):
        # link a reference to a module / component / concept (stored in links.yaml)
        if ref_id not in self.refs:
            raise ValueError(f"unbekannte Referenz '{ref_id}'")
        target = str(target).strip()
        if not target:
            raise ValueError("leeres Verknüpfungsziel")
        links = [l for l in self.links if not (l["reference"] == ref_id and l["target"] == target)]
        links.append({"reference": ref_id, "target": target, "note": note})
        self._write_links(links)
        return links[-1]

    def unlink(self, ref_id, target):
        links = [l for l in self.links if not (l["reference"] == ref_id and l["target"] == target)]
        changed = len(links) != len(self.links)
        if changed:
            self._write_links(links)
        return changed

    def _write_links(self, links):
        items = [{k: v for k, v in l.items() if v != ""} for l in sorted(links, key=lambda l: (l["reference"], l["target"]))]
        self._write_yaml(self.directory / LINKS_FILE, {"links": items},
                         "Verknüpfungen Referenz -> Ziel (package:, module:, component:, concept:, class:, function:)")
        self.load()

    def _read_user(self):
        path = self.directory / USER_FILE
        if not path.exists():
            return {}
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            data = {}
        return data if isinstance(data, dict) else {}

    def _write_yaml(self, path, data, comment):
        self.directory.mkdir(parents=True, exist_ok=True)
        text = f"# {comment}\n" + yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=110)
        path.write_text(text, encoding="utf-8")


def validate_reference(ref):
    issues = []
    where = ref.source_file
    if not ID_PATTERN.match(ref.id):
        issues.append(Issue("error", ref.id, "ungültige ID", where))
    if ref.type not in REFERENCE_TYPES:
        issues.append(Issue("error", ref.id, f"unbekannter Typ '{ref.type}' (erlaubt: {', '.join(REFERENCE_TYPES)})",
                            where))
        return issues
    for req in REQUIRED_FIELDS[ref.type]:
        options = req if isinstance(req, tuple) else (req,)
        if not any(getattr(ref, o, None) not in (None, "", []) for o in options):
            issues.append(Issue("error", ref.id, f"Pflichtfeld fehlt: {' oder '.join(options)}", where))
    if ref.year_text and not re.match(r"^\d{4}[a-z]?$", ref.year_text):
        issues.append(Issue("warning", ref.id, f"ungewöhnliche Jahresangabe '{ref.year_text}'", where))
    if ref.doi and not ref.doi.startswith("10."):
        issues.append(Issue("warning", ref.id, f"DOI sollte mit '10.' beginnen ('{ref.doi}')", where))
    if ref.url and not re.match(r"^https?://", ref.url):
        issues.append(Issue("warning", ref.id, f"URL sollte mit http(s):// beginnen ('{ref.url}')", where))
    return issues


CITATION_PATTERN = re.compile(r"\[(@[^\[\]]+)\]")


def parse_citations(text):
    # "[@werling2011, Abschn. 3.4; @rajamani2012]" -> [("werling2011", "Abschn. 3.4"), ("rajamani2012", "")]
    out = []
    for match in CITATION_PATTERN.finditer(text or ""):
        for part in match.group(1).split(";"):
            part = part.strip()
            m = re.match(r"@([A-Za-z][A-Za-z0-9_.:\-]*)\s*,?\s*(.*)$", part)
            if m:
                out.append((m.group(1).rstrip(".,"), m.group(2).strip()))
    return out
