"""Extract data from Signal DB."""

import json
from pathlib import Path
from typing import Optional

from sqlcipher3 import dbapi2
from typer import Exit, colors, secho

from sigexport import crypto, models
from sigexport.logging import log


def fetch_data(
    source_dir: Path,
    password: Optional[str],
    chats: str,
    include_empty: bool,
) -> tuple[models.Convos, models.Contacts]:
    """Load SQLite data into dicts."""
    db_file = source_dir / "sql" / "db.sqlite"
    signal_config = source_dir / "config.json"

    try:
        key = crypto.get_key(signal_config, password)
    except Exception:
        secho("Failed to decrypt Signal password", fg=colors.RED)
        raise Exit(1)

    log(f"Fetching data from {db_file}\n")
    contacts: models.Contacts = {}
    convos: models.Convos = {}
    chats_list = chats.split(",") if len(chats) > 0 else []

    db = dbapi2.connect(str(db_file))
    c = db.cursor()
    # param binding doesn't work for pragmas, so use a direct string concat
    q = f"PRAGMA KEY = \"x'{key}'\""
    print(q)
    c.execute(q)
    q = "PRAGMA cipher_page_size = 4096"
    print(q)
    c.execute(q)
    q = "PRAGMA kdf_iter = 64000"
    print(q)
    c.execute(q)
    q = "PRAGMA cipher_hmac_algorithm = HMAC_SHA512"
    print(q)
    c.execute(q)
    q = "PRAGMA cipher_kdf_algorithm = PBKDF2_HMAC_SHA512"
    print(q)
    c.execute(q)

    query = "SELECT type, id, serviceId, e164, name, profileName, profileFamilyName, profileFullName, members FROM conversations"
    c.execute(query)
    for result in c:
        log(f"\tLoading SQL results for: {result[4]}, aka {result[7]}")
        members = []
        if result[5]:
            members = result[5].split(" ")
        is_group = result[0] == "group"
        cid = result[1]
        contacts[cid] = models.Contact(
            id=cid,
            service_id=result[2],
            name=result[4],
            number=result[2],
            profile_name=result[5],
            profile_family_name=result[6],
            profile_full_name=result[7],
            members=members,
            is_group=is_group,
        )
        if contacts[cid].name is None:
            contacts[cid].name = contacts[cid].profile_name

        if not chats or (result[4] in chats_list or result[5] in chats_list):
            convos[cid] = []

    query = "SELECT json, conversationId, id, sourceServiceId, type, body, source, timestamp, sent_at, serverTimestamp, hasAttachments, readStatus, seenStatus  FROM messages ORDER BY sent_at"
    c.execute(query)
    for result in c:
        res = json.loads(result[0])
        cid = result[1]
        if cid and cid in convos:
            if result[4] in ["keychange", "profile-change"]:
                continue
            con = models.RawMessage(
                conversation_id=cid,
                id=resut[2],
                source_service_id=result[3],
                type=result[4],
                body=result[5],
                contact=res.get("contact"),
                source=result[6],
                timestamp=result[7],
                sent_at=result[8],
                server_timestamp=result[9],
                has_attachments=result[10],
                attachments=res.get("attachments", []),
                read_status=result[11],
                seen_status=result[12],
                call_history=res.get("call_history"),
                reactions=res.get("reactions", []),
                sticker=res.get("sticker"),
                quote=res.get("quote"),
            )
            convos[cid].append(con)

    if not include_empty:
        convos = {key: val for key, val in convos.items() if len(val) > 0}

    return convos, contacts
