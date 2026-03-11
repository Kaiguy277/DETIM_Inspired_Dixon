"""
Sync CMIP6 CSVs from Google Drive (dixon_cmip6 folder) to data/cmip6/.

Downloads files exported by the GEE script. Can be re-run as more
exports complete — only downloads new or updated files.

Usage:
    python sync_cmip6_from_drive.py [--check]   # --check just lists status
"""
import io
import argparse
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

PROJECT = Path('/home/kai/Documents/Opus46Dixon_FirstShot')
TOKEN_FILE = PROJECT / 'data' / 'cmip6' / 'gdrive_token.json'
LOCAL_DIR = PROJECT / 'data' / 'cmip6'
DRIVE_FOLDER = 'dixon_cmip6'

EXPECTED_FILES = []
for gcm in ['ACCESS-CM2', 'EC-Earth3', 'MPI-ESM1-2-HR', 'MRI-ESM2-0', 'NorESM2-MM']:
    for ssp in ['ssp126', 'ssp245', 'ssp585']:
        EXPECTED_FILES.append(f'dixon_{gcm}_{ssp}.csv')


def get_service():
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE))
    return build('drive', 'v3', credentials=creds)


def find_folder(service):
    results = service.files().list(
        q=f"name='{DRIVE_FOLDER}' and mimeType='application/vnd.google-apps.folder'",
        fields='files(id, name)',
    ).execute()
    folders = results.get('files', [])
    if not folders:
        print(f"ERROR: Folder '{DRIVE_FOLDER}' not found on Google Drive.")
        return None
    return folders[0]['id']


def list_drive_files(service, folder_id):
    items = service.files().list(
        q=f"'{folder_id}' in parents",
        fields='files(id, name, size, modifiedTime)',
        orderBy='name',
        pageSize=50,
    ).execute()
    return items.get('files', [])


def download_file(service, file_id, dest_path):
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dest_path, 'wb') as f:
        f.write(fh.getvalue())


def sync(check_only=False):
    service = get_service()
    folder_id = find_folder(service)
    if not folder_id:
        return

    drive_files = list_drive_files(service, folder_id)
    drive_map = {f['name']: f for f in drive_files}

    print(f"Drive folder: {DRIVE_FOLDER}")
    print(f"Files on Drive: {len(drive_files)}")
    print(f"Expected: {len(EXPECTED_FILES)}")
    print()

    downloaded = 0
    skipped = 0
    pending = 0
    empty = 0

    for expected in EXPECTED_FILES:
        local_path = LOCAL_DIR / expected
        drive_file = drive_map.get(expected)

        if drive_file is None:
            print(f"  PENDING  {expected}")
            pending += 1
            continue

        size = int(drive_file.get('size', 0))
        if size < 100:
            print(f"  EMPTY    {expected} ({size} bytes — GEE still exporting?)")
            empty += 1
            continue

        size_kb = size / 1024
        if local_path.exists() and local_path.stat().st_size >= size:
            print(f"  EXISTS   {expected} ({size_kb:.0f} KB)")
            skipped += 1
            continue

        if check_only:
            print(f"  READY    {expected} ({size_kb:.0f} KB)")
            continue

        print(f"  DOWNLOAD {expected} ({size_kb:.0f} KB)...", end='', flush=True)
        download_file(service, drive_file['id'], local_path)
        print(" done")
        downloaded += 1

    # Check for non-CSV files (GEE sometimes exports without extension)
    for name, f in drive_map.items():
        if name not in EXPECTED_FILES and not name.endswith('.csv'):
            csv_name = name + '.csv' if not name.endswith('.csv') else name
            if csv_name in EXPECTED_FILES:
                continue
            size = int(f.get('size', 0))
            if size > 100:
                print(f"  EXTRA    {name} ({size/1024:.0f} KB)")

    print(f"\nSummary: {downloaded} downloaded, {skipped} already local, "
          f"{pending} pending, {empty} empty/exporting")

    if pending > 0 or empty > 0:
        print(f"\nRe-run this script once GEE exports finish.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true',
                        help='Just check status, do not download')
    args = parser.parse_args()
    sync(check_only=args.check)
