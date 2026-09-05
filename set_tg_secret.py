import urllib.request
import urllib.parse
import json
from nacl import encoding, public
import base64
import ssl

context = ssl._create_unverified_context()

GITHUB_TOKEN = "REMOVED_TOKEN"
REPO = "tsxau26-ux/fillo-outreach"
SECRET_NAME = "TELEGRAM_BOT_TOKEN"
SECRET_VALUE = "8827856631:AAFifV78WOsKnLXbmO7wd03TGCBbME4In64"

def get_public_key():
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/actions/secrets/public-key")
    req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    with urllib.request.urlopen(req, context=context) as response:
        data = json.loads(response.read().decode())
    return data['key_id'], data['key']

def encrypt_secret(public_key: str, secret_value: str) -> str:
    public_key_bytes = base64.b64decode(public_key)
    public_key_obj = public.PublicKey(public_key_bytes)
    sealed_box = public.SealedBox(public_key_obj)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")

def update_secret(key_id: str, encrypted_value: str):
    data = json.dumps({"encrypted_value": encrypted_value, "key_id": key_id}).encode("utf-8")
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/actions/secrets/{SECRET_NAME}", data=data, method="PUT")
    req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    try:
        with urllib.request.urlopen(req, context=context) as response:
            print("Secret updated successfully. HTTP Status:", response.status)
    except Exception as e:
        print("Error updating secret:", e)

key_id, pub_key = get_public_key()
enc_val = encrypt_secret(pub_key, SECRET_VALUE)
update_secret(key_id, enc_val)
