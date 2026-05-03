# Pixel Office Visualization — Design

**Date:** 2026-05-03  
**Project:** Mission Control — Agent Pipeline Visualization  
**Status:** Approved for implementation

## Executive Summary

Build a real-time canvas-based pixel art office visualization showing the agent pipeline in motion. 4 R&D agents in a 2×2 grid (Sports, Finance, Creative, Tech), Examination agent below them, Executioner agent at the bottom. Characters are detailed & shaded pixel people holding domain objects. Real-time data from backend APIs, subtle animations, rich information density (importance scores, categories, pending counts).

---

## Visual Design

### Layout

```
┌──────────────────────────────┐
│  Sports        Finance        │
│  (8/10)        (7/10)         │
│  ⚽ Agent      💰 Agent       │
│                               │
│  Creative      Tech           │
│  (5/10)        (9/10)         │
│  🎨 Agent      ⚙️ Agent      │
├──────────────────────────────┤
│     Examination Agent         │
│     📋 "Analyzing 12..."      │
├──────────────────────────────┤
│     Executioner Agent         │
│     ⚡ "Executing..."         │
└──────────────────────────────┘
```

Canvas dimensions: 1000×800px (responsive, scales to container)
Grid: 2×2 for R&D agents (500×300px each with 20px padding)
Examination: Full width, 200px height
Executioner: Full width, 200px height

### Character Design

All characters are **detailed & shaded pixel art** (16-bit style):
- Better human proportions (smaller head relative to body, realistic limbs)
- Clothing detail and shading for depth
- Simple expressive face (eyes, mouth)
- Color-coded body matching agent domain

**Character holding objects:**
- **Sports Agent:** Holds football
- **Finance Agent:** Holds money bag with $ symbol
- **Creative Agent:** Holds paintbrush
- **Tech Agent:** Holds gear/wrench

### Per-Agent Display (R&D Agents)

Each agent card shows:
1. **Character** — Detailed & shaded pixel person (60×60px)
2. **Importance Score** — Above character, color-coded:
   - 🔴 Red: 1-3 (low impact)
   - 🟡 Yellow: 4-6 (medium impact)
   - 🟢 Green: 7-10 (high impact)
3. **Category Badge** — Below score (injury, market_movement, design_trend, sec_vuln, etc.)
4. **Latest Finding** — Speech bubble with truncated text (max 40 chars)
5. **Pending Count** — "X pending findings" in muted text
6. **Status Indicator** — Green (idle) or yellow (working) pulse

### Examination Agent Display

- **Character** — Detailed & shaded pixel person at desk with papers
- **Status text** — "Idle" or "Analyzing X findings..."
- **Visual queue** — Papers slowly stack/drift when findings pending (visual metaphor)
- **Pending count** — Bold number: "12 pending examinations"

### Executioner Agent Display

- **Character** — Detailed & shaded pixel person at action desk
- **Status modes:**
  - **Idle:** "Idle, no pending actions" (green)
  - **Executing:** "Executing war room update..." with brief flash on completion
  - **Awaiting approval:** "Awaiting 3 user approvals" + 📱 SMS indicator
- **Recent action result** — Last action result (success/pending/failed)

---

## Animations (Subtle & Calm)

All animations are professional, low-energy, non-distracting:

- **Idle breathing:** Gentle 1-2px pulse every 2 seconds (slow, meditative)
- **Working indicator:** Soft yellow glow on status when agent is active (not flashing)
- **Finding fade-in:** New findings fade in over 300ms when they arrive
- **Color transitions:** Score color changes fade smoothly (not instant swaps)
- **Paper stacking:** Examination desk shows papers slowly accumulating (1px vertical drift per second as queue grows)
- **Action flash:** Brief white/green flash when Executioner completes an action (500ms duration)
- **No sounds, no particles, no bouncing** — Focused monitoring aesthetic

---

## Data Integration

### Real-Time Updates (Poll every 5 seconds)

1. **GET `/agent-pipeline/status`**
   - Returns agent states (idle/working/analyzing/executing)
   - Pending counts per agent
   - Last activity timestamp

2. **GET `/agent-pipeline/findings?importance_min=6`**
   - Latest high-value findings per agent
   - Importance score, category, text

