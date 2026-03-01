"""Tests for hash_lib.idempotency."""
import hashlib
import pytest
from hash_lib import get_idempotency_key


def test_get_idempotency_key_deterministic():
    a = get_idempotency_key("client", "ord-1", "COMPLETED")
    b = get_idempotency_key("client", "ord-1", "COMPLETED")
    assert a == b


def test_get_idempotency_key_format():
    key = get_idempotency_key("c", "o", "S")
    assert len(key) == 64
    assert all(c in "0123456789abcdef" for c in key)


def test_get_idempotency_key_different_inputs_different_output():
    k1 = get_idempotency_key("client-a", "ord-1", "COMPLETED")
    k2 = get_idempotency_key("client-b", "ord-1", "COMPLETED")
    k3 = get_idempotency_key("client-a", "ord-2", "COMPLETED")
    k4 = get_idempotency_key("client-a", "ord-1", "FAILED")
    assert len({k1, k2, k3, k4}) == 4


def test_get_idempotency_key_matches_sha256():
    client_ref, order_id, order_status = "ref", "id-1", "PENDING"
    expected = hashlib.sha256(f"{client_ref}|{order_id}|{order_status}".encode()).hexdigest()
    assert get_idempotency_key(client_ref, order_id, order_status) == expected
