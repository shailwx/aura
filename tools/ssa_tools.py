"""SSA Tools — Statens standardavtaler (Norwegian State Standard Agreements).

Implements the three Norwegian DFØ standard IT procurement contract type
classification, compliance validation per FOA §5-3, and contract summary
generation.

Reference: https://www.dfo.no/standardavtaler
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

# FOA §5-3 competitive tender threshold
FOA_TENDER_THRESHOLD_NOK = 500_000.0
NOK_USD_RATE = 11.0  # approximate rate: 1 USD = 11 NOK
FOA_TENDER_THRESHOLD_USD = FOA_TENDER_THRESHOLD_NOK / NOK_USD_RATE  # ~45,454.55

_ORG_NUMBER_PATTERN = re.compile(r"^\d{9}$")

# EEA country codes (EU-27 + Iceland, Liechtenstein, Norway + UK post-Brexit)
_EEA_COUNTRY_CODES: frozenset[str] = frozenset({
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
    "DE", "GR", "HU", "IS", "IE", "IT", "LV", "LI", "LT", "LU",
    "MT", "NL", "NO", "PL", "PT", "RO", "SK", "SI", "ES", "SE", "GB",
})

_SSA_TYPES: dict[str, dict[str, Any]] = {
    "SSA-K": {
        "name": "SSA-K — Kjøp av IKT-utstyr (Hardware Purchase)",
        "category": "hardware",
        "is_recurring": False,
        "is_cloud": False,
        "is_development": False,
        "is_agile": False,
        "is_complex": False,
        "reference_url": "https://www.dfo.no/avtaler-og-innkjop/statens-standardavtaler/ssa-k",
        "annexes": [
            "Bilag 1: Kundens kravspesifikasjon",
            "Bilag 2: Leverandørens løsningsbeskrivelse",
            "Bilag 3: Prosjekt- og fremdriftsplan",
            "Bilag 4: Pris og betalingsbestemmelser",
        ],
        "companion_contracts": [],
    },
    "SSA-L": {
        "name": "SSA-L — Lisenser og programvare (Software/SaaS Licenses)",
        "category": "software_licenses",
        "is_recurring": True,
        "is_cloud": False,
        "is_development": False,
        "is_agile": False,
        "is_complex": False,
        "reference_url": "https://www.dfo.no/avtaler-og-innkjop/statens-standardavtaler/ssa-l",
        "annexes": [
            "Bilag 1: Kundens kravspesifikasjon",
            "Bilag 2: Leverandørens løsningsbeskrivelse",
            "Bilag 4: Pris og betalingsbestemmelser",
            "Bilag 5: Endringer i den generelle avtaleteksten",
        ],
        "companion_contracts": ["SSA-D"],
    },
    "SSA-D": {
        "name": "SSA-D — Driftsavtale (Managed Operations)",
        "category": "managed_services",
        "is_recurring": True,
        "is_cloud": False,
        "is_development": False,
        "is_agile": False,
        "is_complex": False,
        "reference_url": "https://www.dfo.no/avtaler-og-innkjop/statens-standardavtaler/ssa-d",
        "annexes": [
            "Bilag 1: Kundens kravspesifikasjon",
            "Bilag 2: Leverandørens løsningsbeskrivelse",
            "Bilag 3: Tjenestenivå (SLA)",
            "Bilag 4: Pris og betalingsbestemmelser",
        ],
        "companion_contracts": ["SSA-L"],
    },
    "SSA-B": {
        "name": "SSA-B — Bistandsavtale (IT Consulting)",
        "category": "consulting",
        "is_recurring": False,
        "is_cloud": False,
        "is_development": False,
        "is_agile": False,
        "is_complex": False,
        "reference_url": "https://www.dfo.no/avtaler-og-innkjop/statens-standardavtaler/ssa-b",
        "annexes": [
            "Bilag 1: Kundens kravspesifikasjon",
            "Bilag 2: Leverandørens løsningsbeskrivelse",
            "Bilag 4: Pris og betalingsbestemmelser",
        ],
        "companion_contracts": [],
    },
    "SSA-T": {
        "name": "SSA-T — Tjenestekontrakt (Service Contract)",
        "category": "services",
        "is_recurring": True,
        "is_cloud": False,
        "is_development": False,
        "is_agile": False,
        "is_complex": False,
        "reference_url": "https://www.dfo.no/avtaler-og-innkjop/statens-standardavtaler/ssa-t",
        "annexes": [
            "Bilag 1: Kundens kravspesifikasjon",
            "Bilag 2: Leverandørens løsningsbeskrivelse",
            "Bilag 3: Tjenestenivå (SLA)",
            "Bilag 4: Pris og betalingsbestemmelser",
        ],
        "companion_contracts": [],
    },
    "SSA-S": {
        "name": "SSA-S — Smidig systemutvikling (Agile Development)",
        "category": "agile_development",
        "is_recurring": True,
        "is_cloud": False,
        "is_development": True,
        "is_agile": True,
        "is_complex": False,
        "reference_url": "https://www.dfo.no/avtaler-og-innkjop/statens-standardavtaler/ssa-s",
        "annexes": [
            "Bilag 1: Kundens overordnede kravspesifikasjon",
            "Bilag 2: Administrative bestemmelser",
            "Bilag 3: Samlet pris og prisbestemmelser",
            "Bilag 4: Løsningsbeskrivelse",
        ],
        "companion_contracts": [],
    },
    "SSA-V": {
        "name": "SSA-V — Vedlikeholds- og supportavtale (Maintenance & Support)",
        "category": "maintenance",
        "is_recurring": True,
        "is_cloud": False,
        "is_development": False,
        "is_agile": False,
        "is_complex": False,
        "reference_url": "https://www.dfo.no/avtaler-og-innkjop/statens-standardavtaler/ssa-v",
        "annexes": [
            "Bilag 1: Systemer som vedlikeholdes",
            "Bilag 3: Tjenestenivå (SLA)",
            "Bilag 4: Pris og betalingsbestemmelser",
        ],
        "companion_contracts": ["SSA-L"],
    },
    "SSA-sky-liten": {
        "name": "SSA-sky-liten — Skytjenester (Small/Standard Cloud Services)",
        "category": "hosting",
        "is_recurring": True,
        "is_cloud": True,
        "is_development": False,
        "is_agile": False,
        "is_complex": False,
        "reference_url": "https://www.dfo.no/avtaler-og-innkjop/statens-standardavtaler/ssa-sky",
        "annexes": [
            "Bilag 1: Kundens kravspesifikasjon",
            "Bilag 2: Leverandørens løsningsbeskrivelse",
            "Bilag 3: Tjenestenivå (SLA)",
            "Bilag 4: Pris og betalingsbestemmelser",
        ],
        "companion_contracts": [],
    },
    "SSA-sky-stor": {
        "name": "SSA-sky-stor — Komplekse skytjenester (Complex/Large Cloud Services)",
        "category": "cloud_infrastructure",
        "is_recurring": True,
        "is_cloud": True,
        "is_development": False,
        "is_agile": False,
        "is_complex": True,
        "reference_url": "https://www.dfo.no/avtaler-og-innkjop/statens-standardavtaler/ssa-sky",
        "annexes": [
            "Bilag 1: Kundens kravspesifikasjon",
            "Bilag 2: Leverandørens løsningsbeskrivelse",
            "Bilag 3: Tjenestenivå (SLA)",
            "Bilag 4: Pris og betalingsbestemmelser",
            "Bilag 5: Særskilte sikkerhetskrav",
        ],
        "companion_contracts": [],
    },
}


def classify_ssa_type(
    category: str,
    is_recurring: bool = False,
    is_cloud: bool = False,
    is_development: bool = False,
    is_agile: bool = False,
    is_complex: bool = False,
) -> dict[str, Any]:
    """Classify the appropriate SSA contract type for a procurement.

    Scores each SSA type based on category match (+3 points) and boolean
    attribute matches (+2 points each), returning the best match.

    Args:
        category: Procurement category (e.g. "hardware", "consulting", "hosting").
        is_recurring: True if the contract involves recurring subscription/service.
        is_cloud: True if the procurement is cloud-based.
        is_development: True if the procurement involves software development.
        is_agile: True if the development uses agile/scrum methodology.
        is_complex: True if the cloud service is complex/enterprise-grade.

    Returns:
        Dict with ssa_type, name, reference_url, annexes, companion_contracts, score.
    """
    best_type = "SSA-K"
    best_score = -1

    flags = {
        "is_recurring": is_recurring,
        "is_cloud": is_cloud,
        "is_development": is_development,
        "is_agile": is_agile,
        "is_complex": is_complex,
    }

    for ssa_type, meta in _SSA_TYPES.items():
        score = 0
        if meta["category"] == category:
            score += 3
        for flag, value in flags.items():
            if value and meta[flag]:
                score += 2
        if score > best_score:
            best_score = score
            best_type = ssa_type

    meta = _SSA_TYPES[best_type]
    return {
        "ssa_type": best_type,
        "name": meta["name"],
        "reference_url": meta["reference_url"],
        "annexes": meta["annexes"],
        "companion_contracts": meta["companion_contracts"],
        "score": best_score,
    }


def validate_ssa_compliance(
    ssa_type: str,
    vendor: dict[str, Any],
    amount_usd: float,
) -> dict[str, Any]:
    """Validate SSA compliance for a vendor and procurement amount.

    Checks:
    1. Norwegian org number (9-digit Brønnøysund registry ID) — required for
       Norwegian vendors; EEA vendors get a warning; non-EEA vendors get a
       violation.
    2. FOA §5-3 competitive tender threshold (500,000 NOK ≈ 45,455 USD) —
       amounts above this threshold require a competitive tender process.

    Args:
        ssa_type: SSA contract type (e.g. "SSA-K", "SSA-L").
        vendor: Vendor dict with at minimum: name (str), country (str),
                org_number (str | None).
        amount_usd: Transaction amount in USD.

    Returns:
        Dict with compliant (bool), violations (list[str]), warnings (list[str]),
        and ssa_compliance_hash (str).
    """
    violations: list[str] = []
    warnings: list[str] = []

    if ssa_type not in _SSA_TYPES:
        violations.append(
            f"Unknown SSA type '{ssa_type}'. "
            f"Valid types: {', '.join(_SSA_TYPES)}"
        )

    org_number: str | None = vendor.get("org_number")
    country: str = vendor.get("country", "").upper()

    if country == "NO":
        if not org_number or not _ORG_NUMBER_PATTERN.fullmatch(str(org_number)):
            violations.append(
                "Norwegian vendor missing valid 9-digit org number "
                "(Brønnøysundregisteret). FOA §5-1 requirement."
            )
    elif country in _EEA_COUNTRY_CODES:
        if not org_number or not _ORG_NUMBER_PATTERN.fullmatch(str(org_number)):
            warnings.append(
                f"EEA vendor ({country}) lacks Norwegian org number. "
                "Cross-border procurement may require additional documentation."
            )
    else:
        if not org_number:
            violations.append(
                f"Non-EEA vendor ({country}) has no org number. "
                "Manual due diligence required under FOA §5-2."
            )

    if amount_usd > FOA_TENDER_THRESHOLD_USD:
        amount_nok = amount_usd * NOK_USD_RATE
        warnings.append(
            f"Amount {amount_usd:.2f} USD ({amount_nok:,.0f} NOK) exceeds "
            f"FOA §5-3 competitive tender threshold of "
            f"{FOA_TENDER_THRESHOLD_NOK:,.0f} NOK "
            f"({FOA_TENDER_THRESHOLD_USD:.2f} USD). "
            "Ensure competitive tender process was followed."
        )

    compliant = len(violations) == 0

    hash_input = (
        f"{ssa_type}:{vendor.get('name', '')}:{vendor.get('country', '')}:"
        f"{org_number}:{amount_usd}:{compliant}"
    )
    ssa_compliance_hash = hashlib.sha256(hash_input.encode()).hexdigest()

    return {
        "compliant": compliant,
        "violations": violations,
        "warnings": warnings,
        "ssa_compliance_hash": ssa_compliance_hash,
    }


def generate_ssa_contract_summary(
    ssa_type: str,
    vendor: dict[str, Any],
    mandate: dict[str, Any],
) -> dict[str, Any]:
    """Generate a structured SSA contract summary post-settlement.

    Produces a human-readable and machine-parseable contract summary
    that can be attached to the settlement record.

    Args:
        ssa_type: SSA contract type (e.g. "SSA-K").
        vendor: Vendor dict with name, country, org_number.
        mandate: Settled IntentMandate dict.

    Returns:
        Dict with contract_type, contract_name, reference_url, annexes,
        companion_contracts, foa_compliant, contract_parties,
        procurement_details.
    """
    meta = _SSA_TYPES.get(ssa_type, _SSA_TYPES["SSA-K"])
    constraints = mandate.get("constraints", {}) if isinstance(mandate, dict) else {}
    amount = constraints.get("amount", 0.0)
    currency = constraints.get("currency", "USD")
    amount_usd = amount if currency == "USD" else amount
    foa_compliant = amount_usd <= FOA_TENDER_THRESHOLD_USD

    return {
        "contract_type": ssa_type,
        "contract_name": meta["name"],
        "reference_url": meta["reference_url"],
        "annexes": meta["annexes"],
        "companion_contracts": meta["companion_contracts"],
        "foa_compliant": foa_compliant,
        "foa_threshold_nok": FOA_TENDER_THRESHOLD_NOK,
        "contract_parties": {
            "buyer": "Norwegian Government Entity",
            "seller": {
                "name": vendor.get("name", ""),
                "country": vendor.get("country", ""),
                "org_number": vendor.get("org_number"),
            },
        },
        "procurement_details": {
            "amount": amount,
            "currency": currency,
            "mandate_id": mandate.get("id", "") if isinstance(mandate, dict) else "",
            "settlement_id": mandate.get("settlement_id", "") if isinstance(mandate, dict) else "",
        },
    }
