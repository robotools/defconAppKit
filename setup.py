#!/usr/bin/env python

import sys
from distutils.core import setup

try:
    import fontTools
except:
    print "*** Warning: defcon requires FontTools, see:"
    print "    fonttools.sf.net"

try:
    import robofab
except:
    print "*** Warning: defcon requires RoboFab, see:"
    print "    robofab.com"

#if "sdist" in sys.argv:
#    import os
#    import subprocess
#    import shutil
#    docFolder = os.path.join(os.getcwd(), "documentation")
#    # remove existing
#    doctrees = os.path.join(docFolder, "build", "doctrees")
#    if os.path.exists(doctrees):
#        shutil.rmtree(doctrees)
#    # compile
#    p = subprocess.Popen(["make", "html"], cwd=docFolder)
#    p.wait()
#    # remove doctrees
#    shutil.rmtree(doctrees)



setup(name="defconAppKit",
    version="0.1",
    description="A set of interface objects for working with font data.",
    author="Tal Leming",
    author_email="tal@typesupply.com",
    url="http://code.typesupply.com",
    license="MIT",
    packages=[
        "defconAppKit",
        "defconAppKit.controls",
        "defconAppKit.representationFactories",
        "defconAppKit.tools",
        "defconAppKit.windows"
    ],
    package_dir={"":"Lib"}
)