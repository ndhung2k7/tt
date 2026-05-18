import os
import uuid
import shutil
import math
import zipfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import ffmpeg
import imageio_ffmpeg

app = FastAPI(title="Video Splitter", version="1.0.0")

# Templates
templates = Jinja2Templates(directory="templates")

# Thư mục lưu file tạm
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

# Giới hạn upload (1GB)
MAX_UPLOAD_SIZE = 1_000_000_000

# Biến toàn cục để lưu đường dẫn ffmpeg (sẽ khởi tạo khi cần)
_FFMPEG_PATH: Optional[str] = None
_FFPROBE_PATH: Optional[str] = None

def _init_ffmpeg():
    """Khởi tạo đường dẫn ffmpeg/ffprobe một cách an toàn, trả về (ffmpeg_path, ffprobe_path)."""
    global _FFMPEG_PATH, _FFPROBE_PATH
    if _FFMPEG_PATH is not None and _FFPROBE_PATH is not None:
        return _FFMPEG_PATH, _FFPROBE_PATH

    try:
        _FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
        _FFPROBE_PATH = imageio_ffmpeg.get_ffprobe_exe()
        # Kiểm tra nhanh xem binary có chạy được không
        import subprocess
        subprocess.run([_FFMPEG_PATH, "-version"], capture_output=True, timeout=10)
        subprocess.run([_FFPROBE_PATH, "-version"], capture_output=True, timeout=10)
        print(f"FFmpeg path: {_FFMPEG_PATH}")
        return _FFMPEG_PATH, _FFPROBE_PATH
    except Exception as e:
        raise RuntimeError(f"Không thể khởi tạo FFmpeg từ imageio-ffmpeg: {e}. "
                           "Hãy kiểm tra kết nối mạng hoặc cấu hình lại server.")


def get_video_duration(input_path: str) -> float:
    try:
        ffprobe_cmd = _init_ffmpeg()[1]
        probe = ffmpeg.probe(input_path, cmd=ffprobe_cmd)
        return float(probe['format']['duration'])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Không thể đọc video: {str(e)}")


def split_video(input_path: str, output_dir: str, mode: str, value: float):
    ffmpeg_cmd, ffprobe_cmd = _init_ffmpeg()
    duration = get_video_duration(input_path)  # đã gọi init

    if duration <= 0:
        raise HTTPException(status_code=400, detail="Video không có thời lượng hợp lệ.")

    segments = []
    if mode == "duration":
        seg_duration = value * 60  # phút -> giây
        if seg_duration <= 0:
            raise HTTPException(status_code=400, detail="Thời lượng mỗi phần phải > 0 phút.")
        num_segments = math.ceil(duration / seg_duration)
        for i in range(num_segments):
            start = i * seg_duration
            end = min((i + 1) * seg_duration, duration)
            if end > start:
                segments.append((start, end))
    elif mode == "count":
        num_segments = int(value)
        if num_segments <= 0:
            raise HTTPException(status_code=400, detail="Số lượng phần phải là số nguyên dương.")
        seg_duration = duration / num_segments
        for i in range(num_segments):
            start = i * seg_duration
            end = (i + 1) * seg_duration if i < num_segments - 1 else duration
            if end > start:
                segments.append((start, end))
    else:
        raise HTTPException(status_code=400, detail="Chế độ không hợp lệ (chỉ 'duration' hoặc 'count').")

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    part_files = []
    for idx, (start, end) in enumerate(segments, 1):
        output_file = os.path.join(output_dir, f"part_{idx:03d}.mp4")
        try:
            (
                ffmpeg
                .input(input_path, ss=start)
                .output(output_file, to=end, c='copy', map=0, avoid_negative_ts='make_zero')
                .run(cmd=ffmpeg_cmd, overwrite_output=True)
            )
            part_files.append(output_file)
        except ffmpeg.Error:
            # Fallback: re-encode nếu copy không được
            try:
                (
                    ffmpeg
                    .input(input_path, ss=start)
                    .output(output_file, to=end, vcodec='libx264', acodec='aac', avoid_negative_ts='make_zero')
                    .run(cmd=ffmpeg_cmd, overwrite_output=True)
                )
                part_files.append(output_file)
            except Exception as e2:
                raise HTTPException(status_code=500, detail=f"Lỗi cắt đoạn {idx}: {str(e2)}")
    return part_files


def create_zip(source_dir: str, zip_path: str):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(source_dir):
            for file in sorted(files):
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, source_dir)
                zf.write(full_path, arcname)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload-and-split")
async def upload_and_split(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    mode: str = Form(...),
    value: str = Form(...)
):
    if not video.filename:
        raise HTTPException(status_code=400, detail="Chưa chọn file video.")

    allowed_ext = ('.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv')
    if not video.filename.lower().endswith(allowed_ext):
        raise HTTPException(status_code=400, detail="Định dạng file không được hỗ trợ.")

    try:
        value_float = float(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="Giá trị tham số phải là số.")

    temp_id = uuid.uuid4().hex
    temp_dir = TEMP_DIR / temp_id
    temp_dir.mkdir(parents=True, exist_ok=True)

    input_video_path = temp_dir / f"input_{video.filename}"
    try:
        content = await video.read()
        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail="File video quá lớn (tối đa 1GB).")
        with open(input_video_path, "wb") as f:
            f.write(content)
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Lỗi khi lưu file: {str(e)}")

    parts_dir = temp_dir / "parts"
    zip_file_path = temp_dir / "split_videos.zip"

    try:
        split_video(str(input_video_path), str(parts_dir), mode, value_float)
        create_zip(str(parts_dir), str(zip_file_path))
    except HTTPException:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý: {str(e)}")

    if not zip_file_path.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail="Không tạo được file zip.")

    # Dọn dẹp thư mục tạm sau khi gửi file zip
    background_tasks.add_task(shutil.rmtree, str(temp_dir), ignore_errors=True)

    # Trả về file (KHÔNG truyền background=background_tasks)
    return FileResponse(
        path=str(zip_file_path),
        filename="split_videos.zip",
        media_type="application/zip"
    )


# Bắt sự kiện khởi động để kiểm tra ffmpeg trước (tùy chọn)
@app.on_event("startup")
async def startup_event():
    try:
        _init_ffmpeg()
        print("FFmpeg/FFprobe sẵn sàng.")
    except Exception as e:
        print(f"CẢNH BÁO: {e}")
        # Không raise để app vẫn chạy, nhưng sẽ lỗi khi cắt video
        pass
