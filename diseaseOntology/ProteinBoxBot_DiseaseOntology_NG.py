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
sys.path.append("/Users/andra/wikidatabots/ProteinBoxBot_Core")
import PBB_Core
import PBB_Functions
import PBB_login
import PBB_settings
from raven import Client
import traceback

# Login to WikiData
login_values = PBB_login.login(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())

# Login to getSentry service
# client = Client(PBB_settings.getSentryKey())

try:
    # Get all WikiData entries that contain a WikiData ID
    DoInWikiData = PBB_Functions.getItemsByProperty("699")['items']
    print DoInWikiData
except Exception, err:
    print traceback.format_exc()
    # client.captureException()