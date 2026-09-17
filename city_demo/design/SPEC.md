# City lab design

Concept: concept.png, generated full primary screen at 1536 × 1024. This is an implementation reference, not a measured result.

Palette: warm off-white #f5f4ef, forest #183f35, charcoal #202928, muted #6b7475, fine gray #d0d3cc borders. Serif title and metric values; system sans controls. 6px corners; no shadows on UI. Header, title, left 3D viewport, right open control rail, shallow four-column metrics, methodology footer. Mobile stacks viewport then rail. Copy follows the concept: Jev / City lab; Protocol; Export run; A city. Every decision counts.; Watch driving decisions unfold. Compare timing, observations and control.; Driver; Challenge; Timing; Seed; Start drive; Decision stream; Distance; Collisions; Red lights; Model latency.

Required functional additions: Stop, replay and screenshot capture, explicit mode assistance/vision availability, progress and per-question usage. Native controls and live values replace image text. Viewport follows the actual simulation and is never a static background.

Intentional deviations: the concept produced photorealistic architecture despite requesting low-poly meshes. Real low-poly Three.js geometry is necessary for free camera movement, consistent collision geometry, and true screenshots. No image sprites or fake raster city: buildings, roads, cars, signals and trees are physical meshes. Static ES modules follow this repository's dependency-free, GitHub Pages demos instead of adding a React build pipeline. Three.js is pinned and vendored. WebGL scene palette follows concept; physical layout follows the scientific simulator.
