#!/bin/bash
# Build DMG installer for HousePhotoMapper using pyappdist
# Requires: CODESIGN_IDENTITY and NOTARY_PROFILE environment variables

set -euo pipefail

# Check for required environment variables
if [[ -z "${CODESIGN_IDENTITY:-}" ]]; then
    echo "ERROR: CODESIGN_IDENTITY environment variable not set"
    echo "Set it to your Developer ID Application certificate name, e.g.:"
    echo '  export CODESIGN_IDENTITY="Developer ID Application: Your Name (TEAMID)"'
    exit 1
fi

if [[ -z "${NOTARY_PROFILE:-}" ]]; then
    echo "ERROR: NOTARY_PROFILE environment variable not set"
    echo "Set it to your notarytool profile name, e.g.:"
    echo '  export NOTARY_PROFILE="notary-profile"'
    exit 1
fi

echo "Building HousePhotoMapper DMG..."
echo "Code Sign Identity: $CODESIGN_IDENTITY"
echo "Notary Profile: $NOTARY_PROFILE"

# Build the DMG
uv run pyappdist build macos-arm64-dmg

echo "DMG built successfully at appdist/macos-arm64-dmg/dist/"
ls -la appdist/macos-arm64-dmg/dist/