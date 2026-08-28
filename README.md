<div align="center">

<h1>
  🎬 slim-video
</h1>

<p>
  <b>Libérez 40% à 65% d'espace disque sur votre bibliothèque vidéo sans perte visuelle ni audio — accéléré matériellement sur Apple Silicon.</b>
</p>

<p>
  <a href="https://github.com/Boblebol/slim-video/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/Boblebol/slim-video/ci.yml?branch=main&style=flat-square&logo=githubactions&logoColor=white&label=CI" alt="CI Status"></a>
  <a href="https://github.com/Boblebol/slim-video/actions/workflows/ci.yml"><img src="https://img.shields.io/badge/coverage-81%25-brightgreen.svg?style=flat-square&logo=pytest&logoColor=white" alt="Coverage 81%"></a>
  <a href="https://github.com/Boblebol/slim-video/releases"><img src="https://img.shields.io/badge/version-1.5.2-blue.svg?style=flat-square&logo=git&logoColor=white" alt="Version 1.5.2"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.9%20|%203.10%20|%203.11%20|%203.12%20|%203.13-3776AB.svg?style=flat-square&logo=python&logoColor=white" alt="Python Versions"></a>
  <a href="https://github.com/astral-sh/uv"><img src="https://img.shields.io/badge/package%20manager-uv-DE5FE9.svg?style=flat-square&logo=uv&logoColor=white" alt="uv"></a>
  <a href="https://docs.pydantic.dev/"><img src="https://img.shields.io/badge/data%20models-Pydantic%20v2-E92063.svg?style=flat-square&logo=pydantic&logoColor=white" alt="Pydantic v2"></a>
</p>
<p>
  <a href="https://mypy.readthedocs.io/"><img src="https://img.shields.io/badge/type%20checker-mypy%20strict-2F6393.svg?style=flat-square&logo=python&logoColor=white" alt="mypy strict"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/badge/code%20style-Ruff-D7FF64.svg?style=flat-square&logo=ruff&logoColor=black" alt="Ruff"></a>
  <a href="https://www.conventionalcommits.org/"><img src="https://img.shields.io/badge/commits-Conventional-FE5196.svg?style=flat-square&logo=conventionalcommits&logoColor=white" alt="Conventional Commits"></a>
  <a href="https://www.apple.com/"><img src="https://img.shields.io/badge/platform-macOS%20Apple%20Silicon-999999.svg?style=flat-square&logo=apple&logoColor=white" alt="macOS Apple Silicon"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg?style=flat-square" alt="License MIT"></a>
</p>

<br>

<p align="center">
  <a href="#-démarrage-rapide-en-30-secondes"><b>🚀 Démarrage Rapide</b></a> •
  <a href="#-pourquoi-slim-video-"><b>✨ Pourquoi slim-video ?</b></a> •
  <a href="#-aperçu-de-linterface"><b>🖥 Interface & TUI</b></a> •
  <a href="DOCUMENTATION.md"><b>📚 Documentation Complète</b></a> •
  <a href="CHANGELOG.md"><b>📦 Changelog</b></a>
</p>

</div>

---

> [!TIP]
> **Consultez le guide complet :** Pour la référence exhaustive des commandes, l'architecture interne et les scripts d'automatisation, rendez-vous sur le **[Guide & Documentation Technique Complète (DOCUMENTATION.md)](DOCUMENTATION.md)**.

---

## 🛑 Le Problème vs ⚡ La Solution `slim-video`

| 🛑 Vos vidéos aujourd'hui (H.264) | ⚡ Avec `slim-video` (HEVC Apple Silicon) |
| :--- | :--- |
| 🗄️ **Stockage saturé** : Les bibliothèques H.264 pèsent des centaines de Go sur vos disques. | 📉 **40% à 65% d'espace libéré** : Un film de 4.5 Go passe à ~1.9 Go sans perte visuelle perçue. |
| ⏳ **Encodages CPU interminables** : Plusieurs heures par film sur un transcodeur classique. | 🚀 **15x à 30x temps réel** : Un film complet de 2h encodé en ~4 minutes grâce au moteur VideoToolbox. |
| ❓ **Incertitude du gain** : Vous encodez à l'aveugle sans savoir si le fichier va rétrécir. | 🧪 **Échantillon réel de 20s** : Teste le fichier au centre pour calculer le gain exact avant traitement. |
| 🔄 **Ré-encodage inutile** : Temps perdu sur des vidéos déjà ultra-compressées. | ⏭️ **Auto-Skip intelligent (< 10%)** : Décoché automatiquement si l'économie est négligeable. |
| 🔇 **Altération audio** : Nombreux outils recompressent et dégradent les pistes son. | 🎵 **100% Bit-Exact Lossless** : Dolby Atmos, 7.1/5.1, DTS-HD et sous-titres copiés bit par bit. |
| 💥 **Disques durs externes qui saturent** : Les accès simultanés lecture/écriture détruisent les débits. | 🛡️ **SSD Staging (`--ssd-staging`)** : Encode sur SSD local ultra-rapide avant transfert continu. |

---

## ✨ Fonctionnalités Phares

```text
  ⚡ Ultra-Rapide (15-30x)   🧪 Échantillon 20s        ⏭️ Auto-Skip < 10%        🎵 Audio Bit-Exact
  Apple Silicon M1/M2/M3/M4   Prédiction mathématique    Élimine le travail inutile   Dolby Atmos & DTS-HD

  🌳 TUI Curses Pliable      🛡️ Mode SSD Staging       🔔 Notification macOS     🤖 Machine-Ready
  Sélection & raccourcis Vim   Préserve disques externes  Alerte en fin de lot        Flag --json & non-TTY
```

