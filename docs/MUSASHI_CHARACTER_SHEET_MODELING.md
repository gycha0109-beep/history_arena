# Musashi character sheet — first 3D appearance checkpoint

Reference: the original four-view concept sheet generated and approved in the ChatGPT project conversation on 2026-11-14. A source image file is not mounted on the Windows PC; retain a separate copy of that image before automated image-to-3D.

## Visual requirements

- Rugged angular adult ronin face and messy black tied-up hair
- Dark distressed layered kimono with short torn sleeves
- Muted red knotted obi and hanging sash ends
- Wide trousers, forearm/calf textile bindings, straw sandals
- Long katana in right hand, shorter wakizashi in left
- Consistent 3/4, front, profile, and rear silhouettes

## Generated files

- tools/musashi_sheet_exterior_v3.py: standalone Blender 5.2.3 external-appearance script
- run-musashi-sheet-review.cmd: rerenders and opens the HTML review
- assets/characters/musashi/sheet_v3/: editable .blend, four view images, HTML

## Current quality — not approved

Procedural outfit/hair over an existing generic rigged body. The current render is a technical first-pass and does NOT meet the concept sheet's high-end quality. Face likeness, credible hair, clothing design and realistic garment folds, fabric deformation and skinning QA, material quality, and real combat animation remain unfinished. Do not present this as a finished Musashi.

The current Windows PC has GTX 1070 8GB VRAM and CPU-only PyTorch. Full high-end textured image-to-3D is not installed. Stable Fast 3D's official guidance estimates ~6GB VRAM for shape/textured mesh but Windows is experimental; successful deployment on this machine has NOT been established.

Do not restart walk/attack animation until a visually approved 3D character has been obtained.
