"""Pydantic 資料模型：PDF 解析結果與相關結構。"""

from pydantic import BaseModel, Field


class BlockElement(BaseModel):
    """單一內容塊：圖片或文字，供編輯器渲染。"""

    type: str = Field(..., description="'image' 或 'text'")
    content: str = Field(..., description="圖片為 base64/uri，文字為內文")
    description: str = Field(default="", description="圖片精簡描述，文字可為空")


class PageBlock(BaseModel):
    """單頁結構化解析結果：頁碼 + 元素列表。"""

    page: int = Field(..., ge=1, description="頁碼，從 1 開始")
    elements: list[BlockElement] = Field(default_factory=list, description="該頁的圖片與文字塊")


class PageExtract(BaseModel):
    """單頁或單一圖文區塊的解析結果。"""

    group_id: str = Field(..., description="圖文區塊或群組識別碼")
    visual_summary: str = Field(..., description="視覺內容摘要（圖表、版面等）")
    associated_text: str = Field(..., description="該區塊對應的文字內容")
    page_number: int = Field(..., ge=1, description="頁碼，從 1 開始")


class ImageTextExtract(BaseModel):
    """圖文解析後的 JSON 結構：單一區塊的影像摘要與文字分析。"""

    group_id: str = Field(..., description="圖文區塊或群組識別碼")
    image_summary: str = Field(..., description="影像內容摘要（圖表、圖片描述等）")
    text_analysis: str = Field(..., description="該區塊的文字分析結果")
    page_number: int = Field(..., ge=1, description="頁碼，從 1 開始")
