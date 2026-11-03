from app.services.dxf_export import concept_dxf


def _pairs(text):
    lines = text.splitlines()
    return list(zip(lines[0::2], lines[1::2]))


def test_dxf_has_valid_envelope_and_entities():
    dxf = concept_dxf(25, 60, 3, 15, "QuickService")
    pairs = _pairs(dxf)
    assert pairs[0] == ("0", "SECTION")
    assert pairs[-1] == ("0", "EOF")
    assert sum(1 for code, value in pairs if code == "0" and value == "LINE") >= 8
    assert sum(1 for code, value in pairs if code == "0" and value == "TEXT") == 4


def test_dxf_text_is_ascii_only():
    dxf = concept_dxf(25, 60, 3, 15, "Quick Service")
    assert all(ord(ch) < 128 for ch in dxf)
