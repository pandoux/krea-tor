#!/bin/bash
# ============================================================
#  Krea-Tor — Script d'installation interactif
#  https://github.com/pandoux/krea-tor
# ============================================================

set -e

# ── Couleurs ─────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

ok()   { echo -e "${GREEN}✔ $1${NC}"; }
info() { echo -e "${CYAN}ℹ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠ $1${NC}"; }
err()  { echo -e "${RED}✘ $1${NC}"; exit 1; }
sep()  { echo -e "${CYAN}──────────────────────────────────────────${NC}"; }

clear
echo -e "${BOLD}"
cat << 'EOF'
  _  __                    _____
 | |/ /_ __ ___  __ _    |_   _|__  _ __
 | ' /| '__/ _ \/ _` |     | |/ _ \| '__|
 | . \| | |  __/ (_| |     | | (_) | |
 |_|\_\_|  \___|\__,_|     |_|\___/|_|

 Torrent Creator — Installation interactive
EOF
echo -e "${NC}"
sep

# ── Vérifications ─────────────────────────────────────────────
[[ $EUID -ne 0 ]] && err "Ce script doit être lancé en root (sudo ./install.sh)"
command -v python3 &>/dev/null || err "python3 non trouvé"

# ── Dépendances ───────────────────────────────────────────────
info "Installation des dépendances..."
apt-get update -qq
apt-get install -y -qq mktorrent python3-flask python3-requests
ok "Dépendances installées"
sep

# ── Adresse du serveur ────────────────────────────────────────
echo -e "${BOLD}📡 Adresse du serveur${NC}"
echo "Exemple : http://192.168.1.21"
read -rp "URL du serveur : " SERVER_URL
SERVER_URL="${SERVER_URL%/}"
[[ -z "$SERVER_URL" ]] && err "URL requise"

# ── Port de Krea-Tor ──────────────────────────────────────────
echo ""
echo -e "${BOLD}🔌 Port de Krea-Tor${NC}"
read -rp "Port d'écoute [défaut: 8081] : " KREATORT_PORT
KREATORT_PORT="${KREATORT_PORT:-8081}"

# ── qBittorrent ───────────────────────────────────────────────
sep
echo -e "${BOLD}⚙️  Connexion qBittorrent Web UI${NC}"
read -rp "Port qBittorrent [défaut: 8090] : " QBIT_PORT
QBIT_PORT="${QBIT_PORT:-8090}"
QBIT_URL="${SERVER_URL}:${QBIT_PORT}"

read -rp "Nom d'utilisateur qBittorrent [défaut: admin] : " QBIT_USER
QBIT_USER="${QBIT_USER:-admin}"

read -rsp "Mot de passe qBittorrent : " QBIT_PASS
echo ""
[[ -z "$QBIT_PASS" ]] && err "Mot de passe requis"

# Test de connexion qBittorrent
info "Test de connexion à qBittorrent ($QBIT_URL)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "${QBIT_URL}/api/v2/auth/login" \
  -d "username=${QBIT_USER}&password=${QBIT_PASS}" 2>/dev/null || echo "000")

if [[ "$HTTP_CODE" == "200" ]]; then
  ok "Connexion qBittorrent réussie"
else
  warn "Connexion qBittorrent échouée (code: $HTTP_CODE). Vous pourrez corriger dans config.json"
fi

# ── Répertoires médias ────────────────────────────────────────
sep
echo -e "${BOLD}📁 Répertoires des fichiers médias${NC}"
echo "Entrez les chemins un par un. Laissez vide pour terminer."
echo "Exemple : /media/MEDIAS"
echo ""

MEDIA_ROOTS=()
i=1
while true; do
  read -rp "Répertoire $i (vide pour terminer) : " DIR
  [[ -z "$DIR" ]] && break
  if [[ -d "$DIR" ]]; then
    MEDIA_ROOTS+=("$DIR")
    ok "Ajouté : $DIR"
    ((i++))
  else
    warn "Répertoire '$DIR' introuvable — ignoré"
  fi
done

[[ ${#MEDIA_ROOTS[@]} -eq 0 ]] && err "Aucun répertoire valide fourni"

# ── Trackers par défaut ───────────────────────────────────────
sep
echo -e "${BOLD}🔗 Tracker par défaut (optionnel)${NC}"
echo "Laissez vide pour aucun tracker pré-rempli"
read -rp "URL du tracker : " DEFAULT_TRACKER

# ── Génération config.json ────────────────────────────────────
sep
info "Création de /opt/krea-tor/config.json..."
mkdir -p /opt/krea-tor

# Construire le JSON des media_roots
ROOTS_JSON=$(printf '"%s",' "${MEDIA_ROOTS[@]}")
ROOTS_JSON="[${ROOTS_JSON%,}]"

cat > /opt/krea-tor/config.json << EOF
{
  "server_url": "${SERVER_URL}",
  "port": ${KREATORT_PORT},
  "media_roots": ${ROOTS_JSON},
  "default_trackers": "${DEFAULT_TRACKER}",
  "qbittorrent": {
    "url": "${QBIT_URL}",
    "username": "${QBIT_USER}",
    "password": "${QBIT_PASS}"
  }
}
EOF
ok "config.json créé"

# ── Copie de l'app ────────────────────────────────────────────
cp "$(dirname "$0")/app.py" /opt/krea-tor/app.py
ok "app.py copié dans /opt/krea-tor/"

# ── Service systemd ───────────────────────────────────────────
info "Création du service systemd..."
cat > /etc/systemd/system/krea-tor.service << EOF
[Unit]
Description=Krea-Tor — Torrent Creator Web UI
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/krea-tor/app.py
WorkingDirectory=/opt/krea-tor
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable krea-tor --now
ok "Service krea-tor démarré"

# ── Résumé ────────────────────────────────────────────────────
sep
echo -e "${BOLD}${GREEN}"
echo "  ✅ Installation terminée !"
echo -e "${NC}"
echo -e "  🌐 Interface web  : ${BOLD}${SERVER_URL}:${KREATORT_PORT}${NC}"
echo -e "  ⚙️  Config         : ${BOLD}/opt/krea-tor/config.json${NC}"
echo -e "  📋 Logs           : ${BOLD}journalctl -u krea-tor -f${NC}"
sep
