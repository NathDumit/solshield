"""Blocklist used by the SolShield risk engine: official sanctions list (live, with a local backup) plus the team's list."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import denuncias  # noqa: E402

BASE58 = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")


@pytest.fixture(autouse=True)
def fresh_cache(monkeypatch):
    monkeypatch.setattr(denuncias, "_cache", None)


def test_backup_copy_has_valid_base58_solana_addresses():
    assert denuncias.COPIA_OFAC
    for addr in denuncias.COPIA_OFAC:
        assert 32 <= len(addr) <= 44 and set(addr) <= BASE58


def test_falls_back_to_the_backup_when_offline_and_merges_the_team_list(monkeypatch):
    def offline():
        raise OSError("no network")
    monkeypatch.setattr(denuncias, "_baixar_ofac", offline)
    monkeypatch.setattr(denuncias, "DENUNCIADAS", {"TeamAddress": "team list"})
    todas = denuncias.todas()
    assert set(denuncias.COPIA_OFAC) <= set(todas) and todas["TeamAddress"] == "team list"
    assert all(todas[a] == denuncias.MOTIVO_OFAC for a in denuncias.COPIA_OFAC)


def test_an_empty_live_answer_also_uses_the_backup(monkeypatch):
    monkeypatch.setattr(denuncias, "_baixar_ofac", lambda: [])
    assert set(denuncias.todas()) == set(denuncias.COPIA_OFAC)


def test_live_list_is_used_when_available_and_cached(monkeypatch):
    calls = []
    monkeypatch.setattr(denuncias, "_baixar_ofac", lambda: calls.append(1) or ["L" * 44])
    assert "L" * 44 in denuncias.todas() and "L" * 44 in denuncias.todas()
    assert len(calls) == 1                                    # downloaded once per process


def test_team_list_wins_over_the_official_reason_for_the_same_address(monkeypatch):
    addr = denuncias.COPIA_OFAC[0]
    monkeypatch.setattr(denuncias, "_baixar_ofac", lambda: [addr])
    monkeypatch.setattr(denuncias, "DENUNCIADAS", {addr: "our own reason"})
    assert denuncias.todas()[addr] == "our own reason"


def test_download_filter_keeps_only_valid_addresses(monkeypatch):
    class Resp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return ("A" * 44 + " not-an-address 0OIl" + "1" * 40 + " " + "B" * 20).encode()
    monkeypatch.setattr(denuncias.urllib.request, "urlopen", lambda *a, **k: Resp())
    assert denuncias._baixar_ofac() == ["A" * 44]             # wrong length or non-base58 characters are dropped


# ---------------------------------------------------------------- how the risk engine uses it
def test_engine_warns_instead_of_silently_skipping_a_missing_blocklist(monkeypatch, caplog):
    import solana_rpc
    monkeypatch.setitem(sys.modules, "denuncias", None)          # makes `from denuncias import todas` fail
    with caplog.at_level("WARNING", logger="solshield"):
        assert solana_rpc._denunciadas() == {}
    assert "indisponível" in caplog.text


def test_engine_uses_the_blocklist_when_present(monkeypatch):
    import solana_rpc
    monkeypatch.setattr(denuncias, "_baixar_ofac", lambda: [])
    monkeypatch.setitem(sys.modules, "denuncias", denuncias)
    assert set(solana_rpc._denunciadas()) >= set(denuncias.COPIA_OFAC)
