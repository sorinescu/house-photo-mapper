# Plan 01-05 Summary: macOS App Bundle and DMG

**Phase:** 01-foundation-core-architecture
**Plan:** 05
**Wave:** 3
**Status:** Complete (ad-hoc signed build verified)
**Date:** 2025-07-13

## What Was Built

Created macOS app bundle (.app) and DMG installer configuration using pyappdist with code signing and Hardened Runtime support.

### Configuration

- **pyproject.toml** (`tool.pyappdist` section):
  - App name: "HousePhotoMapper"
  - Python: 3.12
  - macOS deployment target: 10.14
  - Identifier: com.housephotomapper.HousePhotoMapper
  - Launcher: house_photo_mapper.__main__:main (GUI mode)
  - Icon: resources/icons/app_1024.png
  - Two targets:
    - macos-arm64-app: .app bundle format (macapp)
    - macos-arm64-dmg: DMG installer with notarization support

- **resources/entitlements.plist**: Hardened Runtime entitlements
  - com.apple.security.cs.allow-jit
  - com.apple.security.cs.allow-unsigned-executable-memory
  - com.apple.security.cs.disable-library-validation
  - com.apple.security.files.user-selected.read-write
  - com.apple.security.network.client

- **resources/icons/app.icns**: macOS app icon (generated from 1024x1024 PNG)

- **scripts/build_dmg.sh**: Build script for CI/local builds
  - Validates CODESIGN_IDENTITY and NOTARY_PROFILE environment variables
  - Runs pyappdist build for macos-arm64-dmg

### Platform Utilities

- **src/house_photo_mapper/infrastructure/platform.py**:
  - is_macos(), is_apple_silicon() - platform detection
  - get_app_version() - returns version from package
  - set_dock_icon() - sets Dock icon on macOS
  - get_app_data_dir() - cross-platform app data directory
  - open_file_externally() - opens files with default system app

### Build Verification

The .app bundle was successfully built with ad-hoc signing:

```
OK [macos-arm64-app]: 1 .app -> /Users/sorin/src/my/house-photo-mapper/appdist/macos-arm64-app/dist
```

The app launches successfully on Apple Silicon (verified by running the binary).

## Requirements Satisfied

- CP-01: macOS app bundle foundation established
- Hardened Runtime entitlements configured
- Code signing infrastructure ready (uses CODESIGN_IDENTITY env var)
- Notarization infrastructure ready (uses NOTARY_PROFILE env var)

## Files Created/Modified

### New Files
- resources/icons/app_1024.png (1024x1024 source icon)
- resources/icons/app.icns (macOS icon bundle)
- resources/icons/app.iconset/ (iconset source)
- resources/entitlements.plist (Hardened Runtime entitlements)
- scripts/build_dmg.sh (DMG build script)
- src/house_photo_mapper/infrastructure/platform.py (platform utilities)

### Modified Files
- pyproject.toml (added tool.pyappdist configuration)
- src/house_photo_mapper/infrastructure/__init__.py (export platform functions)
- src/house_photo_mapper/domain/services/coordinate.py (added ViewportContext)
- src/house_photo_mapper/domain/services/__init__.py (export ViewportContext)

## Verification Commands

```bash
# Build .app bundle (ad-hoc signing)
uv run pyappdist build macos-arm64-app

# Verify app launches
./appdist/macos-arm64-app/dist/HousePhotoMapper.app/Contents/MacOS/house-photo-mapper

# Build DMG (requires Developer ID)
export CODESIGN_IDENTITY="Developer ID Application: Your Name (TEAMID)"
export NOTARY_PROFILE="notary-profile"
./scripts/build_dmg.sh

# Verify codesign (after proper signing)
codesign --verify --deep --strict --verbose=2 dist/HousePhotoMapper.app
spctl --assess --type execute --verbose dist/HousePhotoMapper.app
```

## Notes for Distribution

To create a distributable notarized DMG:
1. Obtain Apple Developer ID Application certificate
2. Add certificate to keychain
3. Create notarytool profile: `xcrun notarytool store-credentials notary-profile --apple-id "..." --team-id "..." --password "..."`
4. Set environment variables:
   - `CODESIGN_IDENTITY="Developer ID Application: Your Name (TEAMID)"`
   - `NOTARY_PROFILE="notary-profile"`
5. Run `./scripts/build_dmg.sh`