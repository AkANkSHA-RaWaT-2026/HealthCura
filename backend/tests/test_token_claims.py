from app.core.security import create_access_token, decode_access_token


def test_token_contains_user_id_and_no_role():
    token = create_access_token({"user_id": 7})
    payload = decode_access_token(token)

    assert payload["user_id"] == 7
    assert "role" not in payload