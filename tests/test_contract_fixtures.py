from __future__ import annotations

from system.control_tower.backend.contracts import (
    CONTRACTS,
    contract_manifest,
    load_golden_fixture,
    validate_contract_payload,
)


def test_manifest_represents_required_and_optional_fields() -> None:
    manifest = contract_manifest()

    assert set(manifest) == set(CONTRACTS)

    for contract_name, contract in CONTRACTS.items():
        entry = manifest[contract_name]
        assert entry["required_fields"] == list(contract.required_field_names)
        assert entry["optional_fields"] == list(contract.optional_field_names)
        assert entry["required_fields"]
        assert entry["optional_fields"]


def test_golden_fixtures_parse_and_validate() -> None:
    for contract_name, contract in CONTRACTS.items():
        payload = load_golden_fixture(contract_name)

        assert isinstance(payload, dict)
        assert payload["schema_name"] == contract_name
        assert payload["schema_version"] == contract.version

        validate_contract_payload(contract_name, payload)



def test_optional_fields_can_be_omitted_without_breaking_validation() -> None:
    for contract_name, contract in CONTRACTS.items():
        payload = load_golden_fixture(contract_name)
        missing_optional_fields = [
            field_name
            for field_name in contract.optional_field_names
            if field_name not in payload
        ]

        assert missing_optional_fields, f"fixture for {contract_name} should omit at least one optional field"

        minimal_payload = {
            key: value
            for key, value in payload.items()
            if key in contract.required_field_names
        }

        validate_contract_payload(contract_name, minimal_payload)


def test_parameter_export_contract_accepts_representative_exporter_payload() -> None:
    payload = {
        "schema_name": "parameter_export",
        "schema_version": "1.0.0",
        "export_id": "pe-12345-s0",
        "vessel_name": "ojinger-1",
        "body_name": "kerbin",
        "situation": "prelaunch",
        "ut": 12345.0,
        "mass_kg": 18600.0,
        "dry_mass_kg": 12100.0,
        "fuel_mass_kg": 6500.0,
        "available_thrust_kn": 420.0,
        "max_thrust_kn": 450.0,
        "isp_vac_s": 310.0,
        "isp_atm_s": 285.0,
        "altitude_m": 68.4,
        "surface_gravity_mps2": 9.81,
        "stage_index": 0,
        "pressure_pa": 101325.0,
        "temperature_k": 288.15,
        "vertical_speed_mps": 0.0,
        "resource_summary": [
            {
                "name": "liquidfuel",
                "amount": 180.0,
                "capacity": 180.0,
                "fill_ratio": 1.0,
                "mass_kg": 900.0,
            }
        ],
        "engine_summary": [
            {
                "name": "lv-t45",
                "available_thrust_kn": 420.0,
                "max_thrust_kn": 450.0,
                "vacuum_isp_s": 310.0,
                "sea_level_isp_s": 285.0,
                "thrust_limit_pct": 100.0,
                "ignition": True,
                "flameout": False,
                "mode": "single",
            }
        ],
        "note": "representative export_prams.ks payload",
    }

    validate_contract_payload("parameter_export", payload)
