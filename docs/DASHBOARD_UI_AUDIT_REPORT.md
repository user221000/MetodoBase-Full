# Dashboard UI/UX Audit & Refactor Report

**Date:** 2026-03-29  
**Scope:** Web dashboard (`/dashboard`) — styling & code quality only  
**Files modified:** `web/static/css/styles.css`, `web/templates/dashboard.html`, `web/templates/base.html`  
**Business logic changes:** None

---

## 1. Audit Findings

### 1.1 Dead Code Removed

| Item | Type | Location |
|------|------|----------|
| `.logo-dot` | CSS selector | styles.css — orphan from old logo |
| `.hero-text h2`, `.hero-text p` | CSS selectors | styles.css — removed hero variant |
| `.kpi-card.kpi-hero` | CSS selector | styles.css — unused KPI variant |
| `.kpi-icon` | CSS selector | styles.css — icon wrapper never used |
| Duplicate `.kpi-success` | Duplicate CSS | styles.css — 2nd definition |
| Duplicate `.kpi-info` | Duplicate CSS | styles.css — 2nd definition |
| Duplicate `.kpi-warning:hover` | Duplicate CSS | styles.css — 2nd hover |
| Duplicate `.btn-ghost` | Duplicate CSS | styles.css — 2nd definition |
| Orphan `.subscription-badge` | CSS selector | styles.css — component removed |
| `.top-bar-left h1/p` | CSS selectors | styles.css — old top bar layout |
| `.donut-center-value`, `.donut-center-label` | CSS selectors | styles.css — unused chart component |
| `.gap-6`, `.opacity-50`, `.py-2`, `.py-3`, `.p-4`, `.rounded-lg`, `.rounded-xl`, `.text-lg`, `.space-y-6` | Utility classes | styles.css — never referenced in templates |

**Dead files (recommend deletion):**
- `web/templates/_index_legacy_REMOVED.html` — 487-line legacy template, not loaded
- `web/static/js/DIAGNOSTICO_DASHBOARD.js` — 44-line diagnostic comments, not loaded

### 1.2 Hardcoded Values Eliminated

| Before | After | Count |
|--------|-------|-------|
| `font-size: 2rem` | `var(--text-h1)` | 2 |
| `font-size: 1.5rem` | `var(--text-h2)` | 2 |
| `font-size: 1.15rem` | `var(--text-h3)` | 1 |
| `font-size: 0.95rem` | `var(--text-body)` | 3 |
| `font-size: 0.78rem` | `var(--text-label)` | 4 |
| `font-weight: 800` | `var(--font-weight-heavy)` | 3 |
| `font-weight: 700` | `var(--font-weight-bold)` | 2 |
| `font-weight: 600` | `var(--font-weight-semibold)` | 2 |
| `--space-5: 20px` (broken scale) | `--space-5: 24px` | 1 |
| `--space-10: 40px` (broken scale) | `--space-10: 48px` | 1 |
| Alias tokens with raw hex | Alias tokens with `var()` refs | 5+ |

### 1.3 Inline Styles Extracted

**dashboard.html** — reduced from **13 inline `style=`** to **1** (JS-controlled `display:none` on badge):

| Element | Inline style removed | CSS class created |
|---------|---------------------|-------------------|
| CTA button | `padding:14px 32px;border-radius:10px;...` | `.btn-cta-hero` |
| Skeleton divs (×3) | `width:70%`, `width:60%`, `width:55%` | `.skeleton-w-70`, `.skeleton-w-60`, `.skeleton-w-55` |
| Modal container | `width:min(620px,95vw);padding:32px;...` | `.modal-form-container` |
| Modal header | `display:flex;align-items:center;gap:12px;...` | `.modal-form-header` |
| Modal icon | `width:42px;height:42px;border-radius:10px;...` | `.modal-form-icon` |
| Modal title | `margin:0;font-size:1.15rem` | `.modal-form-title` |
| Modal subtitle | `margin:2px 0 0;font-size:0.8rem;...` | `.modal-form-subtitle` |
| Form sections (×3) | `font-size:.78rem;font-weight:600;text-transform:uppercase;...` | `.form-section-label` |
| Section icon | `width:18px;height:18px` | `.form-section-icon` |
| Food panel | `max-width:520px` | `.modal-sm` |
| Food tags | `display:flex;flex-wrap:wrap;gap:6px;...` | `.food-tags-container` |
| Calendar GIF icons (×2) | `width:22px;height:22px;vertical-align:middle;...` | `.icon-gif` |
| Textarea | `resize:vertical` | `.resize-y` |
| Input group | `margin-top:12px` | `.mt-3` |
| Chevron SVG | `margin-left:auto;flex-shrink:0;opacity:.5` | `.chevron-icon` |
| Food tags (main form) | `display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;...` | `.food-tags-container .mt-2` |
| Submit wrapper | `margin-top:8px;gap:8px;font-weight:600` | `.mt-2` + class attrs |
| JS: food cat count | `opacity:.5;font-weight:400` | `.food-cat-count` |
| JS: empty state | `padding:24px;color:...;font-size:...;text-align:center` | `.food-empty-state` |
| JS: empty state img | `width:48px;height:48px;opacity:.4;margin-bottom:8px` | `.food-empty-img` |

**base.html** — reduced from **8 inline `style=`** to **0**:

