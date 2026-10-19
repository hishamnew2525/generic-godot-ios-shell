# Generic Godot iOS shell — unexecuted draft

Tiny synthetic project for a separately authorised public standard-runner build. No build has been executed as part of this draft's preparation. Proposed repository name: generic-godot-ios-shell. No repository has been created.

Manual workflow only, macos-26 standard runner, Xcode26.6, Godot4.7.2 standard templates, device ARM64 Release, signing disabled. No Actions artifacts, cache, Packages, LFS, Pages, custom runner image, paid larger runner or AI feature is used. Downloads are official public dependencies. A successful later job publishes exactly three files to GitHub Releases: GenericGodotIOS-unsigned.zip, BUILD-INFO.json and SHA256SUMS. Failed build logs remain in Actions; there is no automatic retry or fallback to paid services.

The project-only export avoids Godot's automatic archive/provisioning path. An explicit unsigned xcodebuild links the app. Generated output, actual native version/architecture, pack slot and release publication are unverified until a separately approved run. Do not increase any budget or add a payment method if GitHub blocks a run.

The intended app/executable is GenericGodotIOS. Its main resource slot is GenericGodotIOS.pck in GenericGodotIOS.app. A later separately approved local assembly may copy a compatible local main pack under that filename without altering the original pack. No private pack or source ever belongs in this repository or a release.

Everything in this repository, its history and release outputs is publicly copyable, including its account association, commit author metadata, run IDs, build logs and dependency versions. Never initialise it from an existing private project's checkout or history. Use the exact reviewed public file manifest. No Apple account, private token, key, certificate, receipt or proprietary asset is required.

The automatic job token needs contents:write ONLY for this separate repository to create the generic release/tag/assets. No personal access token or Apple credentials. Existing account and repository Actions policies may still block dispatch or release permissions; stop and report rather than changing account controls.

The placeholder source/build helpers are offered under LICENSE. Preserve the official engine's LICENSE.txt, COPYRIGHT.txt and AUTHORS.md notices included in a later app's Notices directory, plus the pinned MoltenVK and SPIRV-Cross licence/copyright documentation. These notices do not grant rights to unrelated private data. Public publication and workflow execution both require separate human authorisation before use.
