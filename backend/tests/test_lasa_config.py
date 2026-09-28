"""
Phase 10 Tests: LASA Config.
Tests configuration, defaults, hashing, and Tall Man pair integrity.
"""

import pytest
from ai.lasa.config import LasaConfig, get_default_lasa_config, TALL_MAN_PAIRS


class TestLasaConfig:
    """Tests for LASA configuration model."""

    def test_defaults(self):
        config = LasaConfig()
        assert config.orthographic_threshold == 0.70
        assert config.phonetic_threshold == 0.75
        assert config.combined_threshold == 0.65
        assert config.orthographic_weight == 0.50
        assert config.phonetic_weight == 0.50
        assert config.high_risk_threshold == 0.85
        assert config.medium_risk_threshold == 0.70
        assert config.known_pair_risk_override == "high"
        assert config.max_confusable_candidates == 5
        assert config.policy_version == "lasa_policy_v1"

    def test_config_hash_deterministic(self):
        c1 = LasaConfig()
        c2 = LasaConfig()
        assert c1.config_hash() == c2.config_hash()

    def test_config_hash_changes_with_params(self):
        c1 = LasaConfig()
        c2 = LasaConfig(orthographic_threshold=0.80)
        assert c1.config_hash() != c2.config_hash()

    def test_config_hash_is_sha256(self):
        config = LasaConfig()
        h = config.config_hash()
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_custom_thresholds(self):
        config = LasaConfig(
            orthographic_threshold=0.50,
            phonetic_threshold=0.50,
            combined_threshold=0.40,
        )
        assert config.orthographic_threshold == 0.50
        assert config.combined_threshold == 0.40

    def test_threshold_bounds(self):
        with pytest.raises(Exception):
            LasaConfig(orthographic_threshold=1.5)
        with pytest.raises(Exception):
            LasaConfig(orthographic_threshold=-0.1)


class TestGetDefaultLasaConfig:
    """Tests for the singleton config accessor."""

    def test_returns_config(self):
        config = get_default_lasa_config()
        assert isinstance(config, LasaConfig)

    def test_singleton(self):
        c1 = get_default_lasa_config()
        c2 = get_default_lasa_config()
        assert c1 is c2


class TestTallManPairs:
    """Tests for the curated ISMP Tall Man pairs list."""

    def test_not_empty(self):
        assert len(TALL_MAN_PAIRS) > 0

    def test_all_tuples_have_four_elements(self):
        for pair in TALL_MAN_PAIRS:
            assert len(pair) == 4, f"Pair {pair} does not have 4 elements"

    def test_drug_names_are_lowercase(self):
        for pair in TALL_MAN_PAIRS:
            assert pair[0] == pair[0].lower(), f"Drug A '{pair[0]}' is not lowercase"
            assert pair[1] == pair[1].lower(), f"Drug B '{pair[1]}' is not lowercase"

    def test_tall_man_contains_uppercase(self):
        for pair in TALL_MAN_PAIRS:
            # At least one uppercase letter in tall man lettering
            assert any(c.isupper() for c in pair[2]), f"Tall Man A '{pair[2]}' has no uppercase"
            assert any(c.isupper() for c in pair[3]), f"Tall Man B '{pair[3]}' has no uppercase"

    def test_no_duplicate_pairs(self):
        seen = set()
        for pair in TALL_MAN_PAIRS:
            key = tuple(sorted([pair[0], pair[1]]))
            assert key not in seen, f"Duplicate pair: {pair[0]}, {pair[1]}"
            seen.add(key)

    def test_metformin_metronidazole_present(self):
        found = False
        for pair in TALL_MAN_PAIRS:
            if "metformin" in pair[0] and "metronidazole" in pair[1]:
                found = True
                break
        assert found, "Metformin/Metronidazole pair not found in TALL_MAN_PAIRS"

    def test_prednisolone_prednisone_present(self):
        found = False
        for pair in TALL_MAN_PAIRS:
            if set([pair[0], pair[1]]) == {"prednisolone", "prednisone"}:
                found = True
                break
        assert found, "Prednisolone/Prednisone pair not found"
