import time
import uuid
from typing import Any

SANCTIONS_DB: dict[str, list[dict]] = {}

SANCTIONS_LISTS: dict[str, list[dict[str, Any]]] = {
    "OFAC_SDN": [
        {"name": "Ivan Kozlov", "entity_type": "individual", "program": "UKRAINE-EO13661", "country": "Russia", "sanction_date": "2022-03-01", "status": "active"},
        {"name": "NorthStar Shipping Co", "entity_type": "entity", "program": "NKSP", "country": "North Korea", "sanction_date": "2019-06-15", "status": "active"},
        {"name": "Global Trade Partners Ltd", "entity_type": "entity", "program": "IRAN", "country": "Iran", "sanction_date": "2020-11-20", "status": "active"},
        {"name": "Dmitri Volkov", "entity_type": "individual", "program": "UKRAINE-EO14024", "country": "Russia", "sanction_date": "2023-01-10", "status": "active"},
        {"name": "SyriaTel Communications", "entity_type": "entity", "program": "SYRIA", "country": "Syria", "sanction_date": "2018-04-05", "status": "active"},
        {"name": "Banco del Caribe", "entity_type": "entity", "program": "VENEZUELA", "country": "Venezuela", "sanction_date": "2021-08-12", "status": "active"},
        {"name": "Al-Sharif Trading", "entity_type": "entity", "program": "CT", "country": "Yemen", "sanction_date": "2022-05-30", "status": "active"},
        {"name": "Sergei Antonov", "entity_type": "individual", "program": "MAGNITSKY", "country": "Russia", "sanction_date": "2020-12-01", "status": "active"},
        {"name": "Titanium Mining Corp", "entity_type": "entity", "program": "BELARUS", "country": "Belarus", "sanction_date": "2023-02-14", "status": "active"},
        {"name": "Golden Star Resources", "entity_type": "entity", "program": "IRAN", "country": "Iran", "sanction_date": "2019-09-22", "status": "active"},
        {"name": "Myanmar Jade Enterprise", "entity_type": "entity", "program": "BURMA", "country": "Myanmar", "sanction_date": "2021-04-08", "status": "active"},
        {"name": "Quds Force Trading", "entity_type": "entity", "program": "IRGC", "country": "Iran", "sanction_date": "2020-07-19", "status": "active"},
        {"name": "Andrei Sokolov", "entity_type": "individual", "program": "CYBER", "country": "Russia", "sanction_date": "2022-11-15", "status": "active"},
        {"name": "Pacific Intertrade", "entity_type": "entity", "program": "NKSP", "country": "North Korea", "sanction_date": "2023-06-01", "status": "active"},
        {"name": "Alexei Morozov", "entity_type": "individual", "program": "UKRAINE-EO13661", "country": "Russia", "sanction_date": "2022-09-20", "status": "active"},
    ],
    "UN": [
        {"name": "Abdul Rahman Al-Makki", "entity_type": "individual", "program": "ISIL-DAESH", "country": "Iraq", "sanction_date": "2017-03-10", "status": "active"},
        {"name": "North Pearl Trading", "entity_type": "entity", "program": "DPRK", "country": "North Korea", "sanction_date": "2016-08-25", "status": "active"},
        {"name": "Houthi Arms Network", "entity_type": "entity", "program": "YEMEN", "country": "Yemen", "sanction_date": "2022-01-30", "status": "active"},
        {"name": "Libya National Oil Corp", "entity_type": "entity", "program": "LIBYA", "country": "Libya", "sanction_date": "2015-07-12", "status": "active"},
        {"name": "Al-Shabaab Finance", "entity_type": "entity", "program": "SOMALIA", "country": "Somalia", "sanction_date": "2020-10-05", "status": "active"},
        {"name": "Omar Hassan", "entity_type": "individual", "program": "SOMALIA", "country": "Somalia", "sanction_date": "2019-11-18", "status": "active"},
        {"name": "Taliban Financial Network", "entity_type": "entity", "program": "AFGHANISTAN", "country": "Afghanistan", "sanction_date": "2021-09-01", "status": "active"},
        {"name": "South Sudan Arms Corp", "entity_type": "entity", "program": "SOUTH_SUDAN", "country": "South Sudan", "sanction_date": "2022-06-20", "status": "active"},
    ],
    "EU": [
        {"name": "Russian National Wealth Fund", "entity_type": "entity", "program": "UKRAINE", "country": "Russia", "sanction_date": "2022-02-28", "status": "active"},
        {"name": "Belarus State Bank", "entity_type": "entity", "program": "BELARUS", "country": "Belarus", "sanction_date": "2022-03-15", "status": "active"},
        {"name": "Crimea Energy Co", "entity_type": "entity", "program": "CRIMEA", "country": "Crimea", "sanction_date": "2014-07-30", "status": "active"},
        {"name": "Siberia Oil Trading", "entity_type": "entity", "program": "UKRAINE", "country": "Russia", "sanction_date": "2023-04-25", "status": "active"},
    ],
    "UK": [
        {"name": "Evgeny Petrov", "entity_type": "individual", "program": "UKRAINE", "country": "Russia", "sanction_date": "2022-03-10", "status": "active"},
        {"name": "Minsk Industrial Group", "entity_type": "entity", "program": "BELARUS", "country": "Belarus", "sanction_date": "2022-05-20", "status": "active"},
        {"name": "Iranian Drone Corp", "entity_type": "entity", "program": "IRAN_DRONE", "country": "Iran", "sanction_date": "2023-01-05", "status": "active"},
        {"name": "Syrian Chemical Holdings", "entity_type": "entity", "program": "SYRIA_CHEM", "country": "Syria", "sanction_date": "2020-09-15", "status": "active"},
    ],
}

