"""
從 PDF 擷取內嵌圖片，供結構化解析結果填入 image content。

- 使用 PyMuPDF：page.get_images() + doc.extract_image(xref)。
- 回傳依頁分組的 (base64, mime_type)，供 processor 填入 type=image 且 content 為空的區塊。
"""

import base64
import logging
from io import BytesIO

logger = logging.getLogger(__name__)

# 每頁最多擷取張數、單張最大位元組數（超過則略過，避免 payload 過大）
MAX_IMAGES_PER_PAGE = 10
MAX_IMAGE_BYTES = 500 * 1024  # 500KB


def _ext_to_mime(ext: str) -> str:
    e = (ext or "").lower().strip()
    if e in ("jpg", "jpeg"):
        return "image/jpeg"
    if e == "png":
        return "image/png"
    if e == "gif":
        return "image/gif"
    if e == "webp":
        return "image/webp"
    return "image/png"


def extract_images_by_page(pdf_bytes: bytes) -> dict[int, list[tuple[str, str]]]:
    """
    從 PDF 位元組擷取每頁的內嵌圖片，回傳 base64 與 MIME。

    回傳：{ page_index_0based: [ (base64_str, mime_type), ... ] }
    每頁最多 MAX_IMAGES_PER_PAGE 張，單張超過 MAX_IMAGE_BYTES 則略過。
    """
    try:
        import pymupdf
    except ImportError:
        logger.warning("pymupdf not installed, skip PDF image extraction")
        return {}

    result: dict[int, list[tuple[str, str]]] = {}
    try:
        doc = pymupdf.open(stream=BytesIO(pdf_bytes), filetype="pdf")
    except Exception as e:
        logger.warning("pymupdf.open failed: %s", e)
        return {}

    try:
        for page_index in range(len(doc)):
            images = doc[page_index].get_images()
            if not images:
                continue
            list_for_page: list[tuple[str, str]] = []
            for item in images[:MAX_IMAGES_PER_PAGE]:
                xref = item[0] if isinstance(item, (list, tuple)) else item
                try:
                    info = doc.extract_image(xref)
                except Exception as e:
                    logger.debug("extract_image xref=%s: %s", xref, e)
                    continue
                if not info or "image" not in info:
                    continue
                raw = info.get("image", b"")
                if len(raw) > MAX_IMAGE_BYTES:
                    logger.debug("skip large image page=%s size=%s", page_index, len(raw))
                    continue
                ext = info.get("ext") or "png"
                mime = _ext_to_mime(ext)
                b64 = base64.standard_b64encode(raw).decode("ascii")
                list_for_page.append((b64, mime))
            if list_for_page:
                result[page_index] = list_for_page
    finally:
        doc.close()

    return result
