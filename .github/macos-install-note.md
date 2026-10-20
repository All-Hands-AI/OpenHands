<!-- macos-install-note -->
### macOS install note

The macOS app is not yet signed with an Apple Developer ID, so after you drag
**OpenHands Agent Canvas** to your Applications folder macOS may report it as
*"damaged and can't be opened."* This is Gatekeeper quarantining an unsigned
download, not a corrupt file. Clear the quarantine flag once in Terminal, then
open the app normally:

```sh
xattr -dr com.apple.quarantine "/Applications/OpenHands Agent Canvas.app"
```

A signed and notarized build is tracked in
https://github.com/OpenHands/OpenHands/issues/16774.
