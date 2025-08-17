document.addEventListener("DOMContentLoaded", function () {
    // Tạo popup hỏi cho phép nghe nhạc
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.innerHTML = `
        <div class="toast-title">🎵 Bạn có muốn cho phép vừa nghe nhạc vừa lướt web không?</div>
        <div class="toast-buttons">
            <div class="toast-text">Không hẹn lại lần sau</div>
            <button id="allowMusic">Cho phép luôn</button>
        </div>
    `;
    document.body.appendChild(toast);

    // CSS style cho popup
    const style = document.createElement("style");
    style.innerHTML = `
    .toast {
        position: fixed !important;
        bottom: 20px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        background: #1e1e1e !important;
        color: #fff !important;
        padding: 16px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
        max-width: 90% !important;
        width: 400px !important;
        z-index: 99999 !important;
        text-align: center !important;
        font-family: sans-serif !important;
    }
    .toast-title {
        font-size: 16px !important;
        margin-bottom: 12px !important;
        font-weight: bold !important;
    }
    .toast-buttons {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        gap: 10px !important;
        width: 100% !important;
    }
    .toast-buttons .toast-text {
        width: 100% !important;
        text-align: center !important;
        font-size: 15px !important;
        margin-bottom: 8px !important;
        opacity: 0.8 !important;
    }
    .toast-buttons button {
        width: 100% !important;
        padding: 12px !important;
        font-size: 16px !important;
        border-radius: 8px !important;
        border: none !important;
        cursor: pointer !important;
        background: #007bff !important;
        color: white !important;
        font-weight: bold !important;
    }
    .toast-buttons button:hover {
        background: #0056b3 !important;
    }
    @media (max-width: 480px) {
      .toast {
        width: 95% !important;
        font-size: 14px !important;
      }
      .toast-buttons button {
        font-size: 14px !important;
        padding: 10px !important;
      }
    }
    `;
    document.head.appendChild(style);

    // Khi bấm Cho phép
    document.getElementById("allowMusic").addEventListener("click", function () {
        toast.remove();

        // Tạo audio player
        const audio = document.createElement("audio");
        audio.src = "https://cdn.pixabay.com/audio/2022/03/15/audio_7a7d92f1a5.mp3"; // Đổi link nhạc tại đây
        audio.autoplay = true;
        audio.loop = true;
        audio.volume = 0.7;
        document.body.appendChild(audio);

        // Hiển thị thông báo "Đang phát nhạc"
        const playingBox = document.createElement("div");
        playingBox.className = "playing-box";
        playingBox.innerHTML = "🎶 Đang phát nhạc...";
        document.body.appendChild(playingBox);

        // CSS cho thông báo "Đang phát nhạc"
        const playingStyle = document.createElement("style");
        playingStyle.innerHTML = `
        .playing-box {
            position: fixed !important;
            top: 20px !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
            background: #222 !important;
            color: #fff !important;
            padding: 10px 20px !important;
            border-radius: 20px !important;
            font-size: 15px !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
            z-index: 99999 !important;
        }
        `;
        document.head.appendChild(playingStyle);
    });
});
