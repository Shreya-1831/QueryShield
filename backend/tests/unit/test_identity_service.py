from app.identity.identity_service import IdentityService


def test_windows_username():
    service = IdentityService()
    assert service.get_windows_username().lower()


def test_resolve_identity():
    service = IdentityService()
    identity = service.resolve()

    if identity:
        assert identity["employee_id"]
        assert identity["username"]
        assert identity["role"]