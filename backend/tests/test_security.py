from app.security import hash_password, verify_password


def test_correct_password_is_verified():
    password_hash = hash_password("StrongPassword123!")

    assert verify_password(
        "StrongPassword123!",
        password_hash,
    ) is True


def test_incorrect_password_is_rejected():
    password_hash = hash_password("StrongPassword123!")

    assert verify_password(
        "WrongPassword123!",
        password_hash,
    ) is False


def test_same_password_produces_different_hashes():
    first_hash = hash_password("StrongPassword123!")
    second_hash = hash_password("StrongPassword123!")

    assert first_hash != second_hash

    assert verify_password("StrongPassword123!", first_hash)
    assert verify_password("StrongPassword123!", second_hash)


def test_malformed_hash_is_rejected():
    assert verify_password(
        "StrongPassword123!",
        "invalid-hash",
    ) is False