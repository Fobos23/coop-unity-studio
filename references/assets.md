# Assets: installed packs first, then your own

## Order of choice

1. **What is installed.** Run `python <skill>/scripts/find-packs.py <project>` before making any model, texture,
   decal, sound, music or animation. It lists:
   - packs already in the project (`Assets/<Publisher or Pack>/…`: counts of models, prefabs, textures, materials,
     animations, audio) — usable right now;
   - packs downloaded from the Asset Store but not imported (`%APPDATA%/Unity/Asset Store-5.x/<Publisher>/<Category>/*.unitypackage`)
     — one import away;
   - UPM packages from the manifest that carry content.
2. **Offer what fits.** Show the director the candidates for the need: pack, piece names, a contact sheet (lay the
   prefabs out far from the scene and render one frame per eval, or shoot them in a build), and the licence. Use a
   pack piece refitted and recoloured before building one. A tool on a belt from the pack beats a wrench made of boxes.
3. **None installed, or the director says none fits → make it yourself**:
   - 3D: Blender headless with Python (`blender.exe -b --factory-startup --python script.py -- args`); no Blender
     MCP needed. Export FBX, verify (bones, UV sets, groups), import by an editor step;
   - textures, decals, UI art: an image generator if the environment has one (e.g. Codex `exec`, see
     `unity-windows.md`), else procedural in code;
   - sound: a pack, a generator or a placeholder that the director replaces; never silence in a gym.
4. **Buying a pack** is the director's decision (money). Name the pack, price, licence and what it replaces.

## Surface, wear and form

- **Form** is geometry: silhouette, construction, doors, drawers, handles, folds, a shifted plank.
- **Surface** (material, pattern, grain, cartoon shading) is a texture.
- **Wear** (stains, chips, rust, drips, cracks, broken glass, blood) is a decal or a texture mask. Never extra
  polygons.
- Test: if removing a detail does not change the silhouette seen from 2 m, it is a texture or a decal.
- Plain models without a surface layer read as too smooth next to pack art: every own model gets a texture layer and
  a decal layer in the project's style. Measure the style from the installed packs (palette, outline, tones) and
  write it into the project's art doc before mass production.

## Importing without hanging the editor

- `AssetDatabase.ImportPackage` by eval opens a modal and hangs the editor. Extract the `.unitypackage` (tar.gz of
  `<guid>/asset`, `asset.meta`, `pathname`) with `python <skill>/scripts/extract-unitypackage.py <pkg> <project>
  [--match REGEX] [--list]`: it writes `asset` + `.meta` (and parent folder metas, keeping GUIDs), then
  `AssetDatabase.Refresh()` by eval.
- Packages that update Burst or other packages show "Package Update Detected"; after a forced close Unity shows
  "Recovering Scene Backups" and "Packages with Errors". Clear dialogs with `unity-dialogs.ps1`.
- Old shaders in URP: legacy particles render black squares; convert materials to URP/Lit or URP particle shaders.
  Dark default skins (weapons) turn into black blobs in low light: copy to URP/Lit with a lighter skin.
- A ScriptableObject or MonoBehaviour class must live in a file of the same name, or the asset loads as null in the
  player build only.
- Audio import: configure importers inside `StartAssetEditing/StopAssetEditing` first, then load clips and fill the
  bank; a reimport mid-fill destroyed the bank.
- The first icon rendered in an editor session can be empty (async shader compilation): turn
  `ShaderUtil.allowAsyncCompilation` off while rendering icons.

## Licences

Every third-party asset goes into `docs/LICENSES.md` when it enters the project: pack, author, source URL, licence
(Asset Store EULA, CC0, MIT…), what is used, AI-generated or not. Credits and the store's AI disclosure are built from
it in phase 8.

## Characters

Body shapes and clothing from pack characters: `characters.md`.
