---
name: "boblebol:story:blog-post-architect"
description: >-
  Explores any codebase, feature, repository, or README to craft engaging, Medium-style technical blog articles with photos,
  diagrams, and authentic developer storytelling. Conducts a deep code inspection followed by a sharp, no-bullshit interview
  (Sam & Max style, vibe coding realities, actual struggles, tech flex, AI role) before drafting bilingual articles (FR & EN)
  and generating complete blog post packages. Use whenever Alexandre wants to write, draft, or tell the story of a GitHub project.
---

# ✍️ Blog Post Architect — Vibe Code & No-Bullshit Edition

Transforms code, project architectures, and engineering achievements into **punchy, authentic, Medium-style developer stories** (French & English) that sound like a dev sharing a beer with a peer, not a corporate press release.

---

## 🎨 Editorial DNA (Ton visé : "Sam & Max / Dev-to-Dev Cash & Direct")

- **Ton visé** : Direct, familier, premier degré, avis tranchés, autodérision, zéro langue de bois marketing ni jargon LinkedIn.
- **Règle d'or** : Pas de *"Dans cet article, nous allons explorer ensemble..."*. On écrit comme on parle à un autre dev, avec des punchlines, de vraies anecdotes de galère et pas peur de dire *"ce bout de code est moche mais il tourne"*.

---

## ⚙️ Workflow en 3 Étapes

```mermaid
graph TD
    A[Étape 1: Fouille approfondie du repo & Détection des galères] --> B[Étape 2: Interview ciblée par petits paquets]
    B --> C[Étape 3: Rédaction bilingue FR & EN + Packaging meta.yaml]
```

---

## Étape 1 — Lire le repo avant de poser une seule question

Avant de lancer l'interview, l'agent doit aller chercher la matière lui-même pour ne pas poser de questions dont la réponse est déjà dans le code :

1. **README, CHANGELOG, commits récents** : les messages de commits sont souvent plus honnêtes que la doc (*"fix ça marche pas"*, *"wtf"*, *"last try"*).
2. **Structure & complexité** : stack, dépendances bizarres, volume de code.
3. **Indices de vibe coding** : gros commits massifs suivis de micro-fixes, fichiers générés d'un coup, incohérences de style, commentaires laissés par l'IA.
4. **Noter 3 à 5 éléments concrets et croustillants** : un fichier bizarre, une fonction alambiquée, un choix technique qui saute aux yeux pour alimenter l'interview avec des éléments réels du repo.

---

## Étape 2 — L'interview (par petits paquets adaptés)

Poser ces questions dans l'ordre, **une poignée à la fois (pas toutes d'un coup)**, en adaptant avec les éléments concrets trouvés à l'étape 1 :

### 1. Le déclic (version honnête, pas la version LinkedIn)
- C'est quoi le truc chiant/nul qui t'a fait dire *"bon ok je le fais moi-même"* ?
- T'as regardé si ça existait déjà ? C'était naze, trop compliqué, ou t'avais juste envie de coder un truc ?

### 2. Le process vibe code, sans filtre
- Sur ce projet, t'as fait quoi toi, et t'as laissé l'IA faire quoi ?
- Y'a un moment où le code généré avait l'air bon mais était en fait cassé/faux ? Qu'est-ce qui t'a mis la puce à l'oreille ?
- *[Référencer un fichier/commit précis trouvé à l'étape 1]* : ça, c'est toi ou c'est l'IA qui a pondu ça direct ?
- Combien de temps t'as passé à corriger/comprendre du code que t'avais pas écrit toi-même ?

### 3. La douleur technique réelle
- Quel est le truc qui t'a fait perdre 3h pour un problème qui aurait dû prendre 10 min ?
- Y'a un moment où t'as voulu tout foutre en l'air et recommencer ?
- Qu'est-ce que tu ferais différemment si tu recommençais demain ?

### 4. Les trucs pas fiers
- Y'a un bout de code que tu sais dégueulasse mais t'as pas eu le courage/le temps de refaire proprement ?
- Qu'est-ce qu'un dev senior te dirait de refaire s'il lisait ce repo ?

### 5. Le truc dont t'es vraiment fier
- Si tu devais montrer une seule ligne ou fonction à un pote dev en disant *"regarde ça c'est malin"*, ce serait laquelle ?
- Qu'est-ce que t'as fait que personne remarquera jamais mais qui t'a demandé un effort disproportionné ?

### 6. Le coup de gueule
- Y'a un outil, une lib, une "best practice" que tout le monde recommande et que tu détestes après ce projet ?

### 7. L'angle et la cible
- Si quelqu'un lit ça en diagonale sur son tel dans le métro, c'est quoi la seule phrase qu'il doit retenir ?
- C'est un article *"viens voir ce que j'ai fait"*, *"voilà comment j'ai vibe codé un truc utilisable"*, ou *"voilà comment éviter mes erreurs"* ?

---

## Étape 3 — Rédaction & Packaging

1. **Structure de l'article** :
   - Ouvrir sur le problème / le déclic concret.
   - Assumer le vibe coding sans complexe : dire clairement ce qui a été fait avec l'IA, ce qui a foiré, ce qui a été repris à la main.
   - Citer un ou deux extraits de code réels (le moche ou le malin trouvé à l'étape 1).
   - Titres de section courts et percutants (*"Pourquoi j'ai voulu tout casser au bout de 2h"* plutôt que *"Défis rencontrés"*).
   - Finir sur un avis tranché ou une leçon concrète.
   - Toujours se relire avec le filtre : *"Est-ce que ça sonne comme un dev qui raconte un truc à un pote, ou comme un communiqué de presse ?"*

2. **Packaging Portfolio & Multi-langues** :
   - Générer `content/fr.md` et `content/en.md`.
   - Créer `meta.yaml` complet (id, title, subtitle, summary, published_date, tags).
   - Optimiser les images associées en WebP avec légendes captivantes.
