# Characters from pack bodies

Packs first (`assets.md`): a new body type, a zombie variant or a costume starts from an installed pack character.
The reference implementation with scripts is Zombolic's project skill `making-character-variants`
(`D:/Unity/FlatArtProjects/Zombolic/.claude/skills/making-character-variants`); port its scripts to the new pack
instead of writing new ones.

## The method

- **A new body is the pack body with moved vertices only.** Skeleton, topology, UV sets and skin weights stay, so the
  pack's animations, overlay shaders (blood) and face decals keep working. Shape by radial profiles along limbs and
  torso plus soft "blob" masses, in Blender headless.
- **Bulk needs its own Humanoid avatar with narrower arm muscle ranges**: shared animations were made for a thin body
  and drive arms into the new volume. Tune limits (shoulder down/up, arm down/up and front/back, twist, leg in/out),
  not the mesh.
- **Check animations on sheets**: render the same clips before (pack avatar) and after (new avatar) from the front
  and at 120°: idle, walk, run, crouch walk, plus reach clips (block with hands, phone at the ear, punch, carry).
  Hands must still reach the face and the chest.
- **Verify the FBX**: bone deviation 0, the same number of UV layers and vertex groups as the source.
- **Clothing and gear**: refit pack pieces to the new body (atlas, body weights, recolour) and hang tools on a belt;
  a tool in a flat pocket looks wrong. Build a piece yourself only when no pack piece fits.
- Silhouettes for enemy types (fast, fat, boss): distinct at 30 m in dusk, one palette per faction; hitbox numbers
  (capsule radius and height, head sphere) live in data and follow the visible head.

## Traps

| Symptom | Cause |
|---|---|
| animations play as a T-pose in editor previews | background editor does not tick; animators cull when unseen: check in the build with `-shots` |
| Humanoid avatar fails "Parent for … differs" | the exported hierarchy changed: keep the source armature names and parents |
| arms sink into the sides / hands in the belly | arm muscle limits too wide for the body |
| zombie pack differs from the human pack | other UV layout, palette, a jaw bone, hip joints lower: read the pack facts before reusing scripts |
