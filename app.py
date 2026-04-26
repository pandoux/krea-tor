#!/usr/bin/env python3
"""
Krea-Tor — Torrent Creator Web UI
https://github.com/pandoux/krea-tor
"""

from flask import Flask, render_template_string, request, jsonify, send_file
import subprocess, os, json, requests

app = Flask(__name__)

# ─── Config (générée par install.sh) ────────────────────────────────────────
CONFIG_FILE = "/opt/krea-tor/config.json"

def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)

# ─── HTML ────────────────────────────────────────────────────────────────────
HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Krea-Tor</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #1a1a2e; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; min-height: 100vh; }
  .header { background: linear-gradient(135deg, #16213e, #0f3460); padding: 20px 30px; display: flex; align-items: center; gap: 15px; border-bottom: 2px solid #e94560; }
  .header h1 { font-size: 1.5rem; color: #fff; }
  .header .sub { color: #a0aec0; font-size: 0.85rem; }
  .container { max-width: 950px; margin: 30px auto; padding: 0 20px; }
  .card { background: #16213e; border-radius: 12px; padding: 25px; margin-bottom: 20px; border: 1px solid #0f3460; }
  .card h2 { font-size: 1rem; color: #e94560; margin-bottom: 18px; text-transform: uppercase; letter-spacing: 1px; }
  label { display: block; color: #a0aec0; font-size: 0.85rem; margin-bottom: 6px; margin-top: 14px; }
  label:first-of-type { margin-top: 0; }
  input[type=text], textarea, select {
    width: 100%; padding: 10px 14px; border-radius: 8px;
    border: 1px solid #0f3460; background: #0f3460;
    color: #e0e0e0; font-size: 0.9rem; outline: none;
    transition: border-color .2s;
  }
  input:focus, textarea:focus, select:focus { border-color: #e94560; }
  textarea { resize: vertical; min-height: 80px; font-family: monospace; }
  .row { display: flex; gap: 15px; }
  .row > div { flex: 1; }
  .checkbox-row { display: flex; align-items: center; gap: 10px; margin-top: 14px; }
  .checkbox-row input { width: auto; }
  .checkbox-row label { margin: 0; color: #e0e0e0; }
  .browser { background: #0a1628; border-radius: 8px; border: 1px solid #0f3460; max-height: 280px; overflow-y: auto; }
  .browser-item { padding: 8px 14px; cursor: pointer; display: flex; align-items: center; gap: 10px; font-size: 0.88rem; border-bottom: 1px solid #0f3460; transition: background .15s; }
  .browser-item:hover { background: #1a3a5c; }
  .browser-item.selected { background: #1e4d7a; border-left: 3px solid #e94560; }
  .browser-item.folder { color: #63b3ed; }
  .browser-item.file   { color: #e0e0e0; }
  .breadcrumb { padding: 10px 14px; background: #0d2137; border-radius: 8px 8px 0 0; font-size: 0.82rem; color: #a0aec0; border-bottom: 1px solid #0f3460; }
  .breadcrumb span { color: #e94560; cursor: pointer; }
  .breadcrumb span:hover { text-decoration: underline; }
  .btn { padding: 12px 28px; border-radius: 8px; border: none; cursor: pointer; font-size: 0.95rem; font-weight: 600; transition: all .2s; }
  .btn-primary { background: #e94560; color: #fff; }
  .btn-primary:hover { background: #c73652; }
  .btn-primary:disabled { background: #555; cursor: not-allowed; }
  .btn-secondary { background: #0f3460; color: #e0e0e0; }
  .btn-secondary:hover { background: #1a4a7a; }
  .selected-path { padding: 10px 14px; background: #0f3460; border-radius: 8px; margin-top: 10px; font-family: monospace; font-size: 0.85rem; color: #68d391; min-height: 40px; }
  .log { background: #0a1628; border-radius: 8px; padding: 14px; font-family: monospace; font-size: 0.82rem; min-height: 80px; max-height: 200px; overflow-y: auto; border: 1px solid #0f3460; white-space: pre-wrap; }
  .log .ok   { color: #68d391; }
  .log .err  { color: #fc8181; }
  .log .info { color: #63b3ed; }
  .progress-bar { width: 100%; background: #0f3460; border-radius: 99px; height: 8px; margin: 12px 0; overflow: hidden; display: none; }
  .progress-bar-inner { height: 100%; background: linear-gradient(90deg, #e94560, #f6ad55); border-radius: 99px; width: 0%; transition: width .3s; animation: pulse 1.5s infinite; }
  @keyframes pulse { 0%,100%{opacity:1}50%{opacity:.7} }
  .actions { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
  .badge { padding: 4px 10px; border-radius: 99px; font-size: 0.75rem; font-weight: 600; }
  .badge-green { background: #276749; color: #68d391; }
  .badge-red   { background: #742a2a; color: #fc8181; }
  .root-tabs { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
  .root-tab { padding: 6px 14px; border-radius: 99px; background: #0f3460; color: #a0aec0; cursor: pointer; font-size: 0.82rem; border: 1px solid transparent; transition: all .2s; }
  .root-tab.active { background: #e94560; color: #fff; border-color: #e94560; }
</style>
</head>
<body>
<div class="header">
  <div>
    <h1>🧲 Krea-Tor</h1>
    <div class="sub" id="headerSub">Chargement...</div>
  </div>
</div>

<div class="container">

  <div class="card">
    <h2>📁 Source</h2>
    <div class="root-tabs" id="rootTabs"></div>
    <div class="breadcrumb" id="breadcrumb">Chargement...</div>
    <div class="browser" id="browser">Chargement...</div>
    <div class="selected-path" id="selectedPath">Aucun fichier/dossier sélectionné</div>
  </div>

  <div class="card">
    <h2>⚙️ Options</h2>
    <div class="row">
      <div>
        <label>Nom du torrent (optionnel)</label>
        <input type="text" id="torrentName" placeholder="Laissez vide = nom du fichier/dossier">
      </div>
      <div>
        <label>Taille des pièces</label>
        <select id="pieceSize">
          <option value="0">Auto</option>
          <option value="15">256 Ko</option>
          <option value="16">512 Ko</option>
          <option value="17">1 Mo</option>
          <option value="18">2 Mo</option>
          <option value="19">4 Mo</option>
          <option value="20">8 Mo</option>
        </select>
      </div>
    </div>
    <label>Trackers (un par ligne)</label>
    <textarea id="trackers" id="trackers"></textarea>
    <div class="checkbox-row">
      <input type="checkbox" id="isPrivate">
      <label for="isPrivate">🔒 Torrent privé (désactive DHT/PEX)</label>
    </div>
    <div class="checkbox-row">
      <input type="checkbox" id="autoAdd" checked>
      <label for="autoAdd">➕ Ajouter automatiquement dans qBittorrent pour seeder</label>
    </div>
  </div>

  <div class="card">
    <h2>🚀 Création</h2>
    <div class="actions">
      <button class="btn btn-primary" id="btnCreate" onclick="createTorrent()">Créer le torrent</button>
      <button class="btn btn-secondary" id="btnDownload" style="display:none" onclick="downloadTorrent()">⬇️ Télécharger le .torrent</button>
      <span id="statusBadge"></span>
    </div>
    <div class="progress-bar" id="progressBar"><div class="progress-bar-inner" id="progressInner"></div></div>
    <div class="log" id="log">En attente...</div>
  </div>

</div>

<script>
let cfg = {};
let currentRoot = '';
let currentPath = '';
let selectedPath = '';
let currentTorrentFile = '';

fetch('/api/config').then(r => r.json()).then(c => {
  cfg = c;
  document.getElementById('headerSub').textContent = 'qBittorrent · ' + c.media_roots.join(' · ');
  document.getElementById('trackers').value = c.default_trackers || '';

  // Onglets racines
  const tabs = document.getElementById('rootTabs');
  c.media_roots.forEach((root, i) => {
    const tab = document.createElement('div');
    tab.className = 'root-tab' + (i === 0 ? ' active' : '');
    tab.textContent = root;
    tab.onclick = () => {
      document.querySelectorAll('.root-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      currentRoot = root;
      loadDir(root);
    };
    tabs.appendChild(tab);
  });

  currentRoot = c.media_roots[0];
  loadDir(currentRoot);
});

function loadDir(path) {
  currentPath = path;
  fetch('/api/browse?path=' + encodeURIComponent(path))
    .then(r => r.json())
    .then(data => renderBrowser(data, path));
}

function renderBrowser(items, path) {
  const rel = path.replace(currentRoot, '') || '/';
  const parts = rel.split('/').filter(Boolean);
  let bc = `<span onclick="loadDir('${currentRoot}')">📂 ${currentRoot}</span>`;
  let built = currentRoot;
  parts.forEach(p => {
    built += '/' + p;
    const b = built;
    bc += ` / <span onclick="loadDir('${b}')">${p}</span>`;
  });
  document.getElementById('breadcrumb').innerHTML = bc;

  let html = '';
  if (path !== currentRoot) {
    const parent = path.substring(0, path.lastIndexOf('/')) || currentRoot;
    html += `<div class="browser-item folder" onclick="loadDir('${parent}')">⬆️ ..</div>`;
  }
  if (!items || items.length === 0) {
    html += `<div class="browser-item" style="color:#666">Dossier vide</div>`;
  }
  (items || []).forEach(item => {
    const icon = item.type === 'dir' ? '📁' : '🎬';
    const cls = item.type === 'dir' ? 'folder' : 'file';
    const full = path + '/' + item.name;
    const onclick = item.type === 'dir' ? `selectItem('${full}', true)` : `selectItem('${full}', false)`;
    const dblclick = item.type === 'dir' ? `loadDir('${full}')` : '';
    html += `<div class="browser-item ${cls}" onclick="${onclick}" ondblclick="${dblclick}" data-path="${full}">
      ${icon} ${item.name} <span style="color:#555;font-size:.75rem;margin-left:auto">${item.size||''}</span>
    </div>`;
  });
  document.getElementById('browser').innerHTML = html;
}

function selectItem(path, isDir) {
  selectedPath = path;
  document.querySelectorAll('.browser-item').forEach(el => el.classList.remove('selected'));
  const el = document.querySelector(`[data-path="${path}"]`);
  if (el) el.classList.add('selected');
  document.getElementById('selectedPath').textContent = '✅ ' + path + (isDir ? '  [dossier entier]' : '');
  if (isDir) loadDir(path);
}

function log(msg, type='info') {
  const el = document.getElementById('log');
  el.innerHTML += `<span class="${type}">${msg}</span>\n`;
  el.scrollTop = el.scrollHeight;
}

function createTorrent() {
  if (!selectedPath) { alert('Sélectionnez un fichier ou dossier source !'); return; }
  const btn = document.getElementById('btnCreate');
  btn.disabled = true;
  document.getElementById('btnDownload').style.display = 'none';
  document.getElementById('statusBadge').innerHTML = '';
  document.getElementById('log').innerHTML = '';
  document.getElementById('progressBar').style.display = 'block';
  document.getElementById('progressInner').style.width = '30%';
  log('Démarrage de la création...', 'info');

  fetch('/api/create', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      source: selectedPath,
      name: document.getElementById('torrentName').value,
      trackers: document.getElementById('trackers').value,
      piece_size: document.getElementById('pieceSize').value,
      private: document.getElementById('isPrivate').checked,
      auto_add: document.getElementById('autoAdd').checked,
    })
  }).then(r => r.json()).then(data => {
    document.getElementById('progressInner').style.width = '100%';
    setTimeout(() => document.getElementById('progressBar').style.display = 'none', 800);
    if (data.ok) {
      log('✅ Torrent créé : ' + data.torrent_file, 'ok');
      if (data.added_to_qbit) log('➕ Ajouté dans qBittorrent avec succès !', 'ok');
      if (data.warning) log('⚠️ ' + data.warning, 'err');
      currentTorrentFile = data.torrent_file;
      document.getElementById('btnDownload').style.display = 'inline-block';
      document.getElementById('statusBadge').innerHTML = '<span class="badge badge-green">✓ Succès</span>';
    } else {
      log('❌ Erreur : ' + data.error, 'err');
      document.getElementById('statusBadge').innerHTML = '<span class="badge badge-red">✗ Échec</span>';
    }
    btn.disabled = false;
  }).catch(e => {
    log('❌ Erreur réseau : ' + e, 'err');
    btn.disabled = false;
  });
}

function downloadTorrent() {
  window.location = '/api/download?file=' + encodeURIComponent(currentTorrentFile);
}
</script>
</body>
</html>
"""

OUTPUT_DIR = "/tmp/krea-tor"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def fmt_size(b):
    for u in ['o','Ko','Mo','Go','To']:
        if b < 1024: return f"{b:.1f} {u}"
        b /= 1024
    return f"{b:.1f} Po"

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/config')
def api_config():
    cfg = load_config()
    return jsonify({
        'media_roots': cfg['media_roots'],
        'default_trackers': cfg.get('default_trackers', ''),
    })

@app.route('/api/browse')
def browse():
    cfg = load_config()
    path = request.args.get('path', cfg['media_roots'][0])
    if not any(path.startswith(r) for r in cfg['media_roots']):
        return jsonify([])
    try:
        items = []
        for name in sorted(os.listdir(path)):
            if name.startswith('.'): continue
            full = os.path.join(path, name)
            t = 'dir' if os.path.isdir(full) else 'file'
            size = '' if t == 'dir' else fmt_size(os.path.getsize(full))
            items.append({'name': name, 'type': t, 'size': size})
        return jsonify(items)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/create', methods=['POST'])
def create():
    cfg = load_config()
    data = request.json
    source = data.get('source', '')
    if not any(source.startswith(r) for r in cfg['media_roots']):
        return jsonify({'ok': False, 'error': 'Chemin non autorisé'})

    name = data.get('name', '').strip() or os.path.basename(source.rstrip('/'))
    trackers = [t.strip() for t in data.get('trackers', '').splitlines() if t.strip()]
    piece_size = data.get('piece_size', '0')
    is_private = data.get('private', False)
    auto_add = data.get('auto_add', True)
    out_file = os.path.join(OUTPUT_DIR, name.replace('/', '_') + '.torrent')

    cmd = ['mktorrent', '-n', name, '-o', out_file]
    for t in trackers: cmd += ['-a', t]
    if piece_size != '0': cmd += ['-l', piece_size]
    if is_private: cmd += ['-p']
    cmd.append(source)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            return jsonify({'ok': False, 'error': result.stderr or result.stdout})
    except subprocess.TimeoutExpired:
        return jsonify({'ok': False, 'error': 'Timeout — fichier trop volumineux ?'})
    except FileNotFoundError:
        return jsonify({'ok': False, 'error': 'mktorrent non installé : apt install mktorrent'})

    warning, added = None, False
    if auto_add:
        try:
            qbit = cfg['qbittorrent']
            s = requests.Session()
            s.post(f"{qbit['url']}/api/v2/auth/login",
                   data={'username': qbit['username'], 'password': qbit['password']}, timeout=5)
            with open(out_file, 'rb') as f:
                r = s.post(f"{qbit['url']}/api/v2/torrents/add",
                           files={'torrents': (os.path.basename(out_file), f, 'application/x-bittorrent')},
                           data={'savepath': os.path.dirname(source), 'autoTMM': 'false'},
                           timeout=10)
            added = r.status_code == 200
            if not added: warning = f"qBittorrent API: {r.status_code} {r.text}"
        except Exception as e:
            warning = f"Impossible de contacter qBittorrent: {e}"

    return jsonify({'ok': True, 'torrent_file': out_file, 'added_to_qbit': added, 'warning': warning})

@app.route('/api/download')
def download():
    f = request.args.get('file', '')
    if not f.startswith(OUTPUT_DIR):
        return "Interdit", 403
    return send_file(f, as_attachment=True)

if __name__ == '__main__':
    cfg = load_config()
    port = cfg.get('port', 8081)
    app.run(host='0.0.0.0', port=port, debug=False)
