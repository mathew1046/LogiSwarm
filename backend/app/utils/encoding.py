# LogiSwarm - Geo-Aware Swarm Intelligence for Supply Chains
# Copyright (C) 2025 LogiSwarm Contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def detect_file_encoding(file_path: Path | str, sample_size: int = 1024) -> str:
    try:
        import chardet
    except ImportError:
        logger.warning("chardet not installed, defaulting to utf-8")
        return "utf-8"

    path = Path(file_path) if isinstance(file_path, str) else file_path

    try:
        with open(path, "rb") as f:
            raw_data = f.read(sample_size)

        if not raw_data:
            return "utf-8"

        result = chardet.detect(raw_data)
        encoding = result.get("encoding", "utf-8")
        confidence = result.get("confidence", 0)

        logger.info(
            f"Detected encoding {encoding} for {path.name} (confidence: {confidence:.2%})"
        )

        return encoding or "utf-8"

    except Exception as e:
        logger.warning(
            f"Failed to detect encoding for {path}: {e}, defaulting to utf-8"
        )
        return "utf-8"


def read_file_with_fallback(file_path: Path | str, sample_size: int = 1024) -> str:
    path = Path(file_path) if isinstance(file_path, str) else file_path

    encodings_to_try = [
        ("utf-8", "UTF-8 BOM-free"),
        (None, "Auto-detected"),
        ("utf-8-sig", "UTF-8 with BOM"),
        ("latin-1", "Latin-1 (always succeeds)"),
    ]

    detected_encoding: Optional[str] = None

    for encoding, description in encodings_to_try:
        try:
            if encoding is None:
                detected_encoding = detect_file_encoding(path, sample_size)
                encoding_to_use = detected_encoding
                description = f"Auto-detected: {detected_encoding}"
            else:
                encoding_to_use = encoding

            with open(path, "r", encoding=encoding_to_use) as f:
                content = f.read()

            logger.info(f"Successfully read {path.name} using {description} encoding")
            return content

        except UnicodeDecodeError as e:
            logger.debug(f"Failed to read {path.name} with {description}: {e}")
            continue
        except Exception as e:
            logger.error(f"Error reading {path.name}: {e}")
            continue

    logger.warning(f"Using latin-1 as fallback for {path.name}")
    with open(path, "r", encoding="latin-1") as f:
        return f.read()


def safe_decode_bytes(data: bytes, encodings: Optional[list[str]] = None) -> str:
    if encodings is None:
        encodings = ["utf-8", "utf-8-sig", "latin-1"]

    for encoding in encodings:
        try:
            decoded = data.decode(encoding)
            logger.debug(f"Successfully decoded {len(data)} bytes using {encoding}")
            return decoded
        except UnicodeDecodeError:
            continue
        except Exception as e:
            logger.debug(f"Error decoding with {encoding}: {e}")
            continue

    logger.warning("All encodings failed, using latin-1 as ultimate fallback")
    return data.decode("latin-1", errors="replace")
