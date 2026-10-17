from app.auditlog.chain import GENESIS, make_entry, verify_chain


def build(n=4):
    entries, prev = [], GENESIS
    for i in range(n):
        e = make_entry(prev, "deed_verified", f"D{i}", {"i": i}, f"2024-01-01T00:0{i}:00+00:00")
        entries.append(e)
        prev = e["entry_hash"]
    return entries


def test_untouched_chain_verifies():
    r = verify_chain(build())
    assert r.ok and r.checked == 4


def test_editing_an_entry_breaks_the_chain():
    e = build()
    e[1]["payload_hash"] = "f" * 64
    r = verify_chain(e)
    assert not r.ok and r.broken_at == 1


def test_removing_a_middle_entry_breaks_the_chain():
    e = build()
    del e[1]
    assert not verify_chain(e).ok


def test_removing_the_first_entry_breaks_the_chain():
    e = build()
    del e[0]
    assert not verify_chain(e).ok


def test_reordering_breaks_the_chain():
    e = build()
    e[1], e[2] = e[2], e[1]
    assert not verify_chain(e).ok
