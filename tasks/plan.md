# Living Paper Dragon — approved feature scope

The owner approved all five distinct forms, language palettes, current and record
weekly streak effects, richer motion, and all repositories their account can read.

1. Collect owner-authored commits on all readable branches; deduplicate by SHA
   across branches and forks. Include today. Fail closed on incomplete access.
2. Derive persistent growth, weekly streaks, language palette and motion mode.
3. Supply distinct reference-style hatchling/young/growing/mature/elder artwork;
   retain the detailed growing form. Apply language colors to red paper panels,
   preserving ivory paper and gold. Add continuous flowing body deformation (avoiding seams from separately moving raster regions).
4. Integrate read-only repository credentials without exposing raw private data;
   preserve the existing profile until real private access is verified.
5. Run tests, inspect actual artwork, show the full diff, and publish a review
   branch. Main merges require the exact PR approval already required by review.

Growth counts unique authored commits. The calendar supplements active days for
streaks, but is never added to commit totals. This avoids counting merged commits
twice. Existing earned growth is retained during the migration.

Verification: python3 -m unittest discover -s tests -v; browser SVG image-mode
inspection; owner-authenticated run with Contents-read tokens for each resource
owner. No credential creation, no raw snapshots or private project names published.