---

## 🚀 Démarrage Rapide en 30 Secondes

### 1. Prérequis
```bash
brew install ffmpeg
```

### 2. Installation globale isolée (avec `uv`)
```bash
uv tool install git+https://github.com/Boblebol/slim-video.git
```
*(ou `pip install git+https://github.com/Boblebol/slim-video.git`)*

### 3. Valider votre matériel
```bash
slim-video doctor
```

### 4. Lancer une conversion
```bash
# Menu interactif avec sélection de dossier :
slim-video

# Ou cibler directement un dossier de films :
slim-video "/Volumes/Media/Films"

# Recommandé pour disques durs externes :
slim-video "/Volumes/WD_BLACK/Media/Films" --ssd-staging --delete-original --yes
```

---

## 🖥 Aperçu de l'Interface

### 1. Simulation & Estimation sans modification (`estimate`)
Visualisez instantanément les économies potentielles avant de toucher au moindre fichier :

```bash
slim-video estimate /Volumes/Media/Films
```

```text
              📊 Potential Space Savings Estimation (Films)
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Video File                 ┃ Format    ┃  Original ┃ Est. HEVC ┃ Est. Gain ┃ Recommendation  ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ Action/Matrix.mp4          │ h264 1080p│   4.00 GB │   1.83 GB │    -54.2% │ ✅ Transcode    │
│ Action/Die_Hard.mkv        │ h264 1080p│   4.20 GB │   1.89 GB │    -55.1% │ ✅ Transcode    │
│ Autres/Film_Compresse.mp4  │ h264 1080p│   3.00 GB │   2.84 GB │     -5.2% │ ⏭ Skip (< 10%) │
└────────────────────────────┴───────────┴───────────┴───────────┴───────────┴─────────────────┘
```

### 2. Arbre Interactif Clavier (TUI)
Naviguez, pliez/dépliez les saisons et cochez les épisodes en toute fluidité :

```text
┌─ 🎬 slim-video ── H.264 Video Selection for x265 Transcoding ────────────────┐
│ 📁 Directory: /Volumes/Media/Films  (4 candidate files, 14.5 GB)             │
│──────────────────────────────────────────────────────────────────────────────│
│ [x] ▼ 📁 Action/  (2 files, 8.2 GB)                                          │
│       [x] 🎬 Matrix.mp4 [H264, 1080p] 4.0 GB → ~1.8 GB (-54.2% ✅)          │
│       [x] 🎬 Die_Hard.mkv [H264, 1080p] 4.2 GB → ~1.9 GB (-55.1% ✅)        │
│ [ ] ▼ 📁 Autres/  (2 files, 6.3 GB)                                          │
│       [ ] 🎬 Film_Compresse.mp4 [H264, 1080p] 3.0 GB → ~2.8 GB (-5.2% < min)│
│──────────────────────────────────────────────────────────────────────────────│
│ Selected: 2/4 files (8.2 GB → ~3.7 GB, Est. Gain: -54.7%)                    │
│ [↑/↓/j/k] Move  [Space] Toggle  [←/→/h/l] Fold/Unfold  [Enter] Start Transcode│
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Résultats Réels Observés

| Contenu | Format Source | Taille Initiale | Taille Finale HEVC | Gain Réel | Vitesse Encodage |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Film 1080p (2h15)** | H.264 AVC | 8.45 GB | **3.82 GB** | **-54.8%** | 22.4x (5m 40s) |
| **Série TV (10 épisodes)** | H.264 1080p | 32.10 GB | **13.60 GB** | **-57.6%** | 24.1x (18m 10s) |
| **Film Animation (1h30)** | H.264 1080p | 4.90 GB | **1.75 GB** | **-64.3%** | 28.5x (3m 10s) |
| **Documentaire 4K** | H.264 2160p | 18.20 GB | **9.10 GB** | **-50.0%** | 16.2x (12m 30s) |

---

## 📖 Commandes Essentielles

| Commande | Utilisation |
| :--- | :--- |
| `slim-video` | Lance le menu interactif d'accueil. |
| `slim-video transcode <PATH>` | Lance le scan, l'échantillonnage et le transcodage d'un dossier. |
| `slim-video estimate <PATH>` | Estime les économies sous forme de tableau sans modifier les fichiers. |
| `slim-video doctor` | Teste votre installation et lance un benchmark d'encodage live. |
| `slim-video config wizard` | Assistant interactif pas-à-pas pour configurer vos préférences. |
| `slim-video history stats` | Affiche l'historique et le total des gigaoctets économisés à vie. |

---

## 📚 En Savoir Plus

👉 **[Consulter la documentation complète & guide technique approfondi (DOCUMENTATION.md)](DOCUMENTATION.md)**

Vous y trouverez :
- L'explication détaillée de la fidélité 10-bit et de la quantification adaptative (`-spatial_aq 1`).
- La liste complète de tous les drapeaux CLI et options avancées.
- Le fonctionnement détaillé du mode `--ssd-staging` pour disques durs externes.
- Les exemples d'intégration dans des scripts d'automatisation avec `--json`.
- Le guide de dépannage et la FAQ.

---

## 👨‍💻 Auteur & Licence

Développé avec passion par **Alexandre Enouf**  
- 🌐 Site Web : [https://alexandre-enouf.fr](https://alexandre-enouf.fr)
- 🐙 GitHub : [@Boblebol](https://github.com/Boblebol)
- ✉️ Email : [alexandre.enouf@gmail.com](mailto:alexandre.enouf@gmail.com)

Distribué sous licence **MIT**. Voir [LICENSE](LICENSE) pour plus d'informations.
