// 生产环境请将下面的地址替换为你的 Render 后端地址
// 例如：const API_BASE = 'https://ai-music-generator-backend.onrender.com';
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:5000'
    : 'https://ai-music-generator-backend.onrender.com'; // 部署后替换为真实后端地址

// ===== 字符计数 =====
const promptInput = document.getElementById('prompt-input');
const charCount = document.getElementById('char-count');
promptInput.addEventListener('input', () => charCount.textContent = promptInput.value.length);

// ===== 通用选项组切换 =====
function bindOptionGroup(selector, hiddenInputId) {
    const buttons = document.querySelectorAll(selector);
    const input = document.getElementById(hiddenInputId);
    buttons.forEach(button => {
        button.addEventListener('click', function () {
            buttons.forEach(btn => {
                btn.classList.remove('bg-primary', 'text-white');
                btn.classList.add('bg-neutral-light', 'text-neutral-dark');
            });
            this.classList.remove('bg-neutral-light', 'text-neutral-dark');
            this.classList.add('bg-primary', 'text-white');
            input.value = this.dataset[hiddenInputId.replace('-input', '')];
        });
    });
}

bindOptionGroup('[data-lang]', 'lang-input');
bindOptionGroup('[data-style]', 'style-input');
bindOptionGroup('[data-type]', 'type-input');
bindOptionGroup('[data-duration]', 'duration-input');

// ===== 歌词区域切换（歌唱/伴奏） =====
const typeInput = document.getElementById('type-input');
const typeButtons = document.querySelectorAll('[data-type]');

function toggleLyricsSection() {
    const lyricsSection = document.getElementById('lyrics-section');
    if (typeInput.value === 'vocal') {
        lyricsSection.classList.remove('hidden');
    } else {
        lyricsSection.classList.add('hidden');
    }
}
typeButtons.forEach(btn => btn.addEventListener('click', () => setTimeout(toggleLyricsSection, 100)));
toggleLyricsSection();

// ===== AI 生成歌词 =====
const generateLyricsBtn = document.getElementById('generate-lyrics-btn');
const lyricsInput = document.getElementById('lyrics-input');
const lyricsLoading = document.getElementById('lyrics-loading');

generateLyricsBtn.addEventListener('click', async function () {
    const theme = promptInput.value.trim();
    if (!theme) { alert('请先输入音乐描述作为歌词主题'); return; }
    lyricsLoading.classList.remove('hidden');
    generateLyricsBtn.disabled = true;
    try {
        const res = await fetch(`${API_BASE}/api/v1/generate-lyrics`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ theme, style: 'pop' })
        });
        const data = await res.json();
        if (data.code === 200) {
            lyricsInput.value = data.data.lyrics;
        } else {
            alert('歌词生成失败：' + data.message);
        }
    } catch (e) {
        alert('歌词生成失败，请重试');
    } finally {
        lyricsLoading.classList.add('hidden');
        generateLyricsBtn.disabled = false;
    }
});

// ===== 生成音乐 =====
const generateBtn = document.getElementById('generate-music-btn');