3. **GET `/agent-pipeline/examinations`**
   - Pending examinations count
   - Current examination being analyzed

4. **GET `/agent-pipeline/actions`**
   - Recent actions (last 24 hours)
   - Action type, result, timestamp

### Data Mapping

- **R&D Agent display:**
  - Latest finding from that agent → importance score + category + text in speech bubble
  - Pending count → from examinations where finding.agent_name matches
  - Status → from status endpoint

- **Examination Agent:**
  - Pending count → examinations with status='pending_action'
  - Status → "idle" if pending=0, else "analyzing"

- **Executioner Agent:**
  - Pending actions → actions with result='pending'
  - Status → "idle" if pending=0, else "executing"

---

## Color Scheme

### Importance Scores
- 🔴 **Red** (#ef4444): 1-3 (low impact)
- 🟡 **Yellow** (#fbbf24): 4-6 (medium impact)
- 🟢 **Green** (#10b981): 7-10 (high impact)

### Agent Body Colors
- **Sports:** Blue (#3b82f6)
- **Finance:** Green (#10b981)
- **Creative:** Purple (#a855f7)
- **Tech:** Orange (#f97316)

### Status Colors
- **Idle:** Green (#10b981)
- **Working:** Yellow (#fbbf24)
- **Alert/Error:** Red (#ef4444)

### Category Colors (badges)
- Injury: Red (#ef4444)
- Trade: Blue (#3b82f6)
- Market movement: Green (#10b981)
- Design trend: Purple (#a855f7)
- Tech news: Orange (#f97316)
- Security vulnerability: Crimson (#dc2626)

### Background
- Office background: Dark blue (#1a1a2e)
- Floor grid: Dark gray (#16213e)
- Grid lines: Subtle blue (#0f3460)
- Agent card background: Dark gray (#2d3748)

---

## Technical Approach

### Component Structure
- **PixelOffice.jsx** — Main component (existing file, to be enhanced)
- Use HTML5 Canvas for rendering (pixel-perfect, smooth animation)
- requestAnimationFrame for animation loop
- useEffect hook for data polling (5s interval)
- useState for latest data from APIs

### Canvas Rendering Strategy
- Clear canvas each frame
- Draw in layers:
  1. Background (office, floor, grid)
  2. Agent cards (backgrounds, borders)
  3. Characters (pixel art)
  4. Information overlays (scores, badges, text)
  5. Animations (pulses, fades, glows)

### Animation Implementation
- Track animation state per agent (idle/working, pulse phase, etc.)
- Use currentTime to drive smooth motion (not frame-dependent)
- Transition functions for fade-in/out
- requestAnimationFrame for 60fps smooth updates

---

## Edge Cases & Error Handling

- **Empty state:** Agents show "waiting for first finding..." in light gray text
- **No data:** Display fallback values (0 pending, idle status)
- **API error:** Graceful fallback; show last known state with visual error indicator
- **High volume:** Show only most recent 5 findings per agent (prevent overwhelming display)
- **Slow updates:** Smooth transitions hide lag; show "last updated: Xs ago" timestamp

---

## Success Criteria

✅ All 6 agents visible with rich information (score, category, pending count, latest finding)
✅ Characters are recognizable and have personality (detailed & shaded pixel art)
✅ Data flows visually left-to-right (findings → examination → execution)
✅ Animations are subtle and professional (no distracting motion, smooth transitions)
✅ Real-time updates every 5 seconds, visible within 1-2 seconds of data change
✅ Color-coding makes importance/status scannable at a glance
✅ Component fits within Mission Control dashboard as a full-width panel
✅ Canvas renders cleanly at 1x and 2x pixel density (retina displays)
✅ Responsive to different screen sizes (scales gracefully)

---

## Implementation Phases

**Phase 1:** Set up canvas, draw static office and agent cards
**Phase 2:** Implement detailed & shaded pixel character rendering function
**Phase 3:** Wire up API polling and update agent display data
**Phase 4:** Implement animations (pulses, fades, paper stacking, action flashes)
**Phase 5:** Polish, edge cases, responsive scaling, testing

---

## Next Steps

1. Create detailed implementation plan with task breakdown
2. Implement canvas rendering and static layout
3. Build character rendering system
4. Integrate with backend APIs
5. Add animations and polish
6. Test in Mission Control dashboard
