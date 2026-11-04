---
name: Ether AI Voice
description: A voice-first local assistant interface with a guided three-sample training score.
colors:
  sky: "#e9f4ff"
  sky-deep: "#d9ecfb"
  paper: "#f8fbff"
  white: "#ffffff"
  ink: "#281541"
  ink-soft: "#4d3a66"
  ink-muted: "#685a7c"
  purple: "#351c58"
  purple-hover: "#472878"
  blue: "#315cb8"
  blue-soft: "#d7e7ff"
  lilac: "#d9d0f8"
  line: "#c9d9eb"
  line-strong: "#a8bfd9"
  success: "#176448"
  success-bg: "#e2f4eb"
  error: "#9c2e4c"
  error-bg: "#fff0f4"
  warning: "#7d4e0e"
  warning-bg: "#fff1d3"
typography:
  display:
    fontFamily: "Plus Jakarta Sans, Segoe UI, sans-serif"
    fontSize: "clamp(2.25rem, 4.2vw, 3.7rem)"
    fontWeight: 650
    lineHeight: 1.06
    letterSpacing: "-0.035em"
  title:
    fontFamily: "Plus Jakarta Sans, Segoe UI, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 700
    lineHeight: 1.25
    letterSpacing: "-0.025em"
  body:
    fontFamily: "Plus Jakarta Sans, Segoe UI, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: "Plus Jakarta Sans, Segoe UI, sans-serif"
    fontSize: "0.83rem"
    fontWeight: 700
  control:
    fontFamily: "Plus Jakarta Sans, Segoe UI, sans-serif"
    fontSize: "0.86rem"
    fontWeight: 700
    lineHeight: 1.2
  navigation:
    fontFamily: "Plus Jakarta Sans, Segoe UI, sans-serif"
    fontSize: "0.88rem"
    fontWeight: 650
    lineHeight: 1.2
  chip:
    fontFamily: "Plus Jakarta Sans, Segoe UI, sans-serif"
    fontSize: "0.78rem"
    fontWeight: 650
    lineHeight: 1.3
  card-title:
    fontFamily: "Plus Jakarta Sans, Segoe UI, sans-serif"
    fontSize: "0.96rem"
    fontWeight: 720
    letterSpacing: "-0.01em"
  phrase:
    fontFamily: "Palatino Linotype, Book Antiqua, Georgia, serif"
    fontSize: "clamp(1.05rem, 1.7vw, 1.3rem)"
    fontWeight: 600
    lineHeight: 1.35
rounded:
  control: "9px"
  card: "15px"
  panel: "18px"
  pill: "999px"
  circle: "50%"
components:
  button-primary:
    backgroundColor: "{colors.purple}"
    textColor: "{colors.white}"
    rounded: "{rounded.control}"
    padding: "10px 17px"
    height: "44px"
    typography: "{typography.control}"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.purple}"
    rounded: "{rounded.control}"
    padding: "10px 17px"
    height: "44px"
    typography: "{typography.control}"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.ink-soft}"
    rounded: "{rounded.control}"
    padding: "10px 17px"
    height: "44px"
    typography: "{typography.control}"
  text-field:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "10px 13px"
    height: "46px"
    typography: "{typography.body}"
  navigation-tab:
    backgroundColor: "transparent"
    textColor: "{colors.ink-soft}"
    rounded: "0px"
    padding: "0 14px"
    height: "54px"
    typography: "{typography.navigation}"
  chip:
    backgroundColor: "transparent"
    textColor: "{colors.ink-soft}"
    rounded: "{rounded.pill}"
    padding: "8px 13px"
    height: "39px"
    typography: "{typography.chip}"
  card:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.card}"
    padding: "18px 19px 21px"
  voice-score:
    backgroundColor: "transparent"
    textColor: "{colors.ink-soft}"
    rounded: "0px"
    padding: "14px 4px"
    height: "93px"
---

# Design System: Ether AI Voice

## Overview

**Creative North Star: "The Rehearsal Score"**

Ether's interface treats voice training as a short, legible rehearsal: one prompt is in focus while two phrases wait in sequence. A light-blue page and dark-purple ink carry the training surface; a three-line score gives progress a small, specific visual identity without obscuring the words to speak or the recording controls.

The voice console, offline Q&A, and settings retain familiar web controls and use the same palette, rounded controls, and restrained state feedback. The interface is designed around local assistant use. Browser code is the source for this record; no live browser render was available during documentation.

**Key Characteristics:**
- Pale blue surfaces with dark-purple text and blue progress marks.
- One active task area, with profile access in a quieter side panel.
- State changes use short transitions; the score draw is the signature motion.

## Colors

The palette pairs a cool, light-blue ground with deep violet ink; blue marks progress, lilac separates the active step, and green, red, and amber identify outcomes.

