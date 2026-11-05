"""Service wrappers tested against fakes: no network, no Azure."""

import json
from types import SimpleNamespace

import pytest
from azure.core.exceptions import ResourceExistsError

from kiosk import config
from kiosk.services import face, storage


class FakeContainer:
    def __init__(self):
        self.blobs = {}

    def upload_blob(self, name, data, overwrite=False):
        self.blobs[name] = data if isinstance(data, bytes) else data.read()

    def list_blobs(self):
        return [SimpleNamespace(name=n) for n in sorted(self.blobs)]


class FakeBlobService:
    def __init__(self, existing=()):
        self.containers = {name: FakeContainer() for name in existing}

    def create_container(self, name):
        if name in self.containers:
            raise ResourceExistsError("exists")
        self.containers[name] = FakeContainer()

    def get_container_client(self, name):
        return self.containers.setdefault(name, FakeContainer())


def test_ensure_containers_creates_only_missing():
    client = FakeBlobService(existing=["manifest"])
    created = storage.ensure_containers(client)
    assert "manifest" not in created
    assert set(created) | {"manifest"} == set(storage.CONTAINERS)


def test_upload_file_and_json_round_trip(tmp_path):
    client = FakeBlobService()
    path = tmp_path / "m.csv"
    path.write_text("a,b\n")
    assert storage.upload_file(client, "manifest", path) == "m.csv"
    storage.upload_json(client, "kiosk-results", "r.json", {"ok": True})
    assert storage.list_blobs(client, "manifest") == ["m.csv"]
    assert json.loads(client.containers["kiosk-results"].blobs["r.json"]) == {"ok": True}


def test_unknown_container_is_rejected():
    with pytest.raises(ValueError):
        storage.container(FakeBlobService(), "secrets")


def test_missing_setting_fails_fast(monkeypatch):
    monkeypatch.delenv("NOT_A_REAL_SETTING", raising=False)
    with pytest.raises(config.MissingSetting, match="NOT_A_REAL_SETTING"):
        config.setting("NOT_A_REAL_SETTING")
    assert config.setting("NOT_A_REAL_SETTING", "fallback") == "fallback"


class FakeResponse:
    def __init__(self, status=200, payload=None):
        self.status_code = status
        self._payload = payload
        self.content = b"" if payload is None else json.dumps(payload).encode()
        self.text = self.content.decode()

    def json(self):
        return self._payload


@pytest.fixture
def face_env(monkeypatch):
    monkeypatch.setenv("FACE_ENDPOINT", "https://face.example/")
    monkeypatch.setenv("FACE_KEY", "test-key")
    calls = []

    def fake_request(method, url, timeout, **kwargs):
        calls.append((method, url.split("face/v1.2/")[1], kwargs))
        path = url.split("face/v1.2/")[1]
        if path == "detect":
            return FakeResponse(payload=[{"faceId": "id-face", "faceRectangle": {"width": 5, "height": 5}}])
        if path == "verify":
            return FakeResponse(payload={"isIdentical": True, "confidence": 0.91})
        if path == "identify":
            return FakeResponse(payload=[{"candidates": [{"personId": "p1", "confidence": 0.95}]}])
        if path.endswith("/persons"):
            return FakeResponse(payload={"personId": "p1"})
        if path.endswith("/training"):
            return FakeResponse(payload={"status": "succeeded"})
        if path.endswith("persistedfaces") and kwargs.get("data") == b"bad":
            return FakeResponse(status=400, payload={"error": "no face"})
        return FakeResponse(payload={})

    monkeypatch.setattr(face.requests, "request", fake_request)
    monkeypatch.setattr(face.requests, "get", lambda url, headers, timeout: FakeResponse(status=404))
    return calls


def test_detect_sends_key_and_models(face_env):
    assert face.detect(b"img")[0]["faceId"] == "id-face"
    method, path, kwargs = face_env[0]
    assert (method, path) == ("POST", "detect")
    assert kwargs["headers"]["Ocp-Apim-Subscription-Key"] == "test-key"
    assert kwargs["params"]["recognitionModel"] == face.RECOGNITION_MODEL


def test_verify_and_identify(face_env):
    assert face.verify("a", "b")["confidence"] == 0.91
    assert face.identify("g", "a")[0]["candidates"][0]["confidence"] == 0.95


def test_build_person_group_skips_bad_frames(face_env):
    person_id, added = face.build_person_group("g", "Avkash", [b"good", b"bad", b"good"])
    assert (person_id, added) == ("p1", 2)
    assert ("POST", "persongroups/g/train") in [(m, p) for m, p, _ in face_env]


def test_build_person_group_without_usable_frames_raises(face_env):
    with pytest.raises(face.FaceError, match="no usable face frames"):
        face.build_person_group("g", "Avkash", [b"bad"])


def test_http_error_becomes_face_error(monkeypatch):
    monkeypatch.setenv("FACE_ENDPOINT", "https://face.example/")
    monkeypatch.setenv("FACE_KEY", "k")
    monkeypatch.setattr(face.requests, "request", lambda *a, **k: FakeResponse(status=403, payload={"error": "denied"}))
    with pytest.raises(face.FaceError, match="403"):
        face.detect(b"img")
