#!usr/bin/env python
# -*- coding: utf-8 -*-

'''
Author:Andra Waagmeester (andra@waagmeester.net)

This file is part of ProteinBoxBot.

ProteinBoxBot is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

ProteinBoxBot is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with ProteinBoxBot.  If not, see <http://www.gnu.org/licenses/>.
'''
# Load the path to the PBB_Core library
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../ProteinBoxBot_Core")
import PBB_Core
import PBB_Debug
import PBB_Functions
import PBB_login
import PBB_settings

# Resource specific 
import gene

import traceback
from datetime import date, datetime, timedelta


try:

    speciesInfo = dict()
    speciesInfo["human"] = dict()
    speciesInfo["mouse"] = dict()
    speciesInfo["rat"] = dict()
    
    speciesInfo["human"]["taxid"] = "9606"
    speciesInfo["human"]["wdid"] = "Q5"
    speciesInfo["human"]["name"] = "human"
    speciesInfo["human"]["release"] = "Q20950174"
    speciesInfo["human"]["genome_assembly"] = "Q20966585"
    
    speciesInfo["mouse"]["taxid"] = "10090"
    speciesInfo["mouse"]["wdid"] = "Q83310"
    speciesInfo["mouse"]["name"] = "mouse"
    speciesInfo["mouse"]["release"] = "Q20973051"
    speciesInfo["mouse"]["genome_assembly"] = "Q20973075"
    
    speciesInfo["rat"]["taxid"] = "10114"
    speciesInfo["rat"]["wdid"] = "Q36396"
    speciesInfo["rat"]["name"] = "rat"
    speciesInfo["rat"]["release"] = "Q19296606"
    
    if len(sys.argv) == 1:
        print("Please provide one of the following species as argument: "+ str(speciesInfo.keys()))
        print("Example: python ProteinBoxBot_EntrezGene.py human")
        sys.exit()
    else:
        if not sys.argv[1] in speciesInfo.keys():
            print(sys.argv[1] + " is not (yet) supported.")
            sys.exit()
    
    genome = gene.genome(speciesInfo[sys.argv[1]])
    
      
except (Exception):
    print(traceback.format_exc())
    # client.captureException()  