RESTRICTED_COUNTRIES: dict[str, dict[str, Any]] = {
    "Iran": {"restriction_type": "full", "programs": ["IRAN", "IRGC", "IRAN_DRONE"], "effective_date": "1979-11-14"},
    "North Korea": {"restriction_type": "full", "programs": ["NKSP", "DPRK"], "effective_date": "2008-06-26"},
    "Syria": {"restriction_type": "full", "programs": ["SYRIA", "SYRIA_CHEM"], "effective_date": "2011-04-29"},
    "Crimea": {"restriction_type": "full", "programs": ["CRIMEA"], "effective_date": "2014-12-19"},
    "Russia": {"restriction_type": "financial", "programs": ["UKRAINE-EO13661", "UKRAINE-EO14024", "UKRAINE"], "effective_date": "2022-02-24"},
    "Belarus": {"restriction_type": "financial", "programs": ["BELARUS"], "effective_date": "2022-03-02"},
    "Myanmar": {"restriction_type": "financial", "programs": ["BURMA"], "effective_date": "2021-02-10"},
    "Venezuela": {"restriction_type": "financial", "programs": ["VENEZUELA"], "effective_date": "2019-01-28"},
    "Yemen": {"restriction_type": "arms", "programs": ["YEMEN"], "effective_date": "2015-04-14"},
    "Afghanistan": {"restriction_type": "financial", "programs": ["AFGHANISTAN"], "effective_date": "2022-02-11"},
    "Iraq": {"restriction_type": "arms", "programs": ["ISIL-DAESH"], "effective_date": "2014-06-15"},
    "Libya": {"restriction_type": "arms", "programs": ["LIBYA"], "effective_date": "2011-02-26"},
    "Somalia": {"restriction_type": "arms", "programs": ["SOMALIA"], "effective_date": "2010-03-12"},
    "South Sudan": {"restriction_type": "arms", "programs": ["SOUTH_SUDAN"], "effective_date": "2015-04-01"},
    "Sudan": {"restriction_type": "arms", "programs": ["SUDAN"], "effective_date": "2018-05-15"},
}


