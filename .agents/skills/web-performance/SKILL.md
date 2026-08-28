---
name: "boblebol:web:performance"
description: >-
  Optimizes web performance, eliminates critical request chains, removes third-party CDN latency via vendor self-hosting,
  enforces asynchronous Google fonts, converts images to WebP/AVIF, and eliminates Cumulative Layout Shift (CLS).
---

# ⚡ Web Performance & Core Web Vitals Skill

Eliminates network latency, blocking rendering paths, and visual layout shifts.

---

## 🚀 Optimization Checklist

- **Zero Critical CDN Chains**: Self-host vendor libs (React, ReactDOM, Vue, HTMX) in `assets/vendor/`.
- **Async Fonts**: Load Google/Custom fonts via `<link rel="preload" as="style" media="print" onload="this.media='all'">`.
- **Zero CLS on Images**: Explicit `width` and `height` attributes matching natural aspect ratio.
- **LCP Hero Image Optimization**: Add `fetchpriority="high"` and avoid `loading="lazy"` on above-the-fold assets.
