from distutils.core import setup
import py2app
import os
import sys

plist = dict(
        CFBundleDocumentTypes = [
        dict(
            CFBundleTypeExtensions = ["ufo"],
            CFBundleTypeName = "Unified Font Object",
            CFBundleTypeRole = "Viewer",
            NSDocumentClass = "DefconAppKitTestDocument",
            LSTypeIsPackage = False,
        ),
    ],
    CFBundleIdentifier = "com.typesupply.DefconAppKitTest",
    LSMinimumSystemVersion = "10.4.0",
    CFBundleShortVersionString = "1.0.0",
    CFBundleVersion = "1.0.0a1",
    NSHumanReadableCopyright = "Copyright 2007 Tal Leming. All rights reserved."
    )

dataFiles = [
        "Resources/English.lproj",
        ]
frameworks = []
if "-A" not in sys.argv:
    dataFiles += frameworks

setup(
    data_files=dataFiles,
    app=[dict(script="DefconAppKitTest.py", plist=plist)]
    )
