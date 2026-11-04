# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Individual users running Ether as a private local voice assistant.

## Product Purpose

Ether lets a person speak with a local assistant, enroll and verify a voice profile, and ask questions with a locally configured language model. Success means the user can set up a recognizable voice profile and understand whether the local assistant is ready to listen and answer.

## Positioning

Ether is an offline-capable assistant built around local speech recognition, local language models, and voice-profile training. The product keeps the interaction and voice profile on the user's device instead of relying on a hosted assistant.

## Operating Context

Users open Ether in a browser on the device running the assistant, grant microphone access, and move between voice training, the listening console, offline question answering, and engine settings.

## Capabilities and Constraints

- The interface supports three-step voice-profile enrollment, speaker verification, live voice input, spoken responses, offline question answering, and acoustic/model settings.
- Voice recognition uses a local Whisper model. Offline answers require a locally configured language model. Microphone access is required for recording and verification.
- Web search and Spotify control are not product capabilities. The app's README says initial setup may require internet access; the core voice flow is intended to work offline afterward.
- Keep configuration and status messages accurate; do not present unverified performance figures as guarantees.

## Brand Commitments

The product is named Ether AI Voice. For this refresh, the user requires a light-blue background, dark-purple foreground, distinctive purposeful animation, and a training-first opening view. No logo or other approved brand assets were supplied.

## Evidence on Hand

The existing interface, FastAPI routes, voice-engine modules, and README document the supported flows. No verified customer testimonials, performance benchmarks, or approved photography are present.

## Product Principles

- Make local processing and readiness understandable.
- Give voice enrollment a clear, recoverable three-step path.
- Keep microphone, loading, error, and profile states explicit.
- Do not imply online search, Spotify playback, or unsupported performance claims.
