---
name: "boblebol:web:privacy-analytics"
description: >-
  Integrates analytics (Google Analytics GA4, Plausible, Umami, Cloudflare Web Analytics) securely via environment variables,
  adds resilient custom event tracking (trackEvent), and configures RGPD/CNIL compliance (Cookieless vs Cookie Banner).
---

# 📊 Web Privacy & Analytics Skill

Implements lightweight, privacy-respecting analytics with robust custom event tracking.

---

## 🔒 Best Practices

- **Build-Time Variable Injection**: Read `GA_MEASUREMENT_ID` at build time (clean fallback if absent).
- **Universal Event Tracker**:
  ```javascript
  function trackEvent(name, params) {
    try {
      if (typeof window.gtag === 'function') {
        window.gtag('event', name, params || {});
      }
    } catch (e) {}
  }
  ```
- **Track Essential Actions**: CV/file downloads, outbound socials, contact links, primary CTA clicks, language switches.
- **RGPD Strategy**: Choose between Cookieless mode (`analytics_storage: 'denied'`, `client_storage: 'none'`) without cookie pop-up vs Standard mode with accessible cookie banner.
