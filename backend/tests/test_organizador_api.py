# Regression tests for Organizador de Etiquetas API (jobs, corrections, download, settings, reanalyze)
import os
import pymupdf
import pytest
import requests

def _base():
    url = os.environ.get("REACT_APP_BACKEND_URL")
    if not url:
        for line in open("/app/frontend/.env"):
            if line.startswith("REACT_APP_BACKEND_URL="):
                url = line.split("=", 1)[1].strip()
    return url.rstrip("/")

BASE_URL = _base()
PDF = "/tmp/e.pdf"
EXPECTED_REVIEW_PAGES = {36, 43, 45, 67}  # 1-based


@pytest.fixture(scope="module")
def s():
    return requests.Session()


@pytest.fixture(scope="module")
def created():
    ids = []
    yield ids
    for i in ids:
        requests.delete(f"{BASE_URL}/api/jobs/{i}")
    requests.post(f"{BASE_URL}/api/settings/reset")


@pytest.fixture(scope="module")
def job(s, created):
    requests.post(f"{BASE_URL}/api/settings/reset")
    with open(PDF, "rb") as f:
        r = s.post(f"{BASE_URL}/api/jobs", files={"file": ("TEST_e.pdf", f, "application/pdf")},
                   data={"user_name": "TEST_user"}, timeout=180)
    assert r.status_code == 200, r.text
    j = r.json()
    created.append(j["id"])
    return j


def _page_texts(data):
    d = pymupdf.open(stream=data, filetype="pdf")
    t = [p.get_text() for p in d]
    d.close()
    return t


# --- Job creation / analysis
class TestJobCreate:
    def test_counts(self, job):
        assert job["total_pages"] == 67
        assert job["labels_count"] == 67
        assert job["classified"] == 63
        assert job["review"] == 4
        assert job["integrity"] == {"original_pages": 67, "final_pages": 67, "ok": True}
        assert job["user_name"] == "TEST_user"
        assert job["filename"] == "TEST_e.pdf"
        assert job["file_available"] is True
        assert "_id" not in job

    def test_review_pages(self, job):
        rev = {l["pages"][0] + 1 for l in job["labels"] if l["status"] != "ok"}
        assert rev == EXPECTED_REVIEW_PAGES
        for l in job["labels"]:
            if l["status"] != "ok":
                assert l["reasons"], l

    def test_review_at_end_and_sorted(self, job):
        po = job["page_order"]
        assert sorted(po) == list(range(67))
        assert set(p + 1 for p in po[-4:]) == EXPECTED_REVIEW_PAGES

    def test_reject_txt_renamed_pdf(self, s):
        r = s.post(f"{BASE_URL}/api/jobs", files={"file": ("TEST_fake.pdf", b"hello world", "application/pdf")})
        assert r.status_code == 400

    def test_reject_wrong_extension(self, s):
        with open(PDF, "rb") as f:
            r = s.post(f"{BASE_URL}/api/jobs", files={"file": ("TEST_e.txt", f.read(2048), "text/plain")})
        assert r.status_code == 400


# --- Download
class TestDownload:
    def test_download_order(self, s, job):
        r = s.get(f"{BASE_URL}/api/jobs/{job['id']}/download", timeout=120)
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("application/pdf")
        out = _page_texts(r.content)
        orig = _page_texts(open(PDF, "rb").read())
        assert len(out) == 67
        for pos, src in enumerate(job["page_order"]):
            assert out[pos] == orig[src], f"pos {pos} != orig {src}"

    def test_download_404(self, s):
        assert s.get(f"{BASE_URL}/api/jobs/nope/download").status_code == 404


