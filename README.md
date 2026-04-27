# 🧲 Krea-Tor v.1

**Krea-Tor** est une interface web légère pour créer des torrents directement sur un serveur Linux (LXC Proxmox, VPS, NAS...), sans avoir besoin d'un client bureau.

Conçu pour fonctionner aux côtés de **qBittorrent-WebUI** (https://community-scripts.org/scripts/qbittorrent), il comble l'absence du créateur de torrent graphique absent de la Web UI.
Peu gourmand, il s'installe directement sur l'hôte de **qBittorrent**

---

## ✨ Fonctionnalités

- 📁 Navigateur de fichiers intégré (multi-répertoires)
- 🧲 Création de torrent via `mktorrent`
- ➕ Ajout automatique dans qBittorrent pour seeder immédiatement
- ⬇️ Téléchargement du `.torrent` généré
- 🔒 Support des torrents privés
- ⚙️ Configuration centralisée dans un fichier JSON
- 🎁 **A venir :** Génération automatique de .nfo

---

## 📋 Prérequis

- Debian/Ubuntu (ou dérivé)
- Python 3
- qBittorrent-nox avec Web UI activée
- Git

---

## 🚀 Installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/pandoux/krea-tor.git
cd krea-tor

# 2. Rendre le script exécutable
chmod +x install.sh

# 3. Lancer l'installation interactive (en root)
sudo ./install.sh
```

**Le script vous demandera interactivement :**
- L'adresse et le port de votre serveur
- Les identifiants qBittorrent
- Les répertoires où sont stockés vos médias (pensez à repérer le point de montage en amont et à le noter)
- Un tracker par défaut (optionnel) permettant l'ajout de votre passkey sur un tracker privé

---


## 🧲 Utilisation

- Connexion à la page web : [IP_DU_SERVEUR]:8081 (Port par défaut modifiable)
- Choix de la source si sources multiples
- Options : Choix du nom du torrent, taille des pièces, gestion manuelle du ou des trackers...
- Création du torrent : Ajout direct dans qBittorrent si l'option a été cochée et possibilité de télécharger le fichier *.torrent

---

## ⚙️ Configuration manuelle

La configuration est stockée dans `/opt/krea-tor/config.json` :

```json
{
  "server_url": "http://192.168.1.21",
  "port": 8081,
  "media_roots": [
    "/media/MEDIAS",
    "/media/MEDIAS2"
  ],
  "default_trackers": "https://montracker.org/announce/PASSKEY",
  "qbittorrent": {
    "url": "http://192.168.1.21:8090",
    "username": "admin",
    "password": "monmotdepasse"
  }
}
```

Après modification :
```bash
sudo systemctl restart krea-tor
```

---

## 🛠️ Commandes utiles

```bash
# Statut du service
sudo systemctl status krea-tor

# Logs en direct
sudo journalctl -u krea-tor -f

# Redémarrer
sudo systemctl restart krea-tor

# Désinstaller
sudo systemctl disable krea-tor --now
sudo rm -rf /opt/krea-tor /etc/systemd/system/krea-tor.service
```

---

## 📜 Licence

MIT