### Primary
- **Light Blue Ground** (#e9f4ff): Main page background.
- **Deep Violet** (#351c58): Primary actions, selected navigation, and active training text.
- **Progress Blue** (#315cb8): Links, completed score marks, and small progress labels.

### Secondary
- **Soft Lilac** (#d9d0f8): Active marker and selected decorative accents.
- **Purple Hover** (#472878): Primary button hover state.

### Neutral
- **Deep Ink** (#281541): Main text and headings.
- **Soft Ink** (#4d3a66): Supporting text and secondary labels.
- **Muted Ink** (#685a7c): Hints and quiet metadata.
- **Paper** (#f8fbff) and **White** (#ffffff): Form fields, header, and cards.
- **Blue Lines** (#c9d9eb, #a8bfd9): Dividers and control outlines.

### Named Rules
**The Status Color Rule.** Reserve green, red, and amber for success, error, and warning states; pair status colors with readable text.

## Typography

**Display Font:** Plus Jakarta Sans when installed locally, with Segoe UI and sans-serif fallbacks.
**Body Font:** Plus Jakarta Sans when installed locally, with Segoe UI and sans-serif fallbacks.
**Label/Mono Font:** No distinct label or monospace family is used.

**Character:** Compact sans-serif headings keep the task direct. The spoken phrases switch to a restrained italic serif, giving the score a little editorial character while keeping supporting instructions plain.

### Hierarchy
- **Display** (650, `clamp(2.25rem, 4.2vw, 3.7rem)`, 1.06): Main section and console headings; at narrow widths it becomes `clamp(2.1rem, 10vw, 3rem)`.
- **Title** (700, 1.25rem, 1.25): Training workbench and section card titles.
- **Body** (400, 1rem, 1.55): Instructions, descriptions, and standard text.
- **Label** (700, 0.83rem): Form labels and compact step labels.
- **Phrase** (600 italic, Palatino Linotype / Book Antiqua / Georgia, `clamp(1.05rem, 1.7vw, 1.3rem)`, 1.35): The three spoken sample prompts.

## Layout

The shell uses a centered header up to 1320px and a main content measure up to 1240px, both with 32px desktop gutters. The header is sticky and keeps the engine status alongside tab navigation. The opening training area uses a two-column grid: a wide workbench and a narrower profile panel; the workbench receives 40px padding at its widest, and the score rows are at least 93px tall. Console and settings use two-column grids.

At 1040px the header navigation moves to its own horizontally scrollable row and the content narrows to 900px. At 720px the training, console, and settings grids stack; page gutters become 16px and workbench padding contracts. At 380px the tab and score columns tighten again. The tabs use tablist/tab/tabpanel semantics, roving tab focus, and Arrow, Home, and End navigation; inactive panels are hidden from assistive technology. Layout spacing is expressed with local gap and padding values rather than a named spacing scale; preserve the larger breathing room around the training score and the smaller gaps within controls.

## Elevation & Depth

The interface is mostly flat. Borders and pale-blue/lilac surface changes establish hierarchy; shadows appear only around interactive score markers and the listening microphone state. Keep resting cards crisp and avoid adding persistent elevation that competes with the score.

### Shadow Vocabulary
- **Score Marker** (`0 0 0 1px #8c79aa`, active `0 0 0 3px #d9d0f8`, complete `0 0 0 2px #c9dcff`): Ring separates each marker from its score staff.
- **Listening Control** (`0 7px 17px rgba(40, 21, 65, 0.18)`): Hover lift on the console microphone; listening uses a tinted outer ring.

## Shapes

Controls use 9px corners; cards use 14–15px, and the training panels use 18px. Pills and circular microphone/brand controls use full rounding. Thin blue-gray borders define cards and fields, while the score staff itself stays square and line-based.

## Components

### Buttons
Buttons are compact and tactile, with a small lift on hover and clear disabled opacity.
- **Shape:** 9px radius; minimum height 44px, with 10px 17px padding.
- **Primary:** Purple fill (#351c58) with white text; hover shifts to #472878.
- **Hover / Focus:** 140ms transform and color transitions; keyboard focus uses a 3px violet outline with 3px offset. Disabled buttons use reduced opacity and a not-allowed cursor.
- **Secondary / Ghost:** Secondary uses a purple outline and text; ghost uses a blue-gray outline and supporting ink.

### Chips
Sample-query chips have a transparent ground, thin blue border, pill shape, and supporting text. Hover adds a pale lilac surface and purple text.

### Cards / Containers
Cards use white or pale blue surfaces with thin borders, 14–15px corners, and 18–21px internal padding. The main training workbench is white; the saved-profile panel uses a deeper blue surface.

### Inputs / Fields
Text and select fields use a pale paper fill, blue-gray stroke, 9px radius, 46px minimum height, and dark ink. Hover deepens the border; keyboard focus receives the shared violet outline. The search field places its icon inside a bordered wrapper and moves the focus outline to that wrapper.

### Navigation
Tabs are plain, transparent controls with a 2px bottom indicator on the active tab. Hover adds a faint blue surface. At tablet widths they scroll horizontally in a separate header row; their active state is exposed with `aria-selected`, and the tablist supports roving focus and Arrow/Home/End keys.

### Voice Score
Three prompt rows align a number, a five-line staff, and the spoken phrase. The current sample enlarges its violet marker; each saved sample draws a blue line across its staff and settles to a distinct marker. Text labels and prompt copy carry the step meaning, so progress is not color-only.

## Do's and Don'ts

### Do:
- **Do** lead the home view with voice training and keep the current spoken prompt above its recording action.
- **Do** use blue for progress, purple for the current action, and status colors only for status.
- **Do** preserve the 3px focus outline and the reduced-motion override.
- **Do** collapse the training columns to one column below 720px.

### Don't:
- **Don't** let the score staff replace prompt text, sample numbering, or familiar recording controls.
- **Don't** add a persistent shadow to flat resting cards.
- **Don't** rely on color alone for saved, active, error, or success states.
- **Don't** add external font or image dependencies to the local interface without a product need.
