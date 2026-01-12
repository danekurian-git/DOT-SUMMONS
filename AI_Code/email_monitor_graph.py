"""
Email monitor for NYC DOT NOV PDFs using Microsoft Graph API (device code flow).
Downloads PDF attachments from a sender and writes them to the NYCDOT root.
"""
import argparse
import base64
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import msal
import requests

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
DEFAULT_SENDER = "dashnov@dot.nyc.gov"
SCOPES = ["Mail.Read"]


def load_state(state_path):
    if state_path.exists():
        with state_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "processed_message_ids": [],
        "processed_attachment_ids": [],
        "last_run_utc": "",
    }


def save_state(state_path, state):
    state_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = state_path.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    tmp_path.replace(state_path)


def get_access_token(client_id, tenant_id, cache_path):
    cache = msal.SerializableTokenCache()
    if cache_path.exists():
        cache.deserialize(cache_path.read_text(encoding="utf-8"))

    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.PublicClientApplication(client_id=client_id, authority=authority, token_cache=cache)

    accounts = app.get_accounts()
    result = None
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])

    if not result:
        flow = app.initiate_device_flow(scopes=SCOPES)
        if "message" not in flow:
            raise RuntimeError("Device flow init failed. Check client/tenant IDs.")
        print(flow["message"])
        result = app.acquire_token_by_device_flow(flow)

    if "access_token" not in result:
        raise RuntimeError(f"Token acquisition failed: {result.get('error_description', result)}")

    if cache.has_state_changed:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(cache.serialize(), encoding="utf-8")

    return result["access_token"]


def graph_get(url, token, params=None):
    headers = {"Authorization": f"Bearer {token}"}
    for _ in range(3):
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        if resp.status_code in (429, 503):
            wait_s = int(resp.headers.get("Retry-After", "5"))
            time.sleep(wait_s)
            continue
        if resp.status_code >= 400:
            raise RuntimeError(f"Graph error {resp.status_code}: {resp.text[:500]}")
        return resp
    raise RuntimeError("Graph request failed after retries")


def iter_messages(token, sender, since_dt, folder, all_folders, max_messages):
    if all_folders:
        endpoint = f"{GRAPH_BASE}/me/messages"
    else:
        endpoint = f"{GRAPH_BASE}/me/mailFolders/{folder}/messages"

    since_iso = since_dt.isoformat().replace("+00:00", "Z")
    filter_str = (
        f"from/emailAddress/address eq '{sender}' and "
        f"hasAttachments eq true and "
        f"receivedDateTime ge {since_iso}"
    )

    params = {
        "$filter": filter_str,
        "$select": "id,subject,from,receivedDateTime,hasAttachments",
        "$orderby": "receivedDateTime desc",
        "$top": 50,
    }

    url = endpoint
    count = 0
    while url:
        resp = graph_get(url, token, params=params)
        data = resp.json()
        for item in data.get("value", []):
            yield item
            count += 1
            if max_messages and count >= max_messages:
                return
        url = data.get("@odata.nextLink")
        params = None


def list_attachments(token, message_id):
    url = f"{GRAPH_BASE}/me/messages/{message_id}/attachments"
    params = {"$select": "id,name,contentType,size,contentBytes"}
    resp = graph_get(url, token, params=params)
    return resp.json().get("value", [])


def download_attachment(token, message_id, attachment_id):
    url = f"{GRAPH_BASE}/me/messages/{message_id}/attachments/{attachment_id}/$value"
    resp = graph_get(url, token)
    return resp.content


def save_pdf_attachment(token, message_id, attachment, output_dir, dry_run):
    name = attachment.get("name") or "attachment.pdf"
    content_type = (attachment.get("contentType") or "").lower()
    if not (name.lower().endswith(".pdf") or content_type == "application/pdf"):
        return "not_pdf", None

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / name
    if output_path.exists():
        return "exists", output_path

    if dry_run:
        return "dry_run", output_path

    content_bytes = attachment.get("contentBytes")
    if content_bytes:
        data = base64.b64decode(content_bytes)
    else:
        data = download_attachment(token, message_id, attachment["id"])

    with output_path.open("wb") as f:
        f.write(data)

    return "saved", output_path


