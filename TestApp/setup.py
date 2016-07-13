from setuptools import setup

PLIST = dict(
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

DATAFILES = [
        "Resources/English.lproj",
        ]

OPTIONS = {
    'plist': PLIST,
   }

setup(
    app = ["DefconAppKitTest.py"],
    name = "DefconAppKit Test",
    options = {'py2app': OPTIONS},
    setup_requires = ['py2app'],
    data_files = DATAFILES,
    )
