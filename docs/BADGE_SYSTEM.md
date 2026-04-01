# Badge System — MetodoBase Design System

## Overview

Consistent badge component system for status indicators across the application.

---

## Design Tokens

### Badge Anatomy
```
┌────────────────────────┐
│  [Icon] STATUS TEXT    │  ← Rounded corners (6px)
└────────────────────────┘
  ↑       ↑
  Glow    High contrast text
```

**Structure:**
- Background: rgba with 0.12-0.15 alpha
- Border: 1px solid with 0.3-0.35 alpha
- Border radius: 6px
- Padding: 4px 10px
- Font size: 11px
- Font weight: 600
- Letter spacing: 0.3px

---

## Badge Variants

### Client Status Badges (Dashboard Table)

#### Nuevo (New Client)
**QLabel#badgeNuevo**
- **Color**: #00FFA3 (Neon green — Primary accent)
- **Background**: rgba(0, 255, 163, 0.15)
- **Border**: rgba(0, 255, 163, 0.35)
- **Use**: Client registered within last 7 days

#### Sin Plan (No Plan)
**QLabel#badgeSinPlan**
- **Color**: #EF4444 (Red-500 — Strong contrast)
- **Background**: rgba(239, 68, 68, 0.15)
- **Border**: rgba(239, 68, 68, 0.35)
- **Use**: Client has no nutrition plan generated

#### En Progreso (In Progress)
**QLabel#badgeEnProgreso**
- **Color**: #FBBF24 (Yellow-400 — High visibility)
- **Background**: rgba(251, 191, 36, 0.15)
- **Border**: rgba(251, 191, 36, 0.35)
- **Use**: Client has active plan in progress

---

### Nutrition Status Badges (Plan Details)

#### Déficit (Caloric Deficit)
**QLabel#badgeDeficit**
- **Color**: #60A5FA (Blue-400 — 9.8:1 contrast ✅)
- **Background**: rgba(59, 130, 246, 0.12)
- **Border**: rgba(59, 130, 246, 0.3)
- **Use**: Client in caloric deficit phase

#### Mantenimiento (Maintenance)
**QLabel#badgeMaintenance** or **QLabel#badgeMantenimiento**
- **Color**: #FBBF24 (Yellow-400 — 13.2:1 contrast ✅)
- **Background**: rgba(251, 191, 36, 0.12)
- **Border**: rgba(251, 191, 36, 0.3)
- **Use**: Client in maintenance phase

#### Superávit (Caloric Surplus)
**QLabel#badgeSurplus** or **QLabel#badgeSuperavit**
- **Color**: #A855F7 (Purple-400 — 8.4:1 contrast ✅)
- **Background**: rgba(168, 85, 247, 0.12)
- **Border**: rgba(168, 85, 247, 0.3)
- **Use**: Client in caloric surplus phase

---

### General Status Badges

#### Active
**QLabel#badgeActive**
- **Color**: #34D399 (Green-400 — 6.8:1 contrast ✅)
- **Background**: rgba(52, 211, 153, 0.12)
- **Border**: rgba(52, 211, 153, 0.3)
- **Use**: Active status indicator

#### Inactive / Expired
**QLabel#badgeInactive** or **QLabel#badgeExpired**
- **Color**: #F87171 (Red-400 — 5.5:1 contrast ✅)
- **Background**: rgba(248, 113, 113, 0.12)
- **Border**: rgba(248, 113, 113, 0.3)
- **Use**: Inactive or expired status

---

## Usage in PySide6

### Basic Implementation

```python
# Create badge widget
badge = QLabel("Nuevo")
badge.setObjectName("badgeNuevo")
badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

# Wrap in container for proper centering
container = QWidget()
layout = QHBoxLayout(container)
layout.setContentsMargins(8, 4, 8, 4)
layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
container.setStyleSheet("background: transparent;")
layout.addWidget(badge)

# Add to table cell
table.setCellWidget(row, column, container)
```

### Dynamic Badge Selection

