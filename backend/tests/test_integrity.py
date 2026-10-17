import pytest

from app.integrity.canonical import FIELDS, canonical_bytes, make_record, normalize_fields, record_hash
from app.integrity.qr import qr_png_base64, verify_url
from app.integrity.signing import Signer, generate_seed_b64
from app.integrity.verify import verify_copy


def sample():
    return make_record("DEED-1", "2024-03-10", "registered", "OWNER-A", "BUYER-B", "P-1", 5, "SRC-1")


def stored(signer, rec):
    h = record_hash(rec)
    return {"record": rec, "hash": h, "signature": signer.sign(h)}


def test_hash_is_deterministic_and_field_order_free():
    rec = sample()
    reordered = {k: rec[k] for k in reversed(FIELDS)}
    assert canonical_bytes(rec) == canonical_bytes(reordered)
    assert record_hash(rec) == record_hash(sample())


def test_area_and_date_are_normalised():
    a = normalize_fields({**sample(), "area_decimal": "5"})
    b = normalize_fields({**sample(), "area_decimal": "5.0000"})
    assert record_hash(a) == record_hash(b)


def test_genuine_copy_matches(signer):
    rec = sample()
    s = stored(signer, rec)
    r = verify_copy(signer, s, dict(rec), s["hash"], s["signature"])
    assert r["result"] == "match" and r["signature_valid"] and r["mismatched_fields"] == []


@pytest.mark.parametrize(
    "field,value",
    [
        ("area_decimal", "6.0000"),
        ("buyer", "BUYER-Z"),
        ("registration_date", "2024-03-11"),
        ("seller", "OWNER-A "),
        ("parcel_id", "P-2"),
    ],
)
def test_one_changed_field_fails_and_names_it(signer, field, value):
    rec = sample()
    s = stored(signer, rec)
    r = verify_copy(signer, s, {**rec, field: value}, s["hash"], s["signature"])
    assert r["result"] == "mismatch"
    assert field in r["mismatched_fields"]
    assert r["recomputed_hash"] != r["signed_hash"]


def test_forged_qr_hash_is_rejected(signer):
    rec = sample()
    s = stored(signer, rec)
    forged = {**rec, "buyer": "BUYER-Z"}
    r = verify_copy(signer, s, forged, record_hash(forged), s["signature"])  # attacker re-hashes the copy
    assert r["result"] == "mismatch" and r["qr_signature_valid"] is False


def test_signature_from_another_key_is_rejected(signer):
    rec = sample()
    s = stored(signer, rec)
    other = Signer(generate_seed_b64())
    assert not other.verify(s["hash"], s["signature"])


def test_unknown_deed_is_not_found(signer):
    assert verify_copy(signer, None, sample())["result"] == "not_found"


def test_bad_key_material_is_refused():
    with pytest.raises(ValueError):
        Signer("not base64 !!")
    with pytest.raises(ValueError):
        Signer("QUJD")  # decodes to 3 bytes, not 32


def test_qr_payload_and_png(signer):
    url = verify_url("http://localhost:5173", "DEED-1", "a" * 64, "sig")
    assert url.startswith("http://localhost:5173/verify?") and "ref=DEED-1" in url
    assert len(qr_png_base64(url)) > 100
