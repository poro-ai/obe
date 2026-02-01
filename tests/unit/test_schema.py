"""Pydantic schema 驗證：BlockElement、PageBlock、PageExtract、ImageTextExtract。"""

import pytest
from pydantic import ValidationError

from src.models.schema import BlockElement, ImageTextExtract, PageBlock, PageExtract


class TestBlockElement:
    """BlockElement：type、content 必填；description 預設空字串。"""

    def test_valid_image(self) -> None:
        el = BlockElement(type="image", content="base64data", description="圖表")
        assert el.type == "image"
        assert el.content == "base64data"
        assert el.description == "圖表"

    def test_valid_text_default_description(self) -> None:
        el = BlockElement(type="text", content="內文")
        assert el.description == ""

    def test_missing_type_raises(self) -> None:
        with pytest.raises(ValidationError):
            BlockElement(content="x", description="")  # type missing

    def test_missing_content_raises(self) -> None:
        with pytest.raises(ValidationError):
            BlockElement(type="text", description="")  # content missing

    def test_content_is_str(self) -> None:
        el = BlockElement(type="text", content="x")
        assert isinstance(el.content, str)


class TestPageBlock:
    """PageBlock：page >= 1，elements 預設空列表。"""

    def test_valid_minimal(self) -> None:
        block = PageBlock(page=1, elements=[])
        assert block.page == 1
        assert block.elements == []

    def test_valid_with_elements(self) -> None:
        el = BlockElement(type="text", content="hi")
        block = PageBlock(page=1, elements=[el])
        assert len(block.elements) == 1
        assert block.elements[0].content == "hi"

    def test_page_less_than_one_raises(self) -> None:
        with pytest.raises(ValidationError):
            PageBlock(page=0, elements=[])

    def test_page_invalid_type_raises(self) -> None:
        """page 無法轉成 int 時應拋 ValidationError（Pydantic v2 會將 '1' 轉成 1，故用 list）。"""
        with pytest.raises(ValidationError):
            PageBlock(page=[1], elements=[])  # type: ignore[arg-type]

    def test_elements_default(self) -> None:
        block = PageBlock(page=1)
        assert block.elements == []


class TestPageExtract:
    """PageExtract：group_id、visual_summary、associated_text、page_number 必填；page_number >= 1。"""

    def test_valid(self) -> None:
        ex = PageExtract(
            group_id="g1",
            visual_summary="圖表",
            associated_text="文字",
            page_number=1,
        )
        assert ex.page_number == 1

    def test_page_number_less_than_one_raises(self) -> None:
        with pytest.raises(ValidationError):
            PageExtract(
                group_id="g1",
                visual_summary="x",
                associated_text="y",
                page_number=0,
            )

    def test_missing_group_id_raises(self) -> None:
        with pytest.raises(ValidationError):
            PageExtract(
                visual_summary="x",
                associated_text="y",
                page_number=1,
            )


class TestImageTextExtract:
    """ImageTextExtract：group_id、image_summary、text_analysis、page_number 必填。"""

    def test_valid(self) -> None:
        ex = ImageTextExtract(
            group_id="g1",
            image_summary="圖",
            text_analysis="文",
            page_number=1,
        )
        assert ex.page_number == 1

    def test_page_number_ge_one(self) -> None:
        with pytest.raises(ValidationError):
            ImageTextExtract(
                group_id="g1",
                image_summary="x",
                text_analysis="y",
                page_number=0,
            )
