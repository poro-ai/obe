"""Pydantic 資料模型：PDF 解析結果與相關結構。"""

from pydantic import BaseModel, Field


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
