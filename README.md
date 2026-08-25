<div align="center">

<h1>
  🎬 slim-video
</h1>

<p>
  <b>Transcodeur par lot H.264 → x265 (HEVC) intelligent, accéléré matériellement pour Apple Silicon avec estimation sur échantillon réel de 20s et interface arborescente pliable.</b>
</p>

<p>
  <a href="https://github.com/Boblebol/slim-video/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/Boblebol/slim-video/ci.yml?branch=main&style=flat-square&logo=githubactions&logoColor=white&label=CI" alt="CI Status"></a>
  <a href="https://github.com/Boblebol/slim-video/releases"><img src="https://img.shields.io/badge/version-1.3.0-blue.svg?style=flat-square&logo=git&logoColor=white" alt="Version 1.3.0"></a>
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

</div>

---

## 📖 Sommaire

- [✨ Fonctionnalités Clés](#-fonctionnalités-clés)
- [🎬 Qualité, Fidélité Visuelle & Préservation](#-qualité-fidélité-visuelle--préservation)
- [🖥 Prérequis](#-prérequis)
- [🚀 Installation](#-installation)
- [🩺 Diagnostic Système (`slim-video doctor`)](#-diagnostic-système-slim-video-doctor)
- [🎬 Utilisation Rapide](#-utilisation-rapide)
- [📊 Mode Estimation Seule (`slim-video estimate`)](#-mode-estimation-seule-slim-video-estimate)
- [🌳 Contrôles de l'Arbre Interactif](#-contrôles-de-larbre-interactif)
- [⚙️ Configuration & Wizard (`slim-video config`)](#️-configuration--wizard-slim-video-config)
- [📈 Historique & Économies à Vie (`slim-video history`)](#-historique--économies-à-vie-slim-video-history)
- [📄 Rapport Texte Automatique](#-rapport-texte-automatique)
- [🔒 Sécurité, Quarantaine & Suppression](#-sécurité-quarantaine--suppression)
- [📦 Changelog & Versioning](#-changelog--versioning)
- [👨‍💻 Auteur & Licence](#-auteur--licence)

---

## ✨ Fonctionnalités Clés

- 🧭 **Interface CLI Ergonomique & Interactive** : Lancez simplement `slim-video` sans argument pour naviguer avec un menu interactif complet (dossier courant, sélection personnalisée, `~/Movies`, volumes externes, configuration, diagnostic).
- 🧪 **Test Échantillon Réel de 20s au Milieu** : Évalue le taux de compression exact sur un extrait de 20 secondes au centre de la vidéo pour extrapoler le gain réel sur l'ensemble du fichier.
- 🎯 **Seuil d'Éligibilité Automatique (< 10%)** : Si l'extrapolation montre un gain inférieur à 10%, le fichier est automatiquement décoché avec la mention `[< 10% ⏭ Ignoré]`. Vous ne perdez pas de temps à ré-encoder des fichiers qui ne réduisent pas significativement.
- 📊 **Mode Estimation Seule (`estimate`)** : Prévisualisez le gain potentiel sur toute une bibliothèque sous forme de tableau Rich coloré sans modifier aucun fichier.
- 🌳 **Navigation en Arbre Interactive (TUI)** : Pliez/dépliez les dossiers (`←`/`→`), cochez/décochez les fichiers (`Espace`), sélection globale (`a`), navigation fluide au clavier.
- ⚡ **Compression Matérielle Optimale x265** : Re-compression matérielle en HEVC 10-bit (`p010le` + `spatial_aq`) via Apple VideoToolbox préservant la qualité tout en réduisant la taille de 40% à 65%.
- 🎵 **Copie Lossless Audio & Sous-titres** : Toutes les pistes audio (Dolby Atmos, 5.1/7.1, AAC, DTS, etc.) et tous les sous-titres sont copiés à l'identique sans perte (`-c:a copy -c:s copy -map 0`).
- 🧙 **Assistant de Configuration Interactif (`wizard`)** : Ajustez tous vos paramètres pas-à-pas avec des questions interactives et des valeurs par défaut.
- 📈 **Suivi Cumulé des Économies (`history`)** : Visualisez l'espace disque total libéré au fil du temps sur votre Mac.
- 📄 **Rapport Texte Détaillé (`transcode_report.txt`)** : Généré automatiquement à la fin de chaque session.
- 🏥 **Diagnostic Système & Matériel (`slim-video doctor`)** : Valide en temps réel les dépendances, le support matériel Apple Silicon et lance un benchmark vidéo live (> 200 fps).
- 🔒 **Sécurité & Flexibilité** : Vos fichiers originaux sont soit déplacés en quarantaine dans `_originals_to_delete/` par défaut, soit supprimés directement avec `--delete-original`.

---

## 🎬 Qualité, Fidélité Visuelle & Préservation

Une question fréquente lors du passage de H.264 à H.265 (HEVC) : **Y a-t-il une dégradation de l'image, du son ou des pistes multilingues ?**

### 1. 🔊 Audio & Multilingue : Zéro perte (Copie Bit à Bit 100% Lossless)
* **Conservation intégrale de tous les flux (`-map 0`)** : Toutes les pistes audio (VF, VO, pistes 5.1/7.1 DTS-HD, Dolby Atmos, AC3, pistes de commentaires, audio descriptions...) sont capturées.
* **Aucun ré-encodage (`-c:a copy`)** : Le son n'est **jamais décompressé ni recompressé**. Le flux binaire audio original est copié bit pour bit sans aucune altération de dynamique ou de qualité acoustique.
* **Sous-titres & Chapitres (`-c:s copy`, `-map_chapters 0`, `-map_metadata 0`)** : Tous les sous-titres (SRT, ASS, PGS...) ainsi que le découpage en chapitres et métadonnées restent parfaitement intacts.

### 2. 📐 Résolution & Fréquence d'Images : Strictement Identiques
* **Aucun redimensionnement (*no downscaling*)** : Une source en **1080p** (1920×1080) reste en 1080p, une source **4K** (3840×2160) reste en 4K, une source **720p** reste en 720p.
* **Framerate préservé** : Le nombre d'images par seconde d'origine (23.976 fps, 24 fps, 25 fps, 60 fps...) est conservé à la microseconde près.

### 3. 🖼️ Qualité d'Image & Facteur de Qualité (`-q:v 50`)

Une question légitime : **Est-ce que le réglage par défaut `Quality 50` va dégrader mes vidéos ?**
👉 **Non.** Sur l'encodeur matériel **Apple VideoToolbox**, la valeur `50` est le **"sweetspot" officiel recommandé par Apple** pour obtenir une qualité **visuellement sans perte** (*visually lossless*, indiscernable de la source à l'œil nu sur écran 4K/OLED).

#### 🎛️ Échelle de qualité VideoToolbox (1 à 100) :
Contrairement au CRF logiciel (où 0 est sans perte et 51 très moche), l'échelle matérielle VideoToolbox fonctionne de **1 (qualité maximale / débit le plus élevé)** à **100 (compression maximale)** :

| Valeur `-q:v` | Profil d'usage | Rendu visuel & Réduction d'espace |
|---|---|---|
| **`35 - 45`** | **Qualité Ultra-Haute / Archivage** | Débit vidéo très généreux pour puristes 4K HDR. Réduction de taille plus modérée (~25% à 35%). |
| **`50`** *(Défaut)* | **Sweetspot Optimal (Visually Lossless)** | **Transparence visuelle totale à l'œil nu.** Réduction de taille optimale de **~40% à 60%**. |
| **`60 - 70`** | **Compression Forte** | Gain d'espace maximal pour petits écrans ou vidéos d'appoint (~65% à 80%). |

#### 💎 Pourquoi l'image reste-t-elle aussi nette à 50 ?
* **H.264 (2003) vs H.265/HEVC (2013)** : Le H.264 découpait l'image en blocs rigides de 16×16 pixels. Le H.265 utilise des arbres de codage dynamiques (CTU) de 4×4 à 64×64 pixels et 35 directions de prédiction intra-image. Pour restituer **la même finesse de détails**, le H.265 a besoin de 40% à 60% de débit en moins. Le gain vient de l'intelligence mathématique, pas d'une coupe destructive.
* **Encodage 10-bit (`p010le`)** : Même si la source est en 8-bit, `slim-video` encode en 10-bit (1,07 milliard de nuances de couleurs). Cela élimine les effets de bandes et d'artefacts (*banding*) dans les dégradés sombres, le ciel et les fumées.
* **Spatial Adaptive Quantization (`-spatial_aq 1`)** : Le silicium Apple analyse l'image en continu : il préserve le piqué, les textures fines et le grain de pellicule, et compresse plus fort uniquement les fonds neutres et zones planes.

#### ⚙️ Ajuster la qualité selon vos préférences :
```bash
# Tester une qualité supérieure (ex: 45 ou 40) pour un dossier spécifique :
slim-video /Volumes/UGREEN/Films -q 45

# Ou définir définitivement une nouvelle qualité par défaut dans votre configuration :
slim-video config set quality 45
```

### 4. 🛡️ Garde-Fous Intelligents
* **Échantillon réel de 20s** : Mesure sur le film réel le gain avant tout calcul.
* **Seuil d'exclusion automatique (< 10%)** : Si un film est déjà ultra-compressé et qu'un ré-encodage n'économiserait presque rien, il est automatiquement décoché.

---

## 🖥 Prérequis

- **macOS** (optimisé pour processeurs Apple Silicon M1 / M2 / M3 / M4)
- **Python** ≥ 3.9 (ou [uv](https://github.com/astral-sh/uv))
- **ffmpeg** avec support VideoToolbox

```bash
brew install ffmpeg
```

---

## 🚀 Installation

### Avec `uv` *(recommandé)*

```bash
# Installation globale en CLI isolée :
uv tool install git+https://github.com/Boblebol/slim-video.git

# Ou dans un environnement de développement local :
git clone https://github.com/Boblebol/slim-video.git
cd slim-video
uv sync --all-extras --dev
```

### Avec `pip`

```bash
git clone https://github.com/Boblebol/slim-video.git
cd slim-video
pip install -e ".[dev]"
```

---

## 🩺 Diagnostic Système (`slim-video doctor`)

Avant de commencer, vérifiez que votre machine et l'accélération matérielle Apple Silicon sont prêtes :

```bash
slim-video doctor
```

```text
╭──────────────────────────────────────────────────────────────────────────────╮
│ slim-video Doctor ── System & Hardware Diagnostics                           │
╰──────────────────────────────────────────────────────────────────────────────╯
                             🏥 Diagnostic Results                              
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  Status  ┃ Component                         ┃ Details                       ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ ✅ PASS  │ Python Version                    │ Python 3.13.1 (CPython)       │
│ ✅ PASS  │ Operating System & Architecture   │ Darwin (arm64) [Apple Silicon]│
│ ✅ PASS  │ FFmpeg Binary                     │ Found at /opt/homebrew/bin    │
│ ✅ PASS  │ FFprobe Binary                    │ Found at /opt/homebrew/bin    │
│ ✅ PASS  │ VideoToolbox Hardware Encoder     │ hevc_videotoolbox available   │
│ ✅ PASS  │ Temporary SSD Storage (/tmp)      │ Write & read access OK        │
│ ✅ PASS  │ Terminal & Curses Support         │ Curses loaded (fr_FR.UTF-8)   │
│ ✅ PASS  │ Live Hardware Transcode Benchmark │ VideoToolbox test passed!     │
└──────────┴───────────────────────────────────┴───────────────────────────────┘
```

---

## 🎬 Utilisation Rapide

```bash
# 1. Menu interactif d'accueil (choix du dossier, disques externes, etc.) :
slim-video

# 2. Spécifier directement un dossier cible :
slim-video /Volumes/UGREEN/Films

# 3. Spécifier un seuil de gain personnalisé (ex: 15%) et qualité (ex: 45) :
slim-video /Volumes/UGREEN/Films --min-gain 15 --quality 45

# 4. Mode non-interactif / batch (automatisation) :
slim-video /Volumes/UGREEN/Films --yes

# 5. Mode suppression directe de l'ancien fichier après transcodage :
slim-video /Volumes/UGREEN/Films --delete-original
```

---

## 📊 Mode Estimation Seule (`slim-video estimate`)

Pour savoir combien de Go vous allez économiser sans toucher aux fichiers :

```bash
slim-video estimate /Volumes/UGREEN/Films
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

---

## 🌳 Contrôles de l'Arbre Interactif

```text
┌─ 🎬 slim-video ── H.264 Video Selection for x265 Transcoding ────────────────┐
│ 📁 Directory: /Volumes/UGREEN/Films  (4 candidate files, 14.5 GB)            │
│──────────────────────────────────────────────────────────────────────────────│
│ [x] ▼ 📁 Action/  (2 files, 8.2 GB)                                          │
│       [x] 🎬 Matrix.mp4 [H264, 1080p] 4.0 GB → ~1.8 GB (-54.2% ✅)          │
│       [x] 🎬 Die_Hard.mkv [H264, 1080p] 4.2 GB → ~1.9 GB (-55.1% ✅)        │
│ [ ] ▼ 📁 Autres/  (2 files, 6.3 GB)                                          │
│       [ ] 🎬 Film_Compresse.mp4 [H264, 1080p] 3.0 GB → ~2.8 GB (-5.2% < min)│
│──────────────────────────────────────────────────────────────────────────────│
│ Selected: 2/4 files (8.2 GB → ~3.7 GB, Est. Gain: -54.7%)                    │
│ [↑/↓] Déplacer  [Espace] Cocher/Décocher  [←/→] Plier/Déplier  [Entrée] Lancer│
└──────────────────────────────────────────────────────────────────────────────┘
```

| Touche | Action |
|---|---|
| `↑` / `↓` ou `k` / `j` | Se déplacer dans l'arborescence |
| `Espace` | Cocher / décocher le fichier ou le dossier sélectionné |
| `←` / `→` ou `h` / `l` | Plier / déplier le dossier |
| `e` / `c` | Tout déplier (`e`) / Tout replier (`c`) |
| `a` | Tout sélectionner / Tout désélectionner |
| `Entrée` | Valider la sélection et démarrer le transcodage |
| `q` / `Echap` | Quitter / Annuler |

---

## ⚙️ Configuration & Wizard (`slim-video config`)

Un fichier de configuration explicite est sauvegardé dans `~/.slim_video_config.json` :

```bash
# Lancer l'assistant interactif de configuration :
slim-video config wizard

# Afficher les paramètres actuels sous forme de tableau :
slim-video config show

# Modifier une option précise :
slim-video config set min_gain_percent 15
slim-video config set sample_duration_seconds 20
slim-video config set quality 50

# Réinitialiser tous les réglages par défaut :
slim-video config reset
```

---

## 📈 Historique & Économies à Vie (`slim-video history`)

Suivez l'espace disque cumulé économisé sur votre machine :

```bash
# Afficher le bilan global des économies :
slim-video history stats

# Voir les 10 dernières conversions :
slim-video history

# Effacer l'historique :
slim-video history clear
```

---

## 📄 Rapport Texte Automatique

À la fin de chaque session, un rapport complet `transcode_report.txt` est enregistré dans le dossier source :

```text
================================================================================
                  HEVC / x265 TRANSCODING SUMMARY REPORT
================================================================================
Date & Time:        2026-08-24 15:45:00
Target Directory:   /Volumes/UGREEN/Films
Video Encoder:      Apple VideoToolbox (hevc_videotoolbox - 10-bit)
Total Batch Time:   08m 12s

================================================================================
                               GLOBAL STORAGE GAIN
================================================================================
Files Selected:     2 / 4 candidate(s)
Transcoded OK:      2 file(s)

Original Total Size:   8.20 GB (8,804,682,752 bytes)
New HEVC Total Size:   3.70 GB (3,972,844,748 bytes)
Storage Freed:         4.50 GB (4,831,838,004 bytes)
Overall Reduction:    -54.9%

================================================================================
                             DETAILED FILE BREAKDOWN
================================================================================
[1/2] Action/Matrix.mp4
  • Status         : SUCCESS
  • Video Spec     : H264 -> HEVC 10-bit (1920x1080 @ 23.98 fps)
  • Audio / Subs   : AAC 6ch (Stream Copied - Lossless)
  • Original Size  : 4.00 GB (4,294,967,296 bytes)
  • New HEVC Size  : 1.85 GB (1,986,422,374 bytes)
  • Space Saved    : 2.15 GB (-53.8%)
  • Encode Time    : 02m 05s (Speed: 14.8x)
  • Output Video   : Action/Matrix.hevc.mkv
  • Original Moved : _originals_to_delete/Action/Matrix.mp4
--------------------------------------------------------------------------------
...
```

---

## 🔒 Sécurité, Quarantaine & Suppression

* **Comportement par défaut (Sécurité maximale)** : Les originaux H.264 ne sont **jamais** supprimés immédiatement. Ils sont déplacés proprement dans le sous-dossier `_originals_to_delete/` en conservant l'arborescence. Vous pouvez vérifier la qualité de vos `.hevc.mkv` et supprimer le dossier de quarantaine quand vous le souhaitez.
* **Mode suppression directe (`--delete-original` / `-d`)** : Si vous manquez d'espace disque ou souhaitez un traitement 100% autonome sans étape de quarantaine intermédiaire, passez l'option `--delete-original` (ou `--delete`). Le fichier source original est supprimé automatiquement et immédiatement dès que le transcodage HEVC a réussi avec succès. Vous pouvez également définir ce comportement par défaut via `slim-video config set delete_original true`.

---

## 📦 Changelog & Versioning

L'historique complet des versions et modifications est disponible dans le fichier [CHANGELOG.md](CHANGELOG.md).

---

## 👨‍💻 Auteur & Licence

**Alexandre Enouf**
- 🌐 Site Web : [https://alexandre-enouf.fr](https://alexandre-enouf.fr)
- 🐙 GitHub : [@Boblebol](https://github.com/Boblebol)
- ✉️ Email : [alexandre.enouf@gmail.com](mailto:alexandre.enouf@gmail.com)

Distribué sous licence **MIT**. Voir [LICENSE](LICENSE) pour plus d'informations.
