"""The shipped providers satisfy the public provider protocols.

The annotated assignments are the real check: `ty check` rejects a provider that does
not match its protocol. Building a provider makes no request.
"""

from pyntpot.maps import Elevation, Features, OpenTopoData, OverpassFeatures

CONTACT = "pyntpot-tests@example.invalid"


def test_the_shipped_providers_satisfy_the_protocols() -> None:
    """`OverpassFeatures` is a `Features` and `OpenTopoData` an `Elevation`, each with an id."""
    features: Features = OverpassFeatures(contact=CONTACT)
    elevation: Elevation = OpenTopoData(contact=CONTACT)
    assert isinstance(features.id, str)
    assert features.id
    assert isinstance(elevation.id, str)
    assert elevation.id
