from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os

app = FastAPI()

LICENSE_FILE = "licenses.json"


def load_licenses():
    if not os.path.exists(LICENSE_FILE):
        with open(LICENSE_FILE, "w") as f:
            json.dump({}, f, indent=4)

    with open(LICENSE_FILE, "r") as f:
        return json.load(f)


def save_licenses(data):
    with open(LICENSE_FILE, "w") as f:
        json.dump(data, f, indent=4)


class LicenseRequest(BaseModel):
    key: str
    spyeye: str
    secret: str


class CreateLicense(BaseModel):
    key: str
    spyeye: str
    secret: str


@app.post("/api/check-license")
def check_license(data: LicenseRequest):

    licenses = load_licenses()

    if data.key not in licenses:
        raise HTTPException(status_code=403, detail="Invalid License")

    lic = licenses[data.key]

    if not lic["active"]:
        raise HTTPException(status_code=403, detail="License Blocked")

    if lic["secret"] != data.secret:
        raise HTTPException(status_code=403, detail="Invalid Secret")

    if lic["spyeye"] != data.spyeye:
        raise HTTPException(status_code=403, detail="Invalid SpyEye Key")

    return {"status": "ok"}


@app.post("/api/create-license")
def create_license(data: CreateLicense):

    licenses = load_licenses()

    licenses[data.key] = {
        "spyeye": data.spyeye,
        "secret": data.secret,
        "active": True
    }

    save_licenses(licenses)

    return {"status": "created"}


@app.post("/api/block/{key}")
def block_license(key: str):

    licenses = load_licenses()

    if key in licenses:
        licenses[key]["active"] = False
        save_licenses(licenses)

    return {"status": "blocked"}


@app.post("/api/unblock/{key}")
def unblock_license(key: str):

    licenses = load_licenses()

    if key in licenses:
        licenses[key]["active"] = True
        save_licenses(licenses)

    return {"status": "active"}


@app.get("/api/licenses")
def all_licenses():
    return load_licenses()