| Element | Replacement class |
|---------|------------------|
| Sidebar logo link | `.sidebar-logo-link` |
| Logo icon container | `.sidebar-logo-icon` |
| Logo subtitle | `.logo-subtitle` |
| Sidebar footer (7 styles) | `.sidebar-footer-inner`, `.sidebar-user-row`, `.sidebar-user-info`, `.sidebar-user-name`, `.sidebar-user-role`, `.btn-logout-icon` |
| Nav section "Gestión" | `.mt-4` |

### 1.4 Redundancy Fixed

- `detail-zone` had `style="display:none"` in dashboard.html AND `.detail-zone { display:none !important; }` in base.html `<style>` block. Removed the inline style; the CSP-nonced `<style>` block in base.html is authoritative.

---

## 2. Design System Definition

### 2.1 Color Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--accent-primary` | `#FBBF24` | Primary CTA, Warm Amber |
| `--accent-primary-glow` | `rgba(251,191,36,0.10)` | Hover/glow states |
| `--accent-purple` / `--accent-secondary` | `#2DD4BF` | Teal accent (badges, section labels) |
| `--accent-green` | `#34D399` | Success state |
| `--accent-red` | `#F87171` | Error/danger |
| `--accent-orange` | `#FB923C` | Warning |
| `--bg-primary` | `#0C0B09` | Page background (charcoal) |
| `--bg-card` | `#1A1A1E` | Card/surface |
| `--bg-surface` | `#1c1d21` | Elevated surface |
| `--text-primary` | `#F9F6F0` | Headings |
| `--text-secondary` | `#8B8B9E` | Body text |
| `--text-muted` | `#5A5A6E` | Captions |

### 2.2 Spacing Scale (strict 4px base)

| Token | Value |
|-------|-------|
| `--space-1` | `4px` |
| `--space-2` | `8px` |
| `--space-3` | `12px` |
| `--space-4` | `16px` |
| `--space-5` | `24px` *(fixed from 20px)* |
| `--space-6` | `24px` |
| `--space-8` | `32px` |
| `--space-10` | `48px` *(fixed from 40px)* |

### 2.3 Typography Scale

| Token | Value | Usage |
|-------|-------|-------|
| `--text-h1` | `2rem` | Page titles |
| `--text-h2` | `1.5rem` | Section headings |
| `--text-h3` | `1.15rem` | Card titles |
| `--text-body` | `0.95rem` | Body copy |
| `--text-label` | `0.78rem` | Labels, captions |
| `--text-caption` | `0.72rem` | Small labels, badges |
| `--font-weight-normal` | `400` | Body text |
| `--font-weight-medium` | `500` | Labels |
| `--font-weight-semibold` | `600` | Section labels |
| `--font-weight-bold` | `700` | Headings |
| `--font-weight-heavy` | `800` | Hero numbers |

### 2.4 Border Radius

| Token | Value |
|-------|-------|
| `--radius-xs` | `6px` |
| `--radius-sm` | `10px` |
| `--radius-md` | `14px` |
| `--radius-lg` | `18px` |
| `--radius-full` | `9999px` |

---

## 3. Microinteractions Spec

### 3.1 Buttons

```css
.btn {
  transition: all 180ms ease-out;
}
.btn-primary:hover {
  transform: scale(1.03);
  box-shadow: 0 4px 20px rgba(251, 191, 36, 0.18);
}
.btn-primary:active {
  transform: scale(0.97);
}
```

### 3.2 Table Rows

```css
.table tbody tr {
  transition: background 120ms linear;
}
.table tbody tr:hover {
  background: rgba(251, 191, 36, 0.04);
}
```

### 3.3 Cards

```css
.action-hero:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(251, 191, 36, 0.10);
}
/* transition: 200ms ease inherited from base .action-hero */
```

### 3.4 KPI Cards

```css
.kpi-card {
  transition: all 200ms ease;
}
.kpi-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(139, 139, 158, 0.08);
}
```

---

## 4. Visual Hierarchy (Business-Goal Aligned)

### PRIMARY — Revenue-Driving Actions
- **"Generar Plan Nutricional" CTA** — largest card, warm amber gradient background, prominent `Comenzar ahora` button with `scale(1.03)` hover. This is the #1 conversion action.
- **"Clientes sin actividad" KPI** — red border accent, "Atención" badge. Drives re-engagement and churn reduction.

### SECONDARY — Risk Indicators
- **KPI cards** — 3-card row showing inactive clients, active clients, plans generated. Color-coded badges (Atención = red, Activo = green, Productividad = yellow).
- **"Actividad reciente" feed** — shows latest client events to surface engagement patterns.

### TERTIARY — Supporting Information
- **"Clientes recientes" table** — recent client list with objective badges and quick-link to plan generation.
- **Sidebar navigation** — minimal, with client count badge for quick context.
- **User identity** in sidebar footer — gym name, plan status, logout.

---

## 5. Files for Manual Deletion

These files are dead code — not referenced by any template, route, or script:

1. `web/templates/_index_legacy_REMOVED.html` (487 lines) — legacy dashboard template
2. `web/static/js/DIAGNOSTICO_DASHBOARD.js` (44 lines) — diagnostic comments

---

## Summary

| Metric | Before | After |
|--------|--------|-------|
| Inline `style=` in dashboard.html | 13 | 1 (JS-controlled) |
| Inline `style=` in base.html | 8 | 0 |
| Dead CSS selectors | 20+ | 0 |
| Hardcoded font-size/weight in CSS | 15+ | 0 (all tokenized) |
| Broken spacing scale values | 2 | 0 |
| New reusable CSS classes added | — | 22 |
| Design system tokens enforced | Partial | Complete |
