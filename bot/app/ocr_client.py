from __future__ import annotations

import base64
import os
from typing import Any

import aiohttp


class OcrServiceError(RuntimeError):
    pass


def _require_env(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        raise OcrServiceError(f"Missing env var: {name}")
    return v


async def scan_image(
    *,
    image_bytes: bytes,
    filename: str = "image.png",
    content_type: str | None = None,
    include_debug: bool = True,
    timeout_seconds: float = 120.0,
) -> tuple[dict[str, Any], bytes | None]:
    """Send image bytes to OCR web service and return (payload, debug_png_bytes)."""

    base_url = _require_env("OCR_SERVICE_URL").rstrip("/")
    api_key = _require_env("OCR_API_KEY")

    url = f"{base_url}/scan"
    params = {"include_debug": "true" if include_debug else "false"}

    form = aiohttp.FormData()
    form.add_field(
        name="image",
        value=image_bytes,
        filename=filename,
        content_type=content_type or "application/octet-stream",
    )

    headers = {"Authorization": f"Bearer {api_key}"}

    timeout = aiohttp.ClientTimeout(total=timeout_seconds)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, params=params, data=form, headers=headers) as resp:
            raw = await resp.text()
            if resp.status >= 400:
                raise OcrServiceError(f"OCR service HTTP {resp.status}: {raw[:500]}")

            try:
                payload = await resp.json()
            except Exception as e:  # noqa: BLE001
                raise OcrServiceError(
                    f"OCR service returned non-JSON: {raw[:500]}"
                ) from e

    if not isinstance(payload, dict) or not payload.get("success"):
        raise OcrServiceError(
            str(payload.get("error") if isinstance(payload, dict) else payload)
        )

    debug_b64 = payload.get("debug_png_base64")
    debug_png = None
    if isinstance(debug_b64, str) and debug_b64:
        try:
            debug_png = base64.b64decode(debug_b64)
        except Exception as e:  # noqa: BLE001
            raise OcrServiceError("Failed to decode debug image") from e

    return payload, debug_png
