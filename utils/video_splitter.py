import os
import math
import zipfile
from pathlib import Path
from moviepy.video.io.VideoFileClip import VideoFileClip
import uuid

class VideoSplitter:
    def __init__(self, upload_folder="uploads", output_folder="outputs"):
        self.upload_folder = upload_folder
        self.output_folder = output_folder
        os.makedirs(upload_folder, exist_ok=True)
        os.makedirs(output_folder, exist_ok=True)
    
    def get_video_duration(self, video_path):
        """Lấy độ dài video (giây)"""
        with VideoFileClip(video_path) as clip:
            return clip.duration
    
    def split_by_duration(self, video_path, segment_duration_minutes):
        """Chế độ 1: Cắt theo thời lượng (phút)"""
        segment_duration = segment_duration_minutes * 60  # chuyển sang giây
        duration = self.get_video_duration(video_path)
        
        num_segments = math.ceil(duration / segment_duration)
        output_paths = []
        
        for i in range(num_segments):
            start_time = i * segment_duration
            end_time = min((i + 1) * segment_duration, duration)
            
            output_filename = f"part_{i+1:03d}.mp4"
            output_path = os.path.join(self.output_folder, output_filename)
            
            with VideoFileClip(video_path) as clip:
                subclip = clip.subclipped(start_time, end_time)
                subclip.write_videofile(
                    output_path,
                    codec='libx264',
                    audio_codec='aac',
                    verbose=False,
                    logger=None
                )
                subclip.close()
            
            output_paths.append(output_path)
        
        return output_paths
    
    def split_by_count(self, video_path, num_parts):
        """Chế độ 2: Cắt theo số lượng phần"""
        duration = self.get_video_duration(video_path)
        segment_duration = duration / num_parts
        
        output_paths = []
        
        for i in range(num_parts):
            start_time = i * segment_duration
            end_time = (i + 1) * segment_duration if i < num_parts - 1 else duration
            
            output_filename = f"part_{i+1:03d}.mp4"
            output_path = os.path.join(self.output_folder, output_filename)
            
            with VideoFileClip(video_path) as clip:
                subclip = clip.subclipped(start_time, end_time)
                subclip.write_videofile(
                    output_path,
                    codec='libx264',
                    audio_codec='aac',
                    verbose=False,
                    logger=None
                )
                subclip.close()
            
            output_paths.append(output_path)
        
        return output_paths
    
    def create_zip(self, file_paths, zip_name=None):
        """Tạo file zip từ danh sách các file"""
        if zip_name is None:
            zip_name = f"split_video_{uuid.uuid4().hex[:8]}.zip"
        
        zip_path = os.path.join(self.output_folder, zip_name)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in file_paths:
                zipf.write(file_path, os.path.basename(file_path))
        
        return zip_path
    
    def cleanup_files(self, *file_paths):
        """Dọn dẹp file rác để giải phóng bộ nhớ"""
        for file_path in file_paths:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Lỗi khi xóa file {file_path}: {e}")
    
    def cleanup_old_files(self, max_age_seconds=3600):
        """Dọn dẹp file cũ hơn 1 giờ (tùy chọn)"""
        import time
        now = time.time()
        for folder in [self.upload_folder, self.output_folder]:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                if os.path.isfile(file_path):
                    file_age = now - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        try:
                            os.remove(file_path)
                        except:
                            pass
