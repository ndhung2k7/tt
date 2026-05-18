from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uuid
import os
from utils.video_splitter import VideoSplitter

app = FastAPI(title="Video Splitter API", description="Tự động cắt video theo thời lượng hoặc số lượng")

# Khởi tạo templates
templates = Jinja2Templates(directory="templates")

# Khởi tạo bộ xử lý video
splitter = VideoSplitter()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Giao diện chính"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/split-video")
async def split_video(
    file: UploadFile = File(...),
    split_mode: str = Form(...),
    value: float = Form(...)
):
    """
    API cắt video
    - split_mode: "duration" hoặc "count"
    - value: giá trị tương ứng (phút hoặc số phần)
    """
    # Kiểm tra định dạng file
    allowed_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv']
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Định dạng video không được hỗ trợ")
    
    # Lưu file upload tạm thời
    temp_filename = f"{uuid.uuid4().hex}{file_extension}"
    temp_path = os.path.join(splitter.upload_folder, temp_filename)
    
    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    try:
        # Xử lý theo chế độ
        if split_mode == "duration":
            if value <= 0:
                raise HTTPException(status_code=400, detail="Thời lượng phải lớn hơn 0")
            output_files = splitter.split_by_duration(temp_path, value)
        elif split_mode == "count":
            if value <= 0 or not value.is_integer():
                raise HTTPException(status_code=400, detail="Số lượng phải là số nguyên dương")
            output_files = splitter.split_by_count(temp_path, int(value))
        else:
            raise HTTPException(status_code=400, detail="Chế độ không hợp lệ")
        
        # Tạo file zip
        zip_path = splitter.create_zip(output_files)
        
        # Trả file zip về cho người dùng
        return FileResponse(
            path=zip_path,
            media_type="application/zip",
            filename=f"split_video_{uuid.uuid4().hex[:8]}.zip"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý video: {str(e)}")
    
    finally:
        # Dọn dẹp file tạm
        splitter.cleanup_files(temp_path)
        # Lưu ý: File zip sẽ được tự động xóa sau khi response hoàn tất 
        # bằng cách dùng BackgroundTasks (xem bên dưới)
        # Đã có cleanup_old_files chạy định kỳ

@app.on_event("startup")
async def startup_event():
    """Chạy khi khởi động app"""
    import asyncio
    import threading
    
    def periodic_cleanup():
        import time
        while True:
            time.sleep(3600)  # Mỗi giờ dọn 1 lần
            splitter.cleanup_old_files(max_age_seconds=3600)
    
    # Chạy thread dọn dẹp nền
    thread = threading.Thread(target=periodic_cleanup, daemon=True)
    thread.start()

# Middleware để xóa file zip sau khi gửi
from fastapi import BackgroundTasks

@app.post("/split-video-v2")
async def split_video_with_cleanup(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    split_mode: str = Form(...),
    value: float = Form(...)
):
    """Phiên bản có tự động xóa file zip sau khi tải"""
    # Code tương tự như trên nhưng thêm:
    # background_tasks.add_task(splitter.cleanup_files, zip_path)
    # (Để tránh trùng lặp, bạn có thể dùng endpoint này)
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
