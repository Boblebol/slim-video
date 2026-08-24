<div align="center">

<h1>
  🎬 hevc-cli
</h1>

<p>
  <b>Transcodeur par lot H.264 → x265 (HEVC) intelligent, accéléré matériellement pour Apple Silicon avec estimation sur échantillon réel de 20s et interface arborescente pliable.</b>
</p>

<p>
  <a href="https://github.com/Boblebol/slim-video/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/Boblebol/slim-video/ci.yml?branch=main&style=flat-square&logo=githubactions&logoColor=white&label=CI" alt="CI Status"></a>
  <a href="https://github.com/Boblebol/slim-video/releases"><img src="https://img.shields.io/badge/version-1.1.0-blue.svg?style=flat-square&logo=git&logoColor=white" alt="Version 1.1.0"></a>
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
- [🖥 Prérequis](#-prérequis)
- [🚀 Installation](#-installation)
- [🩺 Diagnostic Système (`hevc-cli doctor`)](#-diagnostic-système-hevc-cli-doctor)
- [🎬 Utilisation Rapide](#-utilisation-rapide)
- [🌳 Contrôles de l'Arbre Interactif](#-contrôles-de-larbre-interactif)
- [⚙️ Configuration (`hevc-cli config`)](#️-configuration-hevc-cli-config)
- [📄 Rapport Texte Automatique](#-rapport-texte-automatique)
- [🔒 Sécurité & Quarantaine](#-sécurité--quarantaine)
- [📦 Changelog & Versioning](#-changelog--versioning)
- [👨‍💻 Auteur & Licence](#-auteur--licence)

---

## ✨ Fonctionnalités Clés

- 🧪 **Test Échantillon Réel de 20s au Milieu** : Évalue le taux de compression exact sur un extrait de 20 secondes au centre de la vidéo pour extrapoler le gain réel sur l'ensemble du fichier.
- 🎯 **Seuil d'Éligibilité Automatique (< 10%)** : Si l'extrapolation montre un gain inférieur à 10%, le fichier est automatiquement décoché avec la mention `[< 10% ⏭ Ignoré]`. Vous ne perdez pas de temps à ré-encoder des fichiers qui ne réduisent pas significativement.
- 🌳 **Navigation en Arbre Interactive (TUI)** : Pliez/dépliez les dossiers (`←`/`→`), cochez/décochez les fichiers (`Espace`), sélection globale (`a`), navigation rapide au clavier.
- ⚡ **Compression Automatique Optimale x265** : Re-compression matérielle en HEVC 10-bit (`p010le` + `spatial_aq`) préservant la qualité de l'original tout en réduisant la taille de 40% à 65%.
- 🎵 **Copie Lossless Audio & Sous-titres** : Toutes les pistes audio (Dolby Atmos, 5.1/7.1, AAC, DTS, etc.) et tous les sous-titres sont copiés à l'identique sans perte (`-c:a copy -c:s copy -map 0`).
- 📄 **Rapport Texte Détaillé (`transcode_report.txt`)** : Généré automatiquement à la fin de l'encodage avec le bilan complet (avant, après, gain en Go et en %, durée, vitesse d'encodage).
- 🏥 **Diagnostic Système & Matériel (`hevc-cli doctor`)** : Valide en temps réel les dépendances, le support matériel Apple Silicon et lance un benchmark vidéo live (> 200 fps).
- 📐 **Architecture Robuste & Typage Strict** : Modèles de données et DTOs propulsés par **Pydantic v2**, typage statique strict vérifié par **Mypy**, formatage **Ruff**.
- ⚙️ **Fichier de Réglages Explicite (`~/.hevc_cli_config.json`)** : Personnalisable facilement via la commande `hevc-cli config`.
- 🔒 **Sécurité Maximale** : Vos fichiers originaux ne sont jamais supprimés immédiatement mais déplacés en quarantaine dans `_originals_to_delete/`.

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
uv pip install -e ".[dev]"
```

### Avec `pip`

```bash
git clone https://github.com/Boblebol/slim-video.git
cd slim-video
pip install -e ".[dev]"
```

---

## 🩺 Diagnostic Système (`hevc-cli doctor`)

Avant de commencer, vérifiez que votre machine et l'accélération matérielle Apple Silicon sont prêtes :

```bash
hevc-cli doctor
```

```text
╭──────────────────────────────────────────────────────────────────────────────╮
│ hevc-cli Doctor ── System & Hardware Diagnostics                             │
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
# Lancer dans le dossier courant :
hevc-cli

# Ou spécifier un dossier cible :
hevc-cli /Volumes/UGREEN/Films
```

---

## 🌳 Contrôles de l'Arbre Interactif

```text
┌─ 🎬 hevc-cli ── H.264 Video Selection for x265 Transcoding ──────────────────┐
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

## ⚙️ Configuration (`hevc-cli config`)

Un fichier de configuration Pydantic explicite est sauvegardé dans `~/.hevc_cli_config.json` :

```bash
# Afficher les paramètres actuels
hevc-cli config show

# Modifier le seuil de gain minimum (ex: 15%)
hevc-cli config set min_gain_percent 15

# Modifier la durée de l'échantillon de test (ex: 20 secondes)
hevc-cli config set sample_duration_seconds 20

# Modifier la qualité VideoToolbox (1=meilleure qualité, 100=plus compressé)
hevc-cli config set quality 50

# Réinitialiser tous les réglages par défaut
hevc-cli config reset
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

## 🔒 Sécurité & Quarantaine

1. **Aucune suppression automatique directe.** Les originaux H.264 sont déplacés dans le sous-dossier `_originals_to_delete/` en conservant l'arborescence.
2. **Vérifiez la lecture** de vos nouveaux fichiers `.hevc.mkv`.
3. Supprimez `_originals_to_delete/` quand vous le souhaitez pour libérer physiquement l'espace disque.

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