def parse_args():
    parser = argparse.ArgumentParser(description="Download DOT NOV PDFs via Microsoft Graph")
    parser.add_argument("--sender", default=os.getenv("GRAPH_SENDER", DEFAULT_SENDER))
    parser.add_argument("--since-days", type=int, default=180)
    parser.add_argument("--since", help="YYYY-MM-DD (overrides --since-days)")
    parser.add_argument("--folder", default="Inbox")
    parser.add_argument("--all-folders", action="store_true")
    parser.add_argument("--output", help="Output directory for PDFs")
    parser.add_argument("--max-messages", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--reset-state", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--client-id", default=os.getenv("GRAPH_CLIENT_ID"))
    parser.add_argument("--tenant-id", default=os.getenv("GRAPH_TENANT_ID"))
    return parser.parse_args()


def main():
    args = parse_args()

    if not args.client_id or not args.tenant_id:
        print("Missing GRAPH_CLIENT_ID or GRAPH_TENANT_ID.")
        print("Set env vars or pass --client-id/--tenant-id.")
        sys.exit(1)

    if args.since:
        try:
            since_dt = datetime.strptime(args.since, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            print("Invalid --since format. Use YYYY-MM-DD.")
            sys.exit(1)
    else:
        since_dt = datetime.now(timezone.utc) - timedelta(days=args.since_days)

    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    output_dir = Path(args.output) if args.output else repo_root

    cache_dir = script_dir / ".graph_cache"
    token_cache = cache_dir / "msal_token_cache.bin"
    state_path = cache_dir / "email_state.json"

    state = load_state(state_path)
    if args.reset_state:
        state = {
            "processed_message_ids": [],
            "processed_attachment_ids": [],
            "last_run_utc": "",
        }

    processed_messages = set(state.get("processed_message_ids", []))
    processed_attachments = set(state.get("processed_attachment_ids", []))

    token = get_access_token(args.client_id, args.tenant_id, token_cache)

    total_messages = 0
    total_attachments = 0
    saved = 0
    skipped_existing = 0
    skipped_non_pdf = 0

    for message in iter_messages(
        token, args.sender, since_dt, args.folder, args.all_folders, args.max_messages
    ):
        msg_id = message.get("id")
        if msg_id in processed_messages:
            continue

        total_messages += 1
        attachments = list_attachments(token, msg_id)
        for att in attachments:
            total_attachments += 1
            att_id = att.get("id")
            if att_id in processed_attachments:
                continue

            status, path = save_pdf_attachment(token, msg_id, att, output_dir, args.dry_run)
            if status == "saved":
                saved += 1
                processed_attachments.add(att_id)
                if args.verbose:
                    print(f"Saved: {path}")
            elif status == "exists":
                skipped_existing += 1
                processed_attachments.add(att_id)
            elif status == "not_pdf":
                skipped_non_pdf += 1
                processed_attachments.add(att_id)
            elif status == "dry_run":
                if args.verbose:
                    print(f"Dry run: {path}")

        processed_messages.add(msg_id)

    state["processed_message_ids"] = sorted(processed_messages)
    state["processed_attachment_ids"] = sorted(processed_attachments)
    state["last_run_utc"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    save_state(state_path, state)

    print("\nEmail monitor summary")
    print(f"Messages scanned: {total_messages}")
    print(f"Attachments scanned: {total_attachments}")
    print(f"PDFs saved: {saved}")
    print(f"Skipped (existing): {skipped_existing}")
    print(f"Skipped (non-pdf): {skipped_non_pdf}")
    if args.dry_run:
        print("Dry run enabled (no files written).")
    print(f"Output dir: {output_dir}")


if __name__ == "__main__":
    main()
