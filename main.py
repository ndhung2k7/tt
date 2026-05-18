import os
import uuid
import shutil
import math
import zipfile
from pathlib import Path
from tempfile import mkdtemp

from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import ffmpeg
import imageio_ffmpeg

app = FastAPI(title="Video Splitter", version="1.0.0")

# Cấu hình đường dẫn đến ffmpeg/ffprobe từ imageio (đảm bảo có binary ngay cả khi máy chủ không cài sẵn)
FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
FFPROBE_PATH = imageio_ffmpeg.get_ffprobe_exe()

# Thư mục lưu file tạm (tạo tự động nếu chưa có)
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

# Cấu hình Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Giới hạn kích thước upload (1000MB) - có thể điều chỉnh
MAX_UPLOAD_SIZE = 1_000_000_000  # 1GB


def get_video_duration(input_path: str) -> float:
    """Lấy thời lượng video bằng ffprobe."""
    try:
        probe = ffmpeg.probe(input_path, cmd=FFPROBE_PATH)
        duration = float(probe['format']['duration'])
        return duration
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Không thể đọc video: {str(e)}")


def split_video(input_path: str, output_dir: str, mode: str, value: float):
    """Cắt video thành nhiều phần và lưu vào output_dir."""
    duration = get_video_duration(input_path)
    if duration <= 0:
        raise HTTPException(status_code=400, detail="Video không có thời lượng hợp lệ.")

    segments = []
    if mode == "duration":
        seg_duration = value * 60  # đổi phút -> giây
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
        raise HTTPException(status_code=400, detail="Chế độ không hợp lệ (chỉ chấp nhận 'duration' hoặc 'count').")

    # Tạo thư mục output nếu chưa có
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    part_files = []
    for idx, (start, end) in enumerate(segments, 1):
        output_file = os.path.join(output_dir, f"part_{idx:03d}.mp4")
        try:
            (
                ffmpeg
                .input(input_path, ss=start)
                .output(output_file, to=end, c='copy', map=0, avoid_negative_ts='make_zero')
                .run(cmd=FFMPEG_PATH, overwrite_output=True)
            )
            part_files.append(output_file)
        except ffmpeg.Error as e:
            # Nếu copy không được, thử re-encode (tốn tài nguyên hơn nhưng an toàn)
            try:
                (
                    ffmpeg
                    .input(input_path, ss=start)
                    .output(output_file, to=end, vcodec='libx264', acodec='aac', avoid_negative_ts='make_zero')
                    .run(cmd=FFMPEG_PATH, overwrite_output=True)
                )
                part_files.append(output_file)
            except Exception as e2:
                raise HTTPException(status_code=500, detail=f"Lỗi cắt đoạn {idx}: {str(e2)}")

    return part_files


def create_zip(source_dir: str, zip_path: str):
    """Nén tất cả file trong source_dir thành file zip."""
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
    # Kiểm tra file rỗng
    if not video.filename:
        raise HTTPException(status_code=400, detail="Chưa chọn file video.")

    # Kiểm tra định dạng cho phép
    allowed_ext = ('.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv')
    if not video.filename.lower().endswith(allowed_ext):
        raise HTTPException(status_code=400, detail="Định dạng file không được hỗ trợ.")

    # Chuyển đổi value
    try:
        if mode == "duration":
            value_float = float(value)
        else:
            value_float = float(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="Giá trị tham số phải là số.")

    # Tạo thư mục tạm duy nhất
    temp_id = uuid.uuid4().hex
    temp_dir = TEMP_DIR / temp_id
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Lưu file upload
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

    # Thư mục chứa các phần đã cắt
    parts_dir = temp_dir / "parts"
    zip_file_path = temp_dir / "split_videos.zip"

    try:
        # Cắt video
        split_video(str(input_video_path), str(parts_dir), mode, value_float)

        # Nén thành zip
        create_zip(str(parts_dir), str(zip_file_path))

    except HTTPException:
        # Dọn dẹp nếu lỗi
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý: {str(e)}")

    # Đọc kích thước file zip
    if not zip_file_path.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail="Không tạo được file zip.")

    # Lên lịch dọn dẹp thư mục tạm SAU KHI gửi file xong
    background_tasks.add_task(shutil.rmtree, str(temp_dir), ignore_errors=True)

    # Trả file zip cho client
    return FileResponse(
        path=str(zip_file_path),
        filename="split_videos.zip",
        media_type="application/zip",
        background=background_tasks  # không cần thiết vì đã thêm ở trên, nhưng để rõ ràng
    )
