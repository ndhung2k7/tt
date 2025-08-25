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
      transform: translateX(-50%) translateY(-30px);
      z-index: 1000;
      opacity: 0;
      transition: transform 0.5s ease, opacity 0.5s ease;
      pointer-events: none;
      max-width: 90%;
    }
    .popup.show { 
      transform: translateX(-50%) translateY(0);
      opacity: 1; 
    }
    .popup.hide { 
      transform: translateX(-50%) translateY(-30px);
      opacity: 0; 
    }

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
      text-align: center;
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
    .toast-buttons { display: flex; gap: 12px; align-items: center; margin: 0; }
    .toast button {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      height: 40px;
      padding: 0 16px;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      font-weight: 600;
      font-size: 16px;
      white-space: nowrap;
      line-height: 1;
    }
    .toast .toast-close-btn { background-color: transparent; color: #bbb; }
    .toast .confirm-btn { background-color: #0d6efd; color: white; }
    .toast img { width: 40px; height: 40px; }

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
      .toast span { white-space: normal; margin-bottom: 20px; }
      .toast-buttons { flex-direction: column; width: 100%; gap: 12px; }
      .toast-buttons button {
        width: 100%;
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
      <button class="toast-close-btn">Không hẹn lại lần sau</button>
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
    }, 4000);

    currentAudio.addEventListener("ended", playRandomSong);
    currentAudio.addEventListener("error", playRandomSong);
  }

  // Xử lý toast hỏi người dùng
  const confirmBtn = toast.querySelector(".confirm-btn");
  const closeBtn = toast.querySelector(".toast-close-btn");

  confirmBtn.addEventListener("click", () => {
    toast.remove();
    playRandomSong();
  });
  closeBtn.addEventListener("click", () => {
    toast.remove();
  });
})();
