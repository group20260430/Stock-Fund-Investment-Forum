"""文件上传接口"""
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import ApiResponse

router = APIRouter(tags=["uploads"])

# 上传目录（相对于 backend 目录）
UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"

# 允许的文件类型 MIME 白名单
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/svg+xml",
    "application/pdf",
    "text/plain",
    "text/csv",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/zip",
    "application/x-rar-compressed",
    "application/x-7z-compressed",
}

# 单文件最大 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("/uploads")
async def upload_file(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """上传附件文件"""

    # 校验文件大小（读取内容后检查，避免过大文件占用内存）
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小超过 10MB 限制")

    # 校验 MIME 类型
    # FastAPI 的 content_type 可能不可靠，这里只做参考
    # 实际应用中可结合 python-magic 做更准确检测

    # 生成唯一文件名
    original_name = file.filename or "unknown"
    ext = os.path.splitext(original_name)[1].lower() or ".bin"
    safe_name = f"{uuid.uuid4().hex}{ext}"

    # 确保上传目录存在
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # 写入文件
    file_path = UPLOAD_DIR / safe_name
    with open(file_path, "wb") as f:
        f.write(contents)

    # 构造可访问的 URL
    file_url = f"/uploads/{safe_name}"

    # 如果前端请求通过 /api 前缀访问，需要确保 URL 正确
    # 这里返回相对路径，前端通过静态文件服务访问

    return ApiResponse(
        code=200,
        message="上传成功",
        data={
            "file_name": original_name,
            "file_url": file_url,
            "file_size": len(contents),
            "file_type": file.content_type or "application/octet-stream",
        },
    )
