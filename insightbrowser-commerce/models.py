"""Commerce Bridge - Data Models"""

from pydantic import BaseModel, Field
from typing import Optional


class CommerceSiteRequest(BaseModel):
    """商家提交的入驻请求"""
    name: str = Field(..., description="店铺名称")
    url: str = Field(..., description="店铺官网 URL")
    category: str = Field(..., description="商品类别")
    description: str = Field(..., description="简短描述")


class CommerceSiteResponse(BaseModel):
    """入驻响应"""
    success: bool
    message: str = ""
    agent_json: Optional[dict] = None
    registry_id: Optional[str] = None
    hosting_id: Optional[int] = None
    discover_url: Optional[str] = None
