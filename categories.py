# -*- coding: utf-8 -*-
import re
import util
import main

ANNOTATION_CATS = re.compile("\, ").split(
    "LVC, ID, IPronV, IPrepV, VPC, OTH"
)

#"LVC, ID, IPronV, IPrepV, VPC, OTH, LVC/ID, LVC/IPronV, LVC/IPrepV, LVC/VPC, LVC/OTH, LVC/_, ID/IPronV, ID/IPrepV, ID/VPC, ID/OTH, ID/_, IPronV/IPrepV, IPronV/VPC, IPronV/OTH, IPronV/_, IPrepV/VPC, IPrepV/OTH, IPrepV/_, VPC/OTH, VPC/_, OTH/_"

#ANNOTATION_CATS_3PL = util.makeArray2D(ANNOTATION_CATS, 3)

#ANNOTATION_CATS_SPLIT_ON_CHAR = util.segmentArrayOnMaxChars(ANNOTATION_CATS, main.MAX_CHARS_BUTTON_LINE)
