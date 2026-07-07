---
name: Industrial Luxury
colors:
  surface: '#17130d'
  surface-dim: '#17130d'
  surface-bright: '#3f3831'
  surface-container-lowest: '#120d08'
  surface-container-low: '#201b15'
  surface-container: '#241f19'
  surface-container-high: '#2f2923'
  surface-container-highest: '#3a342d'
  on-surface: '#ece0d6'
  on-surface-variant: '#d5c4b2'
  inverse-surface: '#ece0d6'
  inverse-on-surface: '#362f29'
  outline: '#9d8e7e'
  outline-variant: '#514537'
  surface-tint: '#fbba64'
  primary: '#fbba64'
  on-primary: '#462a00'
  primary-container: '#c58b3a'
  on-primary-container: '#442900'
  inverse-primary: '#845400'
  secondary: '#ffb694'
  on-secondary: '#571f00'
  secondary-container: '#ff6a00'
  on-secondary-container: '#571f00'
  tertiary: '#90cdff'
  on-tertiary: '#003350'
  tertiary-container: '#5c9ccd'
  on-tertiary-container: '#00324d'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffddb6'
  primary-fixed-dim: '#fbba64'
  on-primary-fixed: '#2a1800'
  on-primary-fixed-variant: '#643f00'
  secondary-fixed: '#ffdbcc'
  secondary-fixed-dim: '#ffb694'
  on-secondary-fixed: '#351000'
  on-secondary-fixed-variant: '#7b2f00'
  tertiary-fixed: '#cbe6ff'
  tertiary-fixed-dim: '#90cdff'
  on-tertiary-fixed: '#001e30'
  on-tertiary-fixed-variant: '#004b72'
  background: '#17130d'
  on-background: '#ece0d6'
  surface-variant: '#3a342d'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.04em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: '1.2'
  display-mono:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '500'
    lineHeight: '1.5'
    letterSpacing: 0.1em
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  label-sm:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1.0'
    letterSpacing: 0.02em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 12px
  md: 24px
  lg: 48px
  xl: 80px
  gutter: 24px
  margin-mobile: 20px
  margin-desktop: 64px
---

## Brand & Style
The design system embodies a fusion of precision engineering and cinematic luxury. It is crafted for a high-intelligence audience that values technical sophistication and uncompromising quality. The aesthetic direction is "Industrial Luxury"—a mix of **High-Contrast Minimalism** and **Glassmorphism**.

The interface should feel like a high-end physical console: heavy but refined, dark but illuminated. Key characteristics include:
- **Cinematic Depth:** Deep blacks contrasted with metallic accents and glowing elements.
- **Engineering Precision:** Tight alignments, monospaced data, and thin, sharp borders.
- **Intelligent Motion:** Subtle micro-interactions that respond to user intent with "magnetic" physics.

## Colors
The palette is built on a foundation of **Graphite Black**, utilizing layered dark neutrals to create structural hierarchy. 

- **Primary Accent (Copper Gold):** Used for primary actions, branding elements, and high-value highlights.
- **Secondary Accent (AMD Orange):** Reserved for technical indicators, active states, and energetic highlights. Use sparingly to maintain a premium feel.
- **Gradients:** Implement linear gradients for buttons and active states (e.g., `#C58B3A` to `#FF6A00`) at a 135-degree angle to simulate metallic light reflection.
- **Borders:** Use low-opacity versions of accents (15-25%) for "glowing" border effects on glass surfaces.

## Typography
The system utilizes a dual-font approach to balance human-centric design with technical precision.

- **Inter:** Serves as the primary typeface for headlines and body text. Headlines should use tight tracking and bold weights to evoke a "Tesla-inspired" confidence.
- **Geist:** Used for data points, labels, and secondary metadata. Its monospaced structure reinforces the "Industrial" narrative and ensures readability for technical figures.
- **Hierarchy:** Use `display-mono` for small eyebrows or section headers above large `headline-xl` titles to create high-contrast editorial layouts.

## Layout & Spacing
The layout philosophy relies on **Generous Breathing Room** to maintain a premium, uncluttered feel.

- **Grid:** Use a 12-column fluid grid for desktop and a 4-column grid for mobile. 
- **Rhythm:** An 8px base unit drives all spacing. For large cinematic sections, favor `xl` (80px) vertical padding.
- **Safe Areas:** On mobile, maintain a minimum 20px horizontal margin. 
- **Reflow:** Cards should stack vertically on mobile but maintain a minimum 24px gutter to ensure the "floating" effect remains visible.

## Elevation & Depth
Depth is created through **Layered Glassmorphism** and light-based hierarchy rather than traditional heavy shadows.

- **Surface Tiers:** 
  - Level 0: Background (`#0D1117`).
  - Level 1: Floating Cards (`#202733` at 80% opacity) with a 20px backdrop blur.
  - Level 2: Overlays and Tooltips with higher opacity and subtle inner glows.
- **The Glow Border:** Every floating element should have a 1px solid border. Use a top-down linear gradient border (Primary Accent at 30% opacity to Background at 0% opacity) to simulate a rim-light effect.
- **Shadows:** Use a single, very large, very soft ambient shadow for the highest-level cards: `0px 24px 48px rgba(0, 0, 0, 0.5)`.

## Shapes
Shapes are disciplined and modern. 

- **Containers:** Standard cards use a 0.5rem (8px) radius to maintain a structural, architectural look.
- **Interactive Elements:** Buttons and chips use the `rounded-xl` (24px) or full-pill setting to create a friendly, touch-accessible contrast against the sharper layout grid.
- **Inputs:** Maintain the 8px standard for input fields to align with the card geometry.

## Components
Consistent application of the "Industrial Luxury" style across elements:

- **High-Fidelity Buttons:** Primary buttons feature the metallic Copper-to-Orange gradient. On hover, apply a "magnetic" effect (slight translation toward the cursor) and increase the border-glow intensity.
- **Floating Glass Cards:** Use the 20px backdrop-blur consistently. Ensure the 1px rim-light border is present on all sides to separate the card from the dark background.
- **Status Chips:** Use `display-mono` text. Include a small circular "LED" indicator to the left of the text that pulses slowly when active.
- **Input Fields:** Dark background (`#1A1F29`) with a 1px border that transitions from Gray to Copper Gold upon focus. Text should be high-contrast Primary White.
- **Progress Bars:** Thin, technical bars with a glowing leading edge. Use the secondary accent (Orange) for active progress to symbolize energy and movement.
- **Animations:** All sections must use a `fade-in-up` entrance (300ms, cubic-bezier(0.2, 0.8, 0.2, 1)). Micro-interactions on buttons should feel "snappy" but damped.