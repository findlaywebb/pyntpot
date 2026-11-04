"""The maps lane's pending violations of the public-surface gates.

It holds every path under `pyntpot.maps.` that is not under
`pyntpot.maps.lettering.pipeline.`.

This is the ratchet of plan 006: `test_public_signatures.py` and `test_field_docs.py`
fail on a violation not listed here and on a listed entry that no longer violates, so the
sets only shrink. The maps lane empties both; then the ratchet is deleted.
"""

#: Private canonical paths a public signature reaches today.
SIGNATURES: frozenset[str] = frozenset(
    {
        "pyntpot.maps.providers.base.Features",
        "pyntpot.maps.providers.base.Elevation",
        "pyntpot.maps.providers.base.ElevationGrid",
        "pyntpot.maps.track.BoundingBox",
        "pyntpot.maps.credit.Credit",
        "pyntpot.maps.card.Card",
        "pyntpot.maps.plates.Manifest",
        "pyntpot.maps.plates.DarkGrid",
        "pyntpot.maps.basemap.Layers",
        "pyntpot.maps.basemap.River",
        "pyntpot.maps.basemap.Road",
        "pyntpot.maps.basemap.ElevationPatch",
        "pyntpot.maps.basemap.Line",
        "pyntpot.maps.projection.Projection",
        "pyntpot.maps.lettering.label.Label",
        "pyntpot.maps.lettering.label.Span",
        "pyntpot.maps.annotations.Landmark",
        "pyntpot.maps.annotations.SpanRequest",
        "pyntpot.maps.annotations.MAX_NOTES",
        "pyntpot.maps.annotations.MAX_NOTE_CHARS",
        "pyntpot.maps.vector_layer_build.VectorArea",
        "pyntpot.maps.vector_layer_build.VectorLine",
        "pyntpot.maps.vector_layer_build.HillshadeBand",
        "pyntpot.maps.vector_layer_build.HillshadeImage",
        "pyntpot.maps.style_groups.CardStyle",
        "pyntpot.maps.style_groups.RibbonStyle",
        "pyntpot.maps.style_groups.CoverStyle",
        "pyntpot.maps.style_groups.RouteStyle",
        "pyntpot.maps.style_groups.BasemapStyle",
        "pyntpot.maps.style_groups.LetteringPolicy",
        "pyntpot.maps.style_groups.RouteInk",
    }
)

#: Checked classes and module attributes whose fields or docstring break the field rule today.
FIELD_DOCS: frozenset[str] = frozenset(
    {
        "pyntpot.maps.annotations.MAX_NOTES",
        "pyntpot.maps.annotations.MAX_NOTE_CHARS",
        "pyntpot.maps.basemap.Line",
        "pyntpot.maps.lettering.label.Label",
        "pyntpot.maps.lettering.label.Span",
        "pyntpot.maps.providers.opentopodata.OpenTopoData",
        "pyntpot.maps.style_groups.BasemapStyle",
        "pyntpot.maps.style_groups.CardStyle",
        "pyntpot.maps.style_groups.CoverStyle",
        "pyntpot.maps.style_groups.LetteringPolicy",
        "pyntpot.maps.style_groups.RibbonStyle",
        "pyntpot.maps.style_groups.RouteInk",
        "pyntpot.maps.style_groups.RouteStyle",
        "pyntpot.maps.track.BoundingBox",
    }
)