# --- Manual correction
class TestCorrection:
    def test_correct_and_remove(self, s, job):
        idx = next(l["idx"] for l in job["labels"] if l["status"] != "ok")
        body = {"brand": "CMC", "quality": "ECON", "color": "Gelo", "size_value": 5, "size_unit": "KG"}
        r = s.put(f"{BASE_URL}/api/jobs/{job['id']}/labels/{idx}", json=body)
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["review"] == 3 and j["classified"] == 64
        assert j["labels"][idx]["status"] == "ok"
        assert j["page_order"] != job["page_order"]
        g = s.get(f"{BASE_URL}/api/jobs/{job['id']}").json()
        assert g["review"] == 3 and g["labels"][idx]["manual"]["brand"] == "CMC"
        r = s.put(f"{BASE_URL}/api/jobs/{job['id']}/labels/{idx}", json={})
        j = r.json()
        assert j["review"] == 4 and j["labels"][idx]["manual"] is None
        assert j["page_order"] == job["page_order"]

    def test_unknown_brand_stays_review(self, s, job):
        idx = next(l["idx"] for l in job["labels"] if l["status"] != "ok")
        body = {"brand": "XYZ", "quality": "ECON", "color": "Gelo", "size_value": 5, "size_unit": "KG"}
        j = s.put(f"{BASE_URL}/api/jobs/{job['id']}/labels/{idx}", json=body).json()
        assert j["labels"][idx]["status"] != "ok"
        s.put(f"{BASE_URL}/api/jobs/{job['id']}/labels/{idx}", json={})

    def test_bad_idx(self, s, job):
        assert s.put(f"{BASE_URL}/api/jobs/{job['id']}/labels/999", json={}).status_code == 404


# --- Settings + reanalyze
class TestSettings:
    def test_get(self, s):
        d = s.get(f"{BASE_URL}/api/settings").json()
        assert len(d["colors"]) == 27 and len(d["qualities"]) == 3 and len(d["brands"]) == 9
        assert "_id" not in d

    def test_duplicate_rejected(self, s):
        d = s.get(f"{BASE_URL}/api/settings").json()
        d["brands"].append({"name": "cmc", "aliases": []})
        assert s.put(f"{BASE_URL}/api/settings", json=d).status_code == 400

    def test_empty_rejected(self, s):
        d = s.get(f"{BASE_URL}/api/settings").json()
        d["brands"] = []
        assert s.put(f"{BASE_URL}/api/settings", json=d).status_code == 400

    def test_reorder_reanalyze_reset(self, s, job):
        d = s.get(f"{BASE_URL}/api/settings").json()
        d["colors"] = list(reversed(d["colors"]))
        d["qualities"] = list(reversed(d["qualities"]))
        r = s.put(f"{BASE_URL}/api/settings", json=d)
        assert r.status_code == 200
        assert r.json()["colors"][0]["name"] == "Crômio"
        j = s.post(f"{BASE_URL}/api/jobs/{job['id']}/reanalyze").json()
        assert j["page_order"] != job["page_order"]
        assert sorted(j["page_order"]) == list(range(67))
        # first classified label must now be highest quality index
        first = next(l for l in j["labels"] if l["position"] == 0)
        assert first["quality"] == "MANTA EMB / SUPERLAV"
        r = s.post(f"{BASE_URL}/api/settings/reset")
        assert r.json()["colors"][0]["name"] == "Branco Neve"
        j2 = s.post(f"{BASE_URL}/api/jobs/{job['id']}/reanalyze").json()
        assert j2["page_order"] == job["page_order"]


# --- List / delete
class TestListDelete:
    def test_list(self, s, job):
        lst = s.get(f"{BASE_URL}/api/jobs").json()
        m = [x for x in lst if x["id"] == job["id"]]
        assert m and "labels" not in m[0] and m[0]["user_name"] == "TEST_user"

    def test_delete(self, s, job, created):
        assert s.delete(f"{BASE_URL}/api/jobs/{job['id']}").status_code == 200
        assert s.get(f"{BASE_URL}/api/jobs/{job['id']}").status_code == 404
        assert s.delete(f"{BASE_URL}/api/jobs/{job['id']}").status_code == 404
        created.remove(job["id"])
