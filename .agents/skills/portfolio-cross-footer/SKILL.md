---
name: "boblebol:story:portfolio-cross-footer"
description: >-
  Standardizes and injects Alexandre Enouf's cross-site portfolio footer across all web apps, side projects, and micro-tools.
  Enforces consistent identity links (Portfolio, GitHub, LinkedIn, Email, Paris, France) with sleek, responsive, and accessible styling
  to build an interconnected web of personal projects.
---

# 🌐 Portfolio Cross-Footer & Identity Linker Skill

Injects a unified, elegant, and responsive footer into any standalone project, web app, or landing page to connect it seamlessly with Alexandre Enouf's main portfolio.

---

## 🎨 Unified Footer Blueprint

The footer must display Alexandre's identity, role, location, and key outgoing links:

```html
<footer class="ae-cross-footer">
  <div class="ae-footer-inner">
    <div class="ae-footer-identity">
      <a href="https://alexandre-enouf.fr/" class="ae-footer-logo" target="_blank" rel="noopener">
        Alexandre <em>Enouf</em>
      </a>
      <span class="ae-footer-tagline">· Développeur produit & Builder IA · Paris, France</span>
    </div>
    <div class="ae-footer-links">
      <a href="https://alexandre-enouf.fr/#lab" target="_blank" rel="noopener">⚡ Lab & Projets</a>
      <a href="https://alexandre-enouf.fr/blog/" target="_blank" rel="noopener">📖 Blog</a>
      <a href="https://github.com/Boblebol" target="_blank" rel="noopener">GitHub</a>
      <a href="https://www.linkedin.com/in/alexandreenouf-47834990" target="_blank" rel="noopener">LinkedIn</a>
      <a href="mailto:alexandre.enouf@gmail.com">Contact</a>
    </div>
  </div>
</footer>
```

### 💅 Embedded CSS Styling
```css
.ae-cross-footer {
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  background: rgba(247, 246, 243, 0.6);
  padding: 24px 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: 13px;
  color: #6e6b66;
  width: 100%;
}
.ae-footer-inner {
  max-width: 1080px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 14px;
}
.ae-footer-identity {
  display: flex;
  align-items: center;
  gap: 8px;
}
.ae-footer-logo {
  font-weight: 600;
  color: #18171a;
  text-decoration: none;
  font-size: 14px;
}
.ae-footer-logo em {
  font-style: italic;
  color: oklch(0.38 0.16 265);
}
.ae-footer-links {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}
.ae-footer-links a {
  color: #6e6b66;
  text-decoration: none;
  transition: color 0.15s;
}
.ae-footer-links a:hover {
  color: #18171a;
}
@media (max-width: 600px) {
  .ae-footer-inner {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
}
```