generateBtn.addEventListener('click', async function () {
    const prompt = promptInput.value.trim();
    const duration = document.getElementById('duration-input').value;
    const musicType = typeInput.value;
    const musicLang = document.getElementById('lang-input').value;
    const musicStyle = document.getElementById('style-input').value;
    const lyrics = lyricsInput.value.trim();

    if (!prompt) {
        showError('请输入音乐描述');
        return;
    }

    hideMessages();
    const originalHTML = generateBtn.innerHTML;
    generateBtn.innerHTML = '<i class="fa fa-spinner fa-spin mr-2"></i> AI生成中（约2-4分钟）...';
    generateBtn.disabled = true;

    try {
        const requestBody = { prompt, duration: parseInt(duration), music_type: musicType, lang: musicLang, style: musicStyle };
        if (musicType === 'vocal' && lyrics) requestBody.lyrics = lyrics;

        const res = await fetch(`${API_BASE}/api/v1/generate-music`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        if (!res.ok) throw new Error('后端服务未响应');

        const data = await res.json();
        if (data.code === 200) {
            const musicList = data.data;
            if (musicList && musicList.length > 0) {
                playSelectedMusic(musicList[0]);
            }
            showSuccess('音乐生成成功！');
            setTimeout(() => loadHistory(), 2000);
        } else {
            showError(data.message || '生成失败');
        }
    } catch (error) {
        console.error('生成失败，使用示例音乐:', error);
        // 降级：使用免费示例音乐，直接播放
        const mockList = getMockMusicList(musicType, prompt, parseInt(duration));
        if (mockList.length > 0) {
            playSelectedMusic(mockList[0]);
        }
        showSuccess('已加载示例音乐');
    } finally {
        generateBtn.innerHTML = originalHTML;
        generateBtn.disabled = false;
    }
});

// ===== 降级示例音乐 =====
function getMockMusicList(musicType, prompt, duration) {
    const shortTitle = prompt.substring(0, 10);
    if (musicType === 'vocal') {
        return [
            {
                audio_url: "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/ccCommunity/Kai_Engel/Satin/Kai_Engel_-_04_-_Sentinel.mp3",
                duration,
                title: `流行抒情 - ${shortTitle}...`,
                lyrics: "🎵 主歌：\n在星光下起舞，心跳跟着节奏\n梦想在前方，我们不再停留\n每一个音符，都是新的追求\n让音乐带领我们，飞向那自由\n\n🎤 副歌：\n跟着节拍摇摆，让烦恼都走开\n这一刻只属于你和我\n音乐响起时，世界都变美好\n让我们一起唱这首歌",
                cover_url: "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400&h=400&fit=crop",
                music_type: musicType, source: "free-vocal"
            }
        ];
    }
    return [
        {
            audio_url: "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
            duration,
            title: `纯音乐 - ${shortTitle}...`,
            lyrics: "[纯音乐 - 无歌词]",
            cover_url: "https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=400&h=400&fit=crop",
            music_type: musicType, source: "mock"
        }
    ];
}

// ===== 消息提示 =====
function showError(msg) {
    const el = document.getElementById('error-message');
    el.textContent = msg;
    el.classList.remove('hidden');
}
function showSuccess(msg) {
    const el = document.getElementById('success-message');
    el.querySelector('span').textContent = msg;
    el.classList.remove('hidden');
    setTimeout(() => el.classList.add('hidden'), 3000);
}
function hideMessages() {
    document.getElementById('error-message').classList.add('hidden');
    document.getElementById('success-message').classList.add('hidden');
}

// ===== 歌曲选择界面（降级时使用） =====
function showMusicSelection(musicList) {
    document.getElementById('empty-state').classList.add('hidden');
    document.getElementById('music-player').classList.add('hidden');
    const container = document.getElementById('music-selection');
    container.classList.remove('hidden');

    const sourceHint = document.getElementById('music-source-hint');
    const src = musicList[0]?.source;
    if (src === 'minimax') sourceHint.innerHTML = '<i class="fa fa-magic text-purple-500 mr-1"></i> 由 MiniMax AI 生成';
    else if (src === 'free-vocal') sourceHint.innerHTML = '<i class="fa fa-music text-primary mr-1"></i> 免费音乐示例（带人声）';
    else sourceHint.innerHTML = '<i class="fa fa-info-circle text-amber-500 mr-1"></i> 演示模式';

    const grid = container.querySelector('.grid');
    grid.innerHTML = '';
    musicList.forEach(music => {
        const card = document.createElement('div');
        card.className = 'bg-white rounded-2xl p-6 shadow-md hover:shadow-xl transition-all cursor-pointer';
        card.innerHTML = `
            <div class="w-full aspect-square rounded-xl overflow-hidden mb-4 bg-neutral-light flex items-center justify-center">
                <img src="${music.cover_url}" alt="${music.title}" class="w-full h-full object-cover"
                     onerror="this.src='https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=300&h=300&fit=crop'">
            </div>
            <h4 class="font-serif font-bold text-neutral-black mb-1">${music.title}</h4>
            <div class="flex items-center justify-between text-xs mb-4">
                <span class="text-neutral-dark">${formatTime(music.duration)}</span>
                <span class="px-2 py-1 rounded bg-primary/10 text-primary">
                    <i class="fa fa-${music.music_type === 'vocal' ? 'microphone' : 'music'}"></i>
                </span>
            </div>
            <button class="w-full py-2 bg-primary text-white font-medium rounded-xl hover:bg-secondary transition-all">
                <i class="fa fa-play mr-2"></i> 播放
            </button>
        `;
        card.querySelector('button').addEventListener('click', () => playSelectedMusic(music));
        card.addEventListener('click', e => { if (!e.target.closest('button')) playSelectedMusic(music); });
        grid.appendChild(card);
    });
}

// ===== 播放器状态 =====
let durationCheckInterval = null;

// ===== 播放选定音乐 =====
async function playSelectedMusic(music) {
    document.getElementById('music-selection').classList.add('hidden');
    document.getElementById('empty-state').classList.add('hidden');
    document.getElementById('music-player').classList.remove('hidden');

    // 标题 & 时长
    document.getElementById('current-title').textContent = music.title;
    document.getElementById('current-duration').textContent = `时长：${formatTime(music.duration)}`;

    // 封面图片
    const coverImg = document.getElementById('current-cover');
    coverImg.src = (music.cover_url && music.cover_url.startsWith('http'))
        ? music.cover_url
        : 'https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=400&h=400&fit=crop';
    coverImg.onerror = () => {
        coverImg.src = 'https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=400&h=400&fit=crop';
    };

    // 类型标签
    const isVocal = music.music_type === 'vocal';
    document.getElementById('music-type-badge').innerHTML = isVocal
        ? '<i class="fa fa-microphone mr-1"></i> 歌唱'
        : '<i class="fa fa-music mr-1"></i> 伴奏';
    document.getElementById('lyrics-type').innerHTML = isVocal
        ? '<i class="fa fa-microphone mr-1"></i> 歌唱模式'
        : '<i class="fa fa-music mr-1"></i> 伴奏模式';

    // 渲染歌词
    const lyricsContainer = document.getElementById('lyrics-container');
    lyricsContainer.innerHTML = '';
    if (isVocal && music.lyrics) {
        music.lyrics.split('\n').filter(l => l.trim()).forEach((line, idx) => {
            const p = document.createElement('p');
            p.className = 'text-sm text-neutral-dark leading-relaxed text-center lyrics-line';
            p.textContent = line;
            if (idx === 0) p.classList.add('active');
            lyricsContainer.appendChild(p);
        });
    } else {
        const p = document.createElement('p');
        p.className = 'text-sm text-neutral-dark leading-relaxed text-center';
        p.textContent = music.lyrics || '[纯音乐 - 无歌词]';
        lyricsContainer.appendChild(p);
    }

    // 销毁旧音频
    if (durationCheckInterval) { clearInterval(durationCheckInterval); durationCheckInterval = null; }
    const oldAudio = document.getElementById('audio-element');
    if (oldAudio) { oldAudio.pause(); oldAudio.src = ''; oldAudio.load(); oldAudio.remove(); }

    // 创建新音频
    const audio = document.createElement('audio');
    audio.id = 'audio-element';
    audio.src = music.audio_url;
    document.body.appendChild(audio);

    const targetDuration = parseInt(music.duration) || 30;
    const progressFill = document.getElementById('progress-fill');
    const progressHandle = document.getElementById('progress-handle');
    const currentTimeEl = document.getElementById('current-time');
    const totalTimeEl = document.getElementById('total-time');
    const progressContainer = document.getElementById('progress-container');
    const volumeBar = document.getElementById('volume-bar');
    const albumSpin = document.getElementById('album-spin-container');

    function setProgress(pct) {
        progressFill.style.width = pct + '%';
        progressHandle.style.left = pct + '%';
    }

    // 替换播放按钮，清除旧事件
    const oldBtn = document.getElementById('play-pause-btn');
    const newBtn = oldBtn.cloneNode(true);
    oldBtn.parentNode.replaceChild(newBtn, oldBtn);

    function setPlaying(playing) {
        newBtn.innerHTML = playing
            ? '<i class="fa fa-pause text-2xl"></i>'
            : '<i class="fa fa-play text-2xl"></i>';
        if (albumSpin) {
            albumSpin.classList.toggle('paused', !playing);
        }
    }

    newBtn.onclick = () => {
        if (audio.paused) { audio.play(); setPlaying(true); }
        else { audio.pause(); setPlaying(false); }
    };

    // 进度更新 & 歌词滚动
    audio.addEventListener('timeupdate', () => {
        const t = audio.currentTime;
        const pct = Math.min((t / targetDuration) * 100, 100);
        setProgress(pct);
        currentTimeEl.textContent = formatTime(Math.min(t, targetDuration));

        // 歌词高亮滚动
        const lines = lyricsContainer.querySelectorAll('.lyrics-line');
        if (lines.length > 0) {
            const idx = Math.min(Math.floor((t / targetDuration) * lines.length), lines.length - 1);
            lines.forEach((line, i) => {
                line.classList.toggle('active', i === idx);
                if (i === idx) {
                    const lineTop = line.offsetTop - lyricsContainer.offsetTop;
                    lyricsContainer.scrollTo({ top: lineTop - lyricsContainer.clientHeight / 2 + line.clientHeight / 2, behavior: 'smooth' });
                }
            });
        }

        if (t >= targetDuration) {
            audio.pause();
            audio.currentTime = 0;
            setProgress(0);
            setPlaying(false);
        }
    });

    audio.addEventListener('loadedmetadata', () => { totalTimeEl.textContent = formatTime(targetDuration); });
    audio.addEventListener('ended', () => { setProgress(0); setPlaying(false); });

    // 进度条点击
    progressContainer.onclick = e => {
        const rect = progressContainer.getBoundingClientRect();
        const pct = Math.max(0, Math.min(((e.clientX - rect.left) / rect.width) * 100, 100));
        audio.currentTime = (pct / 100) * targetDuration;
        setProgress(pct);
    };

    // 进度条拖拽
    let dragging = false;
    progressHandle.onmousedown = e => { dragging = true; e.preventDefault(); };
    document.onmousemove = e => {
        if (!dragging) return;
        const rect = progressContainer.getBoundingClientRect();
        const pct = Math.max(0, Math.min(((e.clientX - rect.left) / rect.width) * 100, 100));
        setProgress(pct);
    };
    document.onmouseup = e => {
        if (!dragging) return;
        dragging = false;
        const rect = progressContainer.getBoundingClientRect();
        const pct = Math.max(0, Math.min(((e.clientX - rect.left) / rect.width) * 100, 100));
        audio.currentTime = (pct / 100) * targetDuration;
    };

    // 音量
    volumeBar.oninput = () => { audio.volume = volumeBar.value / 100; };

    // 初始化翻译功能
    initTranslation(music.lyrics || '');

    // 不自动播放，等待用户手动点击播放按钮
    audio.currentTime = 0;
    setPlaying(false);
    // 预加载音频
    audio.load();
}

// ===== 翻译功能 =====
let currentLyrics = '';
let isTranslated = false;

function initTranslation(lyrics) {
    currentLyrics = lyrics;
    isTranslated = false;
    const btn = document.getElementById('translate-btn');
    const container = document.getElementById('translation-container');
    const hasEnglish = /[a-zA-Z]{3,}/.test(lyrics);
    if (hasEnglish) {
        btn.classList.remove('hidden');
        btn.onclick = toggleTranslation;
    } else {
        btn.classList.add('hidden');
        container.classList.add('hidden');
    }
}

async function toggleTranslation() {
    const btn = document.getElementById('translate-btn');
    const container = document.getElementById('translation-container');
    const output = document.getElementById('translated-lyrics');
    if (isTranslated) {
        container.classList.add('hidden');
        btn.innerHTML = '<i class="fa fa-language mr-1"></i>翻译';
        isTranslated = false;
    } else {
        btn.innerHTML = '<i class="fa fa-spinner fa-spin mr-1"></i>翻译中...';
        output.textContent = currentLyrics.split('\n').map(line => {
            if (line.startsWith('[') && line.includes(']')) return line;
            if (/^[a-zA-Z\s.,!?]+$/.test(line.trim()) && line.trim().length > 3) return line + ' （英文歌词）';
            return line;
        }).join('\n');
        container.classList.remove('hidden');
        btn.innerHTML = '<i class="fa fa-eye-slash mr-1"></i>隐藏翻译';
        isTranslated = true;
    }
}

// ===== 返回按钮 =====
document.getElementById('back-to-empty').addEventListener('click', () => {
    document.getElementById('music-selection').classList.add('hidden');
    document.getElementById('empty-state').classList.remove('hidden');
});

document.getElementById('back-to-selection').addEventListener('click', () => {
    document.getElementById('music-player').classList.add('hidden');
    document.getElementById('music-selection').classList.add('hidden');
    document.getElementById('empty-state').classList.remove('hidden');
    const audio = document.getElementById('audio-element');
    if (audio) { audio.pause(); audio.src = ''; }
    const albumSpin = document.getElementById('album-spin-container');
    if (albumSpin) albumSpin.classList.add('paused');
    loadHistory();
});

// ===== 历史记录 =====
async function loadHistory() {
    const historyList = document.getElementById('history-list');
    const refreshBtn = document.getElementById('refresh-history');

    // 显示加载中状态
    historyList.innerHTML = '<p class="text-sm text-neutral-dark text-center py-4"><i class="fa fa-spinner fa-spin mr-2"></i>加载中...</p>';
    if (refreshBtn) {
        refreshBtn.disabled = true;
        refreshBtn.innerHTML = '<i class="fa fa-spinner fa-spin mr-1"></i>刷新中';
    }

    try {
        const res = await fetch(`${API_BASE}/api/v1/music-history`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (data.code === 200 && data.data.records.length > 0) {
            historyList.innerHTML = '';
            data.data.records.slice(0, 10).forEach(record => {
                const item = document.createElement('div');
                item.className = 'flex items-center space-x-3 p-3 bg-white rounded-xl hover:bg-neutral-light transition-colors cursor-pointer';
                const coverUrl = record.cover_url || 'https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=100&h=100&fit=crop';
                item.innerHTML = `
                    <img src="${coverUrl}" alt="封面" class="w-12 h-12 rounded-lg object-cover flex-shrink-0"
                         onerror="this.src='https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=100&h=100&fit=crop'">
                    <div class="flex-1 min-w-0">
                        <h4 class="text-sm font-medium text-neutral-black truncate">${record.title}</h4>
                        <p class="text-xs text-neutral-dark">${formatTime(record.duration)} · ${record.music_type === 'vocal' ? '歌唱' : '伴奏'}</p>
                    </div>
                    <button class="text-primary hover:text-accent flex-shrink-0">
                        <i class="fa fa-play-circle text-xl"></i>
                    </button>
                `;
                item.querySelector('button').addEventListener('click', () => playSelectedMusic(record));
                item.addEventListener('click', e => { if (!e.target.closest('button')) playSelectedMusic(record); });
                historyList.appendChild(item);
            });
        } else {
            historyList.innerHTML = '<p class="text-sm text-neutral-dark text-center py-4">暂无历史记录</p>';
        }
    } catch (err) {
        console.error('加载历史记录失败:', err);
        historyList.innerHTML = `<p class="text-sm text-red-500 text-center py-4"><i class="fa fa-exclamation-circle mr-1"></i>加载失败（${err.message}）</p>`;
    } finally {
        if (refreshBtn) {
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<i class="fa fa-refresh mr-1"></i>刷新';
        }
    }
}

document.getElementById('refresh-history').addEventListener('click', loadHistory);
loadHistory();

// ===== 工具函数 =====
function formatTime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}
