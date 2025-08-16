const songs = [
  { name: "Bài hát 1", file: "https://files.catbox.moe/22en11.mp3" },
  { name: "Bài hát 2", file: "song2.mp3" },
  { name: "Bài hát 3", file: "song3.mp3" },
  { name: "Bài hát 4", file: "song4.mp3" },
  { name: "Bài hát 5", file: "song5.mp3" },
];

let currentAudio = null;

function playRandomSong() {
  const randomIndex = Math.floor(Math.random() * songs.length);
  const song = songs[randomIndex];

  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }

  currentAudio = new Audio(song.file);
  currentAudio.play();

  const popup = document.getElementById('popupNotification');
  const popupInner = popup.querySelector('.popup-inner');
  popupInner.textContent = '🎵 Đang phát: ' + song.name;

  popup.classList.add('show');
  setTimeout(() => {
    popup.classList.add('hide');
    setTimeout(() => {
      popup.classList.remove('show', 'hide');
    }, 500);
  }, 3000);

  currentAudio.addEventListener('ended', function () {
    playRandomSong();
  });
}

document.addEventListener('DOMContentLoaded', () => {
  const toast = document.getElementById('toast-prompt');
  const allowBtn = document.querySelector('.toast-accept');
  const declineBtn = document.querySelector('.toast-decline');

  allowBtn.addEventListener('click', () => {
    toast.remove();
    playRandomSong();
  });

  declineBtn.addEventListener('click', () => {
    toast.remove();
  });
});