class SanctionsEngine:
    def check_name(self, name: str) -> list[dict[str, Any]]:
        name_lower = name.lower()
        matches: list[dict[str, Any]] = []
        for list_name, entries in SANCTIONS_LISTS.items():
            for entry in entries:
                entry_name_lower = entry["name"].lower()
                if name_lower in entry_name_lower or entry_name_lower in name_lower:
                    matches.append({
                        "list": list_name,
                        "matched_entry": entry,
                        "match_type": "partial_name",
                        "confidence": 0.85 if name_lower != entry_name_lower else 1.0,
                        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    })
        check_record: dict[str, Any] = {
            "check_id": str(uuid.uuid4()),
            "query": name,
            "matches": matches,
            "total_matches": len(matches),
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        if "checks" not in SANCTIONS_DB:
            SANCTIONS_DB["checks"] = []
        SANCTIONS_DB["checks"].append(check_record)
        return matches

    def check_entity(self, entity_name: str, country: str) -> list[dict[str, Any]]:
        entity_lower = entity_name.lower()
        matches: list[dict[str, Any]] = []
        for list_name, entries in SANCTIONS_LISTS.items():
            for entry in entries:
                if entry["entity_type"] != "entity":
                    continue
                entry_lower = entry["name"].lower()
                if entity_lower in entry_lower or entry_lower in entity_lower:
                    matches.append({
                        "list": list_name,
                        "matched_entry": entry,
                        "country_match": entry["country"].lower() == country.lower(),
                        "confidence": 0.9 if entry["country"].lower() == country.lower() else 0.7,
                        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    })
        return matches

    def check_country(self, country: str) -> dict[str, Any]:
        country_info = RESTRICTED_COUNTRIES.get(country)
        if country_info:
            return {
                "country": country,
                "restricted": True,
                "restriction_type": country_info["restriction_type"],
                "programs": country_info["programs"],
                "effective_date": country_info["effective_date"],
                "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        return {
            "country": country,
            "restricted": False,
            "restriction_type": None,
            "programs": [],
            "effective_date": None,
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    def check_ip_address(self, ip: str) -> dict[str, Any]:
        restricted_ranges: dict[str, dict[str, Any]] = {
            "Iran": {"prefix": ["5.134.", "5.135.", "5.250.", "10."], "type": "full"},
            "North Korea": {"prefix": ["175.45."], "type": "full"},
            "Russia": {"prefix": ["5.3.", "5.8.", "5.23.", "31."], "type": "financial"},
            "China": {"prefix": ["1.0.", "1.1.", "1.2.", "14."], "type": "monitoring"},
        }
        results: list[dict[str, Any]] = []
        for country, cfg in restricted_ranges.items():
            for prefix in cfg["prefix"]:
                if ip.startswith(prefix):
                    results.append({
                        "country": country,
                        "ip": ip,
                        "matched_prefix": prefix,
                        "restriction_type": cfg["type"],
                        "risk": "high" if cfg["type"] == "full" else ("medium" if cfg["type"] == "financial" else "low"),
                    })
        return {
            "ip": ip,
            "restricted": len(results) > 0,
            "matches": results,
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    def get_restricted_countries(self) -> dict[str, dict[str, Any]]:
        return {k: dict(v) for k, v in RESTRICTED_COUNTRIES.items()}

    def get_sanctions_summary(self) -> dict[str, int]:
        return {name: len(entries) for name, entries in SANCTIONS_LISTS.items()}

    def create_demo_data(self):
        if "checks" in SANCTIONS_DB and SANCTIONS_DB["checks"]:
            return
        self.check_name("Ivan Kozlov")
        self.check_name("Acme Corporation")
        self.check_entity("NorthStar Shipping Co", "North Korea")
        self.check_entity("Global Trade Partners Ltd", "Iran")
        self.check_country("Iran")
        self.check_country("Canada")
        self.check_ip_address("5.134.220.15")
        self.check_ip_address("8.8.8.8")
