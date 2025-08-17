(function () {
  // ================== TẠO CSS ==================
  const style = document.createElement("style");
  style.textContent = `
    @property --border-angle-1 { syntax: "<angle>"; inherits: true; initial-value: 0deg; }
    @property --border-angle-2 { syntax: "<angle>"; inherits: true; initial-value: 90deg; }
    @property --border-angle-3 { syntax: "<angle>"; inherits: true; initial-value: 180deg; }

    :root {
      --bright-blue: rgb(0, 100, 255);
      --bright-green: rgb(0, 255, 0);
      --bright-red: rgb(255, 0, 0);
      --background: black;
      --foreground: white;
      --border-size: 2px;
      --border-radius: 0.75em;
    }

    @keyframes rotateBackground { to { --border-angle-1: 360deg; } }
    @keyframes rotateBackground2 { to { --border-angle-2: -270deg; } }
    @keyframes rotateBackground3 { to { --border-angle-3: 540deg; } }

    .popup {
      position: fixed;
      top: 20px;
      left: 50%;
      transform: translateX(-50%) scale(0.5);
      z-index: 1000;
      opacity: 0;
      transition: transform 0.5s ease, opacity 0.5s ease;
      pointer-events: none;
      transform-origin: center center;
    }
    .popup.show { transform: translateX(-50%) scale(1); opacity: 1; }
    .popup.hide { transform: translateX(-50%) scale(0.5); opacity: 0; }

    .popup.gradient-border {
      --border-angle-1: 0deg;
      --border-angle-2: 90deg;
      --border-angle-3: 180deg;
      padding: var(--border-size);
      background-image: conic-gradient(
          from var(--border-angle-1) at 10% 15%,
          transparent,
          var(--bright-blue) 10%,
          transparent 30%,
          transparent
        ),
        conic-gradient(
          from var(--border-angle-2) at 70% 60%,
          transparent,
          var(--bright-green) 10%,
          transparent 60%,
          transparent
        ),
        conic-gradient(
          from var(--border-angle-3) at 50% 20%,
          transparent,
          var(--bright-red) 10%,
          transparent 50%,
          transparent
        );
      animation:
        rotateBackground 3s linear infinite,
        rotateBackground2 8s linear infinite,
        rotateBackground3 13s linear infinite;
      border-radius: var(--border-radius);
    }

    .popup-inner {
      background: var(--background);
      padding: 12px 24px;
      border-radius: calc(var(--border-radius) - var(--border-size));
      color: var(--foreground);
      font-size: 16px;
      font-weight: bold;
      white-space: nowrap;
    }

    .toast {
      position: fixed;
      bottom: 20px;
      left: 50%;
      transform: translateX(-50%);
      background: #1e1e2f;
      color: white;
      border-radius: 12px;
      padding: 10px 20px;
      display: flex;
      align-items: center;
      gap: 12px;
      max-width: 900px;
      z-index: 9999;
    }
    .toast span {
      flex: 1;
      white-space: normal;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  .toast-buttons {
  display: flex;
  justify-content: space-between;
  align-items: stretch;
  gap: 12px;
  width: 100%;
}

.toast-buttons button {
  flex: 1;                  /* Chia đều khoảng trống */
  min-width: 0;             /* Cho phép co nhỏ */
  height: 48px;
  padding: 0 10px;
  border-radius: 12px;
  font-size: 15px;
  line-height: 1.2;
  white-space: normal;       /* Cho phép chữ xuống dòng */
  word-break: break-word;    /* Xuống dòng nếu chữ quá dài */
}

    @media (max-width: 767px) {
      .toast {
        flex-direction: column;
        text-align: center;
        max-width: 90%;
        width: 90%;
        padding: 24px;
        font-size: 18px;
        border-radius: 20px;
      }
      .toast span { 
        white-space: normal; 
        margin-bottom: 20px; 
      }
      /* Giữ 2 nút nằm ngang, không đè lên nhau */
      .toast-buttons { 
        flex-direction: row; 
        flex-wrap: wrap;
        justify-content: center;
        width: 100%; 
        gap: 12px; 
      }
      .toast-buttons button {
        flex: 1;
        min-width: 120px;
        height: 48px;
        padding: 0 16px;
        border-radius: 12px;
      }
    }
  `;
  document.head.appendChild(style);

  // ================== TẠO HTML ==================
  const popup = document.createElement("div");
  popup.id = "popupNotification";
  popup.className = "popup gradient-border";
  popup.innerHTML = `<div class="popup-inner"></div>`;
  document.body.appendChild(popup);

  const toast = document.createElement("div");
  toast.id = "toast-prompt";
  toast.className = "toast";
  toast.innerHTML = `
    <img src="https://i.imgur.com/aGMqekz.gif">
    <span>Bạn có muốn cho phép vừa nghe nhạc vừa lướt trang web không?</span>
    <div class="toast-buttons">
      <button class="close-btn">Không hẹn lại lần sau</button>
      <button class="confirm-btn">Cho phép luôn</button>
    </div>
  `;
  document.body.appendChild(toast);

  // ================== JS CHÍNH ==================
  const songs = [
    { name: "Bài hát 1", file: "https://files.catbox.moe/22en11.mp3" },
    { name: "Bài hát 2", file: "song2.mp3" },
    { name: "Bài hát 3", file: "song3.mp3" },
    { name: "Bài hát 4", file: "song4.mp3" },
    { name: "Bài hát 5", file: "song5.mp3" }
  ];

  let currentAudio = null;
  let availableSongs = [...songs];

  function playRandomSong() {
    if (availableSongs.length === 0) {
      availableSongs = [...songs];
    }
    const randomIndex = Math.floor(Math.random() * availableSongs.length);
    const song = availableSongs.splice(randomIndex, 1)[0];

    if (currentAudio) {
      currentAudio.pause();
      currentAudio = null;
    }

    currentAudio = new Audio(song.file);
    currentAudio.play().catch(() => {});

    // Popup thông báo
    const popupInner = popup.querySelector(".popup-inner");
    popupInner.textContent = "🎵 Đang phát: " + song.name;
    popup.classList.add("show");
    setTimeout(() => {
      popup.classList.add("hide");
      setTimeout(() => popup.classList.remove("show", "hide"), 500);
    }, 3000);

    currentAudio.addEventListener("ended", playRandomSong);
    currentAudio.addEventListener("error", playRandomSong);
  }

  // Xử lý toast hỏi người dùng
  const confirmBtn = toast.querySelector(".confirm-btn");
  const closeBtn = toast.querySelector(".close-btn");

  confirmBtn.addEventListener("click", () => {
    toast.remove();
    playRandomSong();
  });
  closeBtn.addEventListener("click", () => {
    toast.remove();
  });
})();
