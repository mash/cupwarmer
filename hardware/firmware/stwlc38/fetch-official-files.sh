#!/bin/sh
set -eu

archive="STWLC38JRM_config_and_patch_cut1.2_cut1.3.zip"
source_url="https://community.st.com/topic/trackAttachment?file_uuid=5812833d-6f28-40d9-a821-59aeeed58f17&redirect=1"
expected_archive_sha256="f949f542c16c30c5d133c36dd29a9876bf52f8f2560f69d99f4dc5d9e8b72e6b"

curl -L --fail --show-error "$source_url" -o "$archive"
actual_archive_sha256="$(shasum -a 256 "$archive" | awk '{print $1}')"

if [ "$actual_archive_sha256" != "$expected_archive_sha256" ]; then
    echo "Checksum mismatch for $archive" >&2
    exit 1
fi

unzip -o "$archive"

echo "Official STWLC38 files downloaded and verified."
