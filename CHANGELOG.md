# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.0.2] - 2026-10-09

A second pre-release candidate for the upstream consumer's migration: the candidate export, the vector layers and a fed route ink become public (ADR 0027). Not for general use; 0.1.0 is the first release.

### Added

- `pyntpot.maps.vector_layers` and `VectorLayers`: the basemap's layers as SVG path data,
  read from the fetch cache, for a caller that draws its own map.
- `pyntpot.maps.candidate_export`: what a track passes, read from the fetch cache under
  the track's key (was the private `landmark_export`).

### Changed

- `Style.with_route_ink`: a caller feeds the route's colour and width; the default route
  ink is unchanged.

## [0.0.1] - 2026-10-09

A pre-release candidate for the upstream consumer's migration (P8 of the port plan). Not
for general use; 0.1.0 is the first release.