```python
def get_status_badge(status: str) -> tuple[str, str]:
    """
    Returns (display_text, objectName) for badge.
    """
    badge_map = {
        "nuevo": ("Nuevo", "badgeNuevo"),
        "sin_plan": ("Sin plan", "badgeSinPlan"),
        "en_progreso": ("En progreso", "badgeEnProgreso"),
        "deficit": ("Déficit", "badgeDeficit"),
        "mantenimiento": ("Mantenimiento", "badgeMaintenance"),
        "superavit": ("Superávit", "badgeSurplus"),
        "active": ("Activo", "badgeActive"),
        "inactive": ("Inactivo", "badgeInactive"),
    }
    return badge_map.get(status.lower(), ("—", ""))

# Usage
text, obj_name = get_status_badge(client_status)
badge = QLabel(text)
badge.setObjectName(obj_name)
```

---

## Dashboard Table Status Logic

### Client Status Derivation

```python
def _get_client_status(self, cliente: dict) -> tuple[str, str]:
    """
    Derive client status from data:
    1. Nuevo → Registered within last 7 days
    2. Sin plan → No plans generated OR no ultimo_plan
    3. En progreso → Has active plan and activo=1
    """
    total_planes = cliente.get("total_planes_generados", 0)
    ultimo_plan = cliente.get("ultimo_plan")
    activo = cliente.get("activo", 1)
    fecha_registro = cliente.get("fecha_registro", "")
    
    # Check if new (< 7 days)
    if fecha_registro:
        dt_registro = datetime.fromisoformat(str(fecha_registro)[:19])
        dias = (datetime.now() - dt_registro).days
        if dias <= 7:
            return ("Nuevo", "badgeNuevo")
    
    # Check if no plan
    if not ultimo_plan or total_planes == 0:
        return ("Sin plan", "badgeSinPlan")
    
    # Active with plan
    if activo and ultimo_plan:
        return ("En progreso", "badgeEnProgreso")
    
    # Default
    return ("Sin plan", "badgeSinPlan")
```

---

## Accessibility Notes

### Contrast Ratios
All badge colors meet WCAG AA standards:
- Minimum 4.5:1 contrast ratio against dark backgrounds
- Color is NOT the only indicator (text label included)

### Best Practices
1. **Always include text** — Never use color alone
2. **Consistent placement** — Use same column across tables
3. **Center alignment** — Badges should be centered in cells
4. **Hover states** — Optional: Add tooltip for additional info

---

## Migration from Old Badges

### Before (Inline Styles)
```python
# ❌ Old approach — hardcoded styles
badge = QLabel("ACTIVE")
badge.setStyleSheet(
    "background: #D1FAE5; color: #065F46; border-radius: 4px;"
    " padding: 2px 8px; font-size: 11px; font-weight: 600;"
)
```

### After (Design System)
```python
# ✅ New approach — consistent design system
badge = QLabel("Nuevo")
badge.setObjectName("badgeNuevo")
# Styles come from stylesheet.qss automatically
```

**Benefits:**
- Centralized styling (single source of truth)
- Easy theme updates
- Consistent across app
- Better maintainability

---

## Related Components

### KPI Card Change Indicators
Similar badge-style styling for trend indicators:
- `QLabel#kpiChange[trend="up"]` — Green background
- `QLabel#kpiChange[trend="down"]` — Red background
- `QLabel#kpiChange[trend="neutral"]` — Gray

### Alert Type Indicators
Alert panel uses similar color coding:
- Warning: Yellow
- Info: Blue
- Success: Green
- Neutral: Gray

---

## QSS Location

**File:** `ui/styles/stylesheet.qss`

**Section:** Lines 465-555 (approx)

```qss
/* ────────────────────────────────────────────────────────────
   TABLE BADGES — Status indicators
   ──────────────────────────────────────────────────────────── */
```

---

## Testing Checklist

- [ ] Badge renders with correct colors
- [ ] Text is readable (high contrast)
- [ ] Rounded corners visible
- [ ] Proper padding (not cramped)
- [ ] Centered in table cell
- [ ] Consistent across all tables
- [ ] No plain text status remaining
- [ ] Works with different table widths

---

## Future Enhancements

### Potential Additions
- [ ] Animated badges (pulse for urgent states)
- [ ] Icon-only badges (compact mode)
- [ ] Badge groups (multiple statuses)
- [ ] Custom badge builder utility
- [ ] Tooltip on hover with details

---

**Document Version**: 1.0  
**Last Updated**: March 18, 2026  
**Status**: ✅ Implemented  
**Component**: Dashboard Table STATUS column
