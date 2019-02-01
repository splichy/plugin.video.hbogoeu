# -*- coding: utf-8 -*-

import base64
import json
import sys
import urllib

import inputstreamhelper
import requests
import urllib2
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
from urlparse import parse_qsl
import hashlib
import pickle
import time

__addon_id__ = 'plugin.video.hbogoeu'
__Addon = xbmcaddon.Addon(__addon_id__)
__settings__ = xbmcaddon.Addon(id=__addon_id__)
__language__ = __settings__.getLocalizedString

__addonurl__ = sys.argv[0]
__handle__ = int(sys.argv[1])

DEBUG_ID_STRING = "["+str(__addon_id__)+"] "
SESSION_VALIDITY = 2  # stored session valid for 2 hours

UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'  # CHROME ON LINUX

GO_SW_VERSION = '4.7.4'
GO_REQUIRED_PLATFORM = 'CHBR'  # emulate chrome

md = xbmc.translatePath(__Addon.getAddonInfo('path') + "/resources/media/")
search_string = urllib.unquote_plus(__settings__.getSetting('lastsearch'))

# LABELS

LB_SEARCH_DESC = __language__(33700).encode('utf-8')
LB_SEARCH_NORES = __language__(33701).encode('utf-8')
LB_ERROR = __language__(33702).encode('utf-8')
LB_EPISODE_UNTILL = __language__(33703).encode('utf-8')
LB_FILM_UNTILL = __language__(33704).encode('utf-8')
LB_EPISODE = __language__(33705).encode('utf-8')
LB_SEASON = __language__(33706).encode('utf-8')
LB_MYPLAYLIST = __language__(33707).encode('utf-8')
LB_NOLOGIN = __language__(33708).encode('utf-8')
LB_LOGIN_ERROR = __language__(33709).encode('utf-8')
LB_NO_OPERATOR = __language__(33710).encode('utf-8')
LB_SEARCH = __language__(33711).encode('utf-8')

force_original_names = __settings__.getSetting('origtitles')
if force_original_names == "true":
    force_original_names = True
else:
    force_original_names = False

force_scraper_names = __settings__.getSetting('forcescrap')
if force_scraper_names == "true":
    force_scraper_names = True
else:
    force_scraper_names = False

operator = __settings__.getSetting('operator')
if operator == 'N/A':
    xbmcgui.Dialog().ok(LB_ERROR, LB_NO_OPERATOR)
    xbmcaddon.Addon(id='plugin.video.hbogoeu').openSettings()
    sys.exit()
# 'operator SETTING_ID - > operator hash ID, short country code, long country code, default language, country hash ID,web true/false
xbmc.log(DEBUG_ID_STRING+"OPERATOR SETTING_ID: " + operator)

op_ids = {
   'N/A': ['00000000-0000-0000-0000-000000000000', 'hr', 'hr', 'HRV', 'ENG', True, ''],
   'WEB REGISTRATION: HBO Bosnia and Herzegovina': ['6e0fe238-3b45-4049-9206-fb46425c486f', 'ba', 'ba', 'BIH', 'HRV', True, ''],
   'WEB REGISTRATION: HBO Bulgaria': ['b52fda48-25b2-4623-af6b-e8e30ae7d645', 'bg', 'bg', 'BGR', 'BUL', True, ''],
   'WEB REGISTRATION: HBO Croatia': ['24a5e09c-4550-4cd3-a63c-8f6ab0508dd7', 'hr', 'hr', 'HRV', 'HRV', True, ''],
   'WEB REGISTRATION: HBO Czech Republic': ['e04b20c2-be50-4b65-9b77-9e17e854de32', 'cz', 'cz', 'CZE', 'CES', True, ''],
   'WEB REGISTRATION: HBO Hungary': ['15276cb7-7f53-432a-8ed5-a32038614bbf', 'hu', 'hu', 'HUN', 'HUN', True, ''],
   'WEB REGISTRATION: HBO Macedonia': ['9b09ff6b-d2a8-48a5-84c3-31bf52add9ff', 'mk', 'mk', 'MKD', 'MKD', True, ''],
   'WEB REGISTRATION: HBO Montenegro': ['54d370dd-2e28-4661-9ad4-c919b88aac4d', 'me', 'me', 'MNE', 'SRP', True, ''],
   'WEB REGISTRATION: HBO Poland': ['dbaf3435-6ee2-4a79-af13-dac5a1c550a3', 'pl', 'pl', 'POL', 'POL', True, ''],
   'WEB REGISTRATION: HBO Romania': ['febb7b91-f968-4a6b-8592-564f0207ab2d', 'ro', 'ro', 'ROU', 'RON', True, ''],
   'WEB REGISTRATION: HBO Serbia': ['3782faaf-a461-4a4f-95ea-9b2fbcbf1958', 'rs', 'sr', 'SRB', 'SRP', True, ''],
   'WEB REGISTRATION: HBO Slovakia': ['55f359e0-6038-4653-a7db-e2101da2b7a8', 'sk', 'sk', 'SVK', 'SLO', True, ''],
   'WEB REGISTRATION: HBO Slovenia': ['e5ca4913-c5b8-4b08-96a3-b71abafb08aa', 'si', 'si', 'SVN', 'SLV', True, ''],
   'Bosnia and Herzegovina: HBO Development Bosnia': ['b461cb49-d6ad-4375-ae8b-f8dc1a97d027', 'ba', 'ba', 'BIH', 'HRV', False, ''],
   'Bosnia and Herzegovina: HBO GO VIP/Club Bosnia': ['926d5484-bf6f-4b2b-b20b-8f40b71f8c9a', 'ba', 'ba', 'BIH', 'HRV', False, ''],
   'Bosnia and Herzegovina: Telemach': ['ad36b8ac-7cd0-4f28-a57b-1ad0f44a5ec3', 'ba', 'ba', 'BIH', 'HRV', False, ''],
   'Bosnia and Herzegovina: Telrad Net': ['33b6e3da-83f7-438e-be0c-7a1fa6ea6197', 'ba', 'ba', 'BIH', 'HRV', False, ''],
   'Bulgaria: A1': ['29c994ca-48bc-4b19-a0e7-44a25b51b241', 'bg', 'bg', 'BGR', 'BUL', False, ''],
   'Bulgaria: M SAT CABLE EAD': ['c5afc2d3-e50d-4ddf-bd66-d1c256cca142', 'bg', 'bg', 'BGR', 'BUL', False, ''],
   'Bulgaria: N3': ['0b17bfc7-c6a3-457f-b3fa-76547606799f', 'bg', 'bg', 'BGR', 'BUL', False, ''],
   'Bulgaria: NET1': ['63cc0033-1f0d-40ad-bdca-d074dbac5e73', 'bg', 'bg', 'BGR', 'BUL', False, ''],
   'Bulgaria: NetSurf': ['553c40d9-cf30-4a47-9051-cc7ac832e124', 'bg', 'bg', 'BGR', 'BUL', False, ''],
   'Bulgaria: NetWorx': ['105cc484-80a2-4710-9b1c-6f73107bf58b', 'bg', 'bg', 'BGR', 'BUL', False, ''],
   'Bulgaria: Silistra TV - Силистра ТВ': ['e8382e76-c870-4023-b099-4a9e5497175f', 'bg', 'bg', 'BGR', 'BUL', False, ''],
   'Bulgaria: Telekabel': ['4381c076-4942-43d2-8aa0-a1ab919aaf89', 'bg', 'bg', 'BGR', 'BUL', False, ''],
   'Bulgaria: Telenor': ['8d9d817a-aea5-4d9c-bf32-07ba91d66560', 'bg', 'bg', 'BGR', 'BUL', False, ''],
   'Bulgaria: Telenor Promo': ['7d1d3d8a-f052-402a-a964-415da5da6aec', 'bg', 'bg', 'BGR', 'BUL', False, ''],
   'Bulgaria: Vivacom': ['60d4a508-dcc8-4d49-aacd-af9f4dc82a99', 'bg', 'bg', 'BGR', 'BUL', False, ''],
   'Croatia: A1': ['e1fb87d0-7581-4671-94bb-8e647e13385a', 'hr', 'hr', 'HRV', 'HRV', False, ''],
   'Croatia: bonbon': ['81a65859-145b-4bbc-afa6-04e9ade004f9', 'hr', 'hr', 'HRV', 'HRV', False, ''],
   'Croatia: evotv': ['beed025d-06c9-4cac-a8a4-a118bdf22861', 'hr', 'hr', 'HRV', 'HRV', False, ''],
   'Croatia: HBO GO Vip/Club Croatia': ['323f061a-34e9-4453-987b-99aa38c46480', 'hr', 'hr', 'HRV', 'HRV', False, ''],
   'Croatia: Hrvatski Telekom d.d.': ['73893614-eae3-4435-ab53-1d46c7f90498', 'hr', 'hr', 'HRV', 'HRV', False, ''],
   'Croatia: Iskon Internet d.d.': ['5bff83d2-9163-4d85-9ae1-b6c2a6eabf71', 'hr', 'hr', 'HRV', 'HRV', False, ''],
   'Croatia: Optima Telekom d.d.': ['a9e06fc5-c8d3-4b79-a776-b78d86729843', 'hr', 'hr', 'HRV', 'HRV', False, ''],
   'Croatia: Simpa': ['3a1bb01c-9f7b-4029-a98d-6d17708fa4db', 'hr', 'hr', 'HRV', 'HRV', False, ''],
   'Czech Republic: freeSAT Česká republika': ['f8e915f5-4641-47b1-a585-d93f61bbbfd3', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: Skylink': ['c55e69f0-2471-46a9-a8b7-24dac54e6eb9', 'cz', 'cz', 'CZE', 'CES', False, 'https://czapi.hbogo.eu/oauthskylink/protocolgateway.aspx?caller={caller}&cid={cid}&oid=c55e69f0-2471-46a9-a8b7-24dac54e6eb9&platform=COMP&backuri={backuri}'],
   'Czech Republic: UPC CZ': ['f0e09ddb-1286-4ade-bb30-99bf1ade7cff', 'cz', 'cz', 'CZE', 'CES', False, 'https://czapi.hbogo.eu/oauthupc/protocolgateway.aspx?caller={caller}&cid={cid}&oid=f0e09ddb-1286-4ade-bb30-99bf1ade7cff&platform=COMP&backuri={backuri}'],
   'Czech Republic: Slovak Telekom': ['3a2f741b-bcbc-455f-b5f8-cfc55fc910a3', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: Lepší.TV': ['5696ea41-2087-46f9-9f69-874f407f8103', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: O2': ['b8a2181d-b70a-49a7-b823-105c995199a2', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: RIO Media': ['a72f9a11-edc8-4c0e-84d4-17247c1111f5', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: UPC BROADBAND SLOVAKIA': ['249309a7-6e61-436d-aa12-eeaddcfeb72e', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: AIM': ['cdb7396a-bd2c-45e9-a023-71441e8dae64', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: T-Mobile Czech Republic a.s.': ['ac49b07c-4605-409c-83bd-16b5404b16a7', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: Antik Telecom': ['ad5a1855-1abd-4aa5-a947-f9942a08ca75', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: CentroNet, a. s.': ['80c3f17b-718c-4f1b-9a58-67b5ac13b6fd', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: DIGI CZ s. r. o.': ['b132e3a1-ea76-4659-8656-1aac32bccd56', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: DIGI SLOVAKIA s.r.o.': ['cd2b4592-90be-4ad7-96a0-54e34ee74866', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: FixPro': ['6c9e2104-83dc-48fb-a44c-ee3b8d689005', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: flexiTV': ['1bfb5785-446d-4ca7-b7a4-cc76f48c97fe', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: freeSAT Slovensko': ['b3ce9ab2-af8f-4e02-8ab7-9a01d587a35f', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: GRAPE SC': ['25e0270f-ae80-49b1-9a20-bfa47b7690e1', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: HD Kabel': ['82811c4a-ad87-4bda-a1bd-2f4a4215eac4', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: Kuki': ['aa2a90c0-292c-444e-a069-1ae961fa59f7', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: MARTICO': ['95a5f7c8-95b7-4978-8fff-abe023249196', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: Nej.cz': ['6925e9ca-9d97-446c-b3c2-09971f441f2a', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: NETBOX': ['a2edba6f-bffb-4efe-bb7a-3b51e2fc0573', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: Satro': ['939ffed6-d015-427e-a2f7-a82d1b846eb7', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: SATT': ['064a6c6a-0556-4ff1-8d4d-c8cf3141131a', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: SELFNET': ['c2c2fdb7-8562-4b16-a09c-f7530ce2ce78', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: sledovanitv.cz s.r.o.': ['980a4419-1336-4056-a561-268afe7907f3', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: Slovanet a.s.': ['8a312c76-9e9c-42e4-b38c-c0adbd6c6a93', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: SWAN, a. s.': ['5b8544f8-784a-473b-97ad-159a2f95d0fb', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: Tesatel': ['69253de6-3935-4c48-9557-5a1e930f30de', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: HBO GO special': ['b59ee559-45b9-46a0-a40c-7f41ab6e53e9', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: HBO GO Vip/Club Czech Republic': ['a215610d-aecb-4357-934f-403813a7566c', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: HBO Development Czech': ['ad729e98-c792-4bce-9588-106f11ce3b90', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Czech Republic: HBO GO VIP/Club Slovakia': ['2e61999a-1b77-4ed2-b531-081dfdd3bee0', 'cz', 'cz', 'CZE', 'CES', False, ''],
   'Hungary: DIGI': ['b7728684-13d5-46d9-a9a4-97d676cdaeec', 'hu', 'hu', 'HUN', 'HUN', False, ''],
   'Hungary: Magyar Telekom Nyrt.': ['04459649-8a90-46f1-9390-0cd5b1958a5d', 'hu', 'hu', 'HUN', 'HUN', False, ''],
   'Hungary: Telenor MyTV': ['e71fabae-66b6-4972-9823-8743f8fcf06f', 'hu', 'hu', 'HUN', 'HUN', False, ''],
   'Hungary: UPC Direct': ['48f48c5b-e9e4-4fca-833b-2fa26fb1ad22', 'hu', 'hu', 'HUN', 'HUN', False, ''],
   'Hungary: UPC Magyarország': ['1ca45800-464a-4e9c-8f15-8d822ad7d8a1', 'hu', 'hu', 'HUN', 'HUN', False, ''],
   'Hungary: INVITEL': ['f2230905-8e25-4245-80f9-fccf67a24005', 'hu', 'hu', 'HUN', 'HUN', False, ''],
   'Hungary: Celldömölki Kábeltelevízió Kft.': ['383cd446-06fb-4a59-8d39-200a3e9bcf6f', 'hu', 'hu', 'HUN', 'HUN', False, ''],
   'Hungary: Eurocable – Hello Digital': ['fe106c75-293b-42e6-b211-c7446835b548', 'hu', 'hu', 'HUN', 'HUN', False, ''],
   'Hungary: Flip': ['1680a41e-a9bc-499f-aca6-db1a59703566', 'hu', 'hu', 'HUN', 'HUN', False, ''],
   'Hungary: HFC-Network Kft.': ['42677aa5-7576-4dc7-9004-347b279e4e5d', 'hu', 'hu', 'HUN', 'HUN', False, ''],
   'Hungary: HIR-SAT 2000 Kft.': ['3a3cce31-fb19-470a-9bb5-6947c4ac9996', 'hu', 'hu', 'HUN', 'HUN', False, ''],
   'Hungary: JuPiNet': ['93bdad56-6fc7-4494-be0f-3660ce3752f0', 'hu', 'hu', 'HUN', 'HUN', False, ''],
   'Hungary: Kabelszat 2002': ['d91341c2-3542-40d4-adab-40b644798327', 'hu', 'hu', 'HUN', 'HUN', False, ''],
   'Hungary: Klapka Lakásszövetkezet': ['18fb0ff5-9cfa-4042-be00-638c5d34e553', 'hu', 'hu', 'HUN', 'HUN', False, ''],
   'Hungary: Lát-Sat Kft.': ['97cddb59-79e3-4090-be03-89a6ae06f5ec', 'hu', 'hu', 'HUN', 'HUN', False, ''],
   'Hungary: Micro-Wave kft.': ['c071ab5e-8884-434a-9702-084882c2b541', 'hu', 'hu', 'HUN', 'HUN', False, ''],
   'Hungary: MinDig TV Extra': ['c48c350f-a9db-4eb6-97a6-9b659e2db47f', 'hu', 'hu', 'HUN', 'HUN', False, ''],
   'Hungary: PARISAT': ['7982d5c7-63df-431d-806e-54f98fdfa36a', 'hu', 'hu', 'HUN', 'HUN', False, ''],
   'Hungary: PR-TELECOM': ['18f536a3-ecac-42f1-91f1-2bbc3e6cfe81', 'hu', 'hu', 'HUN', 'HUN', False, ''],
   'Hungary: TARR Kft': ['adb99277-3899-439e-8bdf-c749c90493cd', 'hu', 'hu', 'HUN', 'HUN', False, ''],
   'Hungary: Vác Városi Kábeltelevízió Kft.': ['5729f013-f01d-4cc3-b048-fe5c91c64296', 'hu', 'hu', 'HUN', 'HUN', False, ''],
   'Hungary: Vidanet Zrt.': ['b4f422f7-5424-4116-b72d-7cede85ead4e', 'hu', 'hu', 'HUN', 'HUN', False, ''],
   'Hungary: HBO Development Hungary': ['6a52efe0-54c4-4197-8c55-86ee7a63cd04', 'hu', 'hu', 'HUN', 'HUN', False, ''],
   'Hungary: HBO GO Vip/Club Hungary': ['f320aa2c-e40e-49c2-8cdd-1ebef2ac6f26', 'hu', 'hu', 'HUN', 'HUN', False, ''],
   'Macedonia: HBO GO Vip/Club Macedonia': ['b848c6b6-31f1-467d-9814-0011252b4b32', 'mk', 'mk', 'MKD', 'MKD', False, ''],
   'Macedonia: Македонски Телеком': ['f4c9c5de-4c4b-42f4-8355-fd43bf6df571', 'mk', 'mk', 'MKD', 'MKD', False, ''],
   'Macedonia: оне.Вип': ['2cda834c-24ef-4b21-abff-94379f770877', 'mk', 'mk', 'MKD', 'MKD', False, ''],
   'Montenegro: Crnogorski Telekom': ['849f94ec-96be-4520-8c0d-b0d7aadd278b', 'me', 'me', 'MNE', 'SRP', False, ''],
   'Montenegro: HBO GO VIP/Club Montenegro': ['dcda4868-9de9-4be2-8822-1eb510af61d8', 'me', 'me', 'MNE', 'SRP', False, ''],
   'Montenegro: Telemach': ['c1932a89-2060-4c00-8567-9c96e8217491', 'me', 'me', 'MNE', 'SRP', False, ''],
   'Montenegro: Telenor': ['e52cea52-eb14-4bed-b746-eced9a1d2b7b', 'me', 'me', 'MNE', 'SRP', False, ''],
   'Polonia: Cyfrowy Polsat': ['414847a0-635c-4587-8076-079e3aa96035', 'pl', 'pl', 'POL', 'POL', False, 'https://cyfrowyauth.hbogo.eu/oauth/protocolgateway.aspx?caller={caller}&cid={cid}&oid=414847a0-635c-4587-8076-079e3aa96035&platform=COMP&backuri={backuri}'],
   'Polonia: nc+': ['07b113ce-1c12-4bfd-9823-db951a6b4e87', 'pl', 'pl', 'POL', 'POL', False, ''],
   'Polonia: Plus': ['a35f8cd2-05d7-4c0f-832f-0ddfad3b585d', 'pl', 'pl', 'POL', 'POL', False, ''],
   'Polonia: UPC': ['c5ff7517-8ef8-4346-86c7-0fb328848671', 'pl', 'pl', 'POL', 'POL', False, ''],
   'Polonia: Vectra': ['7021fee7-bab1-4b4b-b91c-a2dc4fdd7a05', 'pl', 'pl', 'POL', 'POL', False, ''],
   'Polonia: PLAY': ['22eaaeb6-1575-419f-9f1b-af797e86b9ee', 'pl', 'pl', 'POL', 'POL', False, ''],
   'Polonia: Multimedia Polska': ['598a984f-bc08-4e77-896b-a82d8d6ea8de', 'pl', 'pl', 'POL', 'POL', False, ''],
   'Polonia: Netia': ['c454b13c-5c82-4a01-854f-c34b2901d1b2', 'pl', 'pl', 'POL', 'POL', False, ''],
   'Polonia: Orange': ['48b81f9b-cb72-48cd-85d2-e952f78137c0', 'pl', 'pl', 'POL', 'POL', False, ''],
   'Polonia: INEA': ['82ae5dfd-9d29-4059-a843-2aa16449c42a', 'pl', 'pl', 'POL', 'POL', False, ''],
   'Polonia: TOYA': ['357890f0-2698-445b-8712-b82f715b0648', 'pl', 'pl', 'POL', 'POL', False, ''],
   'Polonia: JAMBOX': ['5eb57ea8-9cd7-4bbf-8c6c-e56b186dd5c0', 'pl', 'pl', 'POL', 'POL', False, ''],
   'Polonia: PROMAX': ['2e0325fa-d4b3-41eb-a9e4-0a36ee59aec5', 'pl', 'pl', 'POL', 'POL', False, ''],
   'Polonia: Asta-Net': ['892771be-a48c-46ab-a0d0-3f51cdc50cf2', 'pl', 'pl', 'POL', 'POL', False, ''],
   'Polonia: TK Chopin': ['6a47f04f-cdd6-428b-abb5-135e38a43b38', 'pl', 'pl', 'POL', 'POL', False, ''],
   'Polonia: ELSAT': ['36f365ac-4ca2-4e8b-9b21-14479e5fe6bb', 'pl', 'pl', 'POL', 'POL', False, ''],
   'Polonia: Eltronik': ['99eed640-107c-4732-81d0-59305ff6b520', 'pl', 'pl', 'POL', 'POL', False, ''],
   'Polonia: SatFilm': ['f7f4d300-23ab-4b79-bb35-49568eb7cd4a', 'pl', 'pl', 'POL', 'POL', False, ''],
   'Polonia: Master': ['5893f3c1-0bcd-4ae3-b434-45666925b5d1', 'pl', 'pl', 'POL', 'POL', False, ''],
   'Polonia: STANSAT': ['8f34fcd8-3b74-4c16-b91c-c8375ab3ffdb', 'pl', 'pl', 'POL', 'POL', False, ''],
   'Polonia: Dialog': ['878e69aa-be98-4a7d-a08e-b11c7330d8b3', 'pl', 'pl', 'POL', 'POL', False, ''],
   'Polonia: Internetia': ['b49a6c5d-033d-4bf1-b273-37ba188aef97', 'pl', 'pl', 'POL', 'POL', False, ''],
   'Polonia: Petrotel': ['62f7b31b-c866-4ff3-a7a1-800fac10de16', 'pl', 'pl', 'POL', 'POL', False, ''],
   'Polonia: Cinema City – promocja': ['1366289b-86ae-4695-8d4b-a6b14eacdd8b', 'pl', 'pl', 'POL', 'POL', False, ''],
   'Polonia: Samsung - promocja': ['64d88671-b490-44b9-b1ee-e145347732b3', 'pl', 'pl', 'POL', 'POL', False, ''],
   'Polonia: Player+': ['57332e2f-958c-4a83-86cc-e569842868a2', 'pl', 'pl', 'POL', 'POL', False, ''],
   'Polonia: Test operator': ['ec6276ae-2246-41c1-b0a9-ed06daa385ce', 'pl', 'pl', 'POL', 'POL', False, ''],
   'Polonia: HBO GO Vip/Club Poland': ['b7018ed3-1858-4436-8e7f-d92a6d0b9bfc', 'pl', 'pl', 'POL', 'POL', False, ''],
   'Romania: AKTA': ['defb1446-0d52-454c-8c86-e03715f723a8', 'ro', 'ro', 'ROU', 'RON', False, ''],
   'Romania: Canal S': ['381ba411-3927-4616-9c6a-b247d3ce55e8', 'ro', 'ro', 'ROU', 'RON', False, ''],
   'Romania: HBO GO Vip/Club Romania': ['4949006b-8112-4c09-87ad-18d6f7bfee02', 'ro', 'ro', 'ROU', 'RON', False, ''],
   'Romania: INES': ['0539b12f-670e-49ff-9b09-9cef382e4dae', 'ro', 'ro', 'ROU', 'RON', False, ''],
   'Romania: INTERSAT': ['078a922e-df7c-4f34-a8de-842dea7f4342', 'ro', 'ro', 'ROU', 'RON', False, ''],
   'Romania: Metropolitan': ['cb71c5a8-9f21-427a-a37e-f08abf9605be', 'ro', 'ro', 'ROU', 'RON', False, ''],
   'Romania: MITnet': ['959cf6b2-34b1-426d-9d51-adf04c0802b0', 'ro', 'ro', 'ROU', 'RON', False, ''],
   'Romania: NextGen Communications': ['cf66ff47-0568-485f-902d-0accc1547ced', 'ro', 'ro', 'ROU', 'RON', False, ''],
   'Romania: Orange Romania': ['754751b7-1406-416e-b4bd-cb6566656de2', 'ro', 'ro', 'ROU', 'RON', False, ''],
   'Romania: RCS RDS': ['c243a2f3-d54e-4365-85ad-849b6908d53e', 'ro', 'ro', 'ROU', 'RON', False, ''],
   'Romania: Telekom Romania': ['972706fe-094c-4ea5-ae98-e8c5d907f6a2', 'ro', 'ro', 'ROU', 'RON', False, 'https://roapi.hbogo.eu/oauthromtelekom/protocolgateway.aspx?caller={caller}&cid={cid}&oid=972706fe-094c-4ea5-ae98-e8c5d907f6a2&platform=COMP&backuri={backuri}'],
   'Romania: Telekom Romania Business': ['6baa4a6e-d707-42b2-9a79-8b475c125d86', 'ro', 'ro', 'ROU', 'RON', False, ''],
   'Romania: TV SAT 2002': ['d68c2237-1f3f-457e-a708-e8e200173b8d', 'ro', 'ro', 'ROU', 'RON', False, ''],
   'Romania: UPC Romania': ['41a660dc-ee15-4125-8e92-cdb8c2602c5d', 'ro', 'ro', 'ROU', 'RON', False, 'https://roapi.hbogo.eu/oauthupcrom/protocolgateway.aspx?caller={caller}&cid={cid}&oid=41a660dc-ee15-4125-8e92-cdb8c2602c5d&platform=COMP&backuri={backuri}'],
   'Romania: Vodafone': ['92e30168-4ca6-4512-967d-b79e584a22b6', 'ro', 'ro', 'ROU', 'RON', False, ''],
   'Romania: Vodafone Romania 4GTV+': ['6826b525-04dc-4bb9-ada5-0a8e80a9f55a', 'ro', 'ro', 'ROU', 'RON', False, 'https://roapi.hbogo.eu/oauthvodafone/protocolgateway.aspx?caller={caller}&cid={cid}&oid=6826b525-04dc-4bb9-ada5-0a8e80a9f55a&platform=COMP&backuri={backuri}'],
   'Romania: Voucher HBOGO': ['da5a4764-a001-4dac-8e52-59d0ae531a62', 'ro', 'ro', 'ROU', 'RON', False, ''],
   'Serbia: HBO GO Promo (rs)': ['6b63c0fe-91a6-41e8-ac8a-9a214834f697', 'rs', 'sr', 'SRB', 'SRP', False, ''],
   'Serbia: HBO GO Vip/Club Serbia': ['f3b52ca0-ea89-4f1d-91eb-02a4f7f60e7d', 'rs', 'sr', 'SRB', 'SRP', False, ''],
   'Serbia: SAT-TRAKT': ['486efd34-38ee-4ed5-86c0-a96f8ab09f2a', 'rs', 'sr', 'SRB', 'SRP', False, ''],
   'Serbia: SBB': ['54bfd03b-a4a3-43a3-87da-9a41d67b13e8', 'rs', 'sr', 'SRB', 'SRP', False, ''],
   'Serbia: Telekom Srbija': ['0d085ea6-63c9-452e-b5ec-db1aa8b38fef', 'rs', 'sr', 'SRB', 'SRP', False, ''],
   'Serbia: Telenor': ['1fac38e7-3677-4607-b60a-f968b80d8084', 'rs', 'sr', 'SRB', 'SRP', False, ''],
   'Slovakia: freeSAT Česká republika': ['f8e915f5-4641-47b1-a585-d93f61bbbfd3', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: Skylink': ['c55e69f0-2471-46a9-a8b7-24dac54e6eb9', 'sk', 'sk', 'SVK', 'SLO', False, 'https://czapi.hbogo.eu/oauthskylink/protocolgateway.aspx?caller={caller}&cid={cid}&oid=c55e69f0-2471-46a9-a8b7-24dac54e6eb9&platform=COMP&backuri={backuri}'],
   'Slovakia: UPC CZ': ['f0e09ddb-1286-4ade-bb30-99bf1ade7cff', 'sk', 'sk', 'SVK', 'SLO', False, 'https://czapi.hbogo.eu/oauthupc/protocolgateway.aspx?caller={caller}&cid={cid}&oid=f0e09ddb-1286-4ade-bb30-99bf1ade7cff&platform=COMP&backuri={backuri}'],
   'Slovakia: Slovak Telekom': ['3a2f741b-bcbc-455f-b5f8-cfc55fc910a3', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: Lepší.TV': ['5696ea41-2087-46f9-9f69-874f407f8103', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: O2': ['b8a2181d-b70a-49a7-b823-105c995199a2', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: RIO Media': ['a72f9a11-edc8-4c0e-84d4-17247c1111f5', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: UPC BROADBAND SLOVAKIA': ['249309a7-6e61-436d-aa12-eeaddcfeb72e', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: AIM': ['cdb7396a-bd2c-45e9-a023-71441e8dae64', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: T-Mobile Czech Republic a.s.': ['ac49b07c-4605-409c-83bd-16b5404b16a7', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: Antik Telecom': ['ad5a1855-1abd-4aa5-a947-f9942a08ca75', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: CentroNet, a. s.': ['80c3f17b-718c-4f1b-9a58-67b5ac13b6fd', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: DIGI CZ s. r. o.': ['b132e3a1-ea76-4659-8656-1aac32bccd56', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: DIGI SLOVAKIA s.r.o.': ['cd2b4592-90be-4ad7-96a0-54e34ee74866', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: FixPro': ['6c9e2104-83dc-48fb-a44c-ee3b8d689005', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: flexiTV': ['1bfb5785-446d-4ca7-b7a4-cc76f48c97fe', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: freeSAT Slovensko': ['b3ce9ab2-af8f-4e02-8ab7-9a01d587a35f', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: GRAPE SC': ['25e0270f-ae80-49b1-9a20-bfa47b7690e1', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: HD Kabel': ['82811c4a-ad87-4bda-a1bd-2f4a4215eac4', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: Kuki': ['aa2a90c0-292c-444e-a069-1ae961fa59f7', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: MARTICO': ['95a5f7c8-95b7-4978-8fff-abe023249196', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: Nej.cz': ['6925e9ca-9d97-446c-b3c2-09971f441f2a', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: NETBOX': ['a2edba6f-bffb-4efe-bb7a-3b51e2fc0573', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: Satro': ['939ffed6-d015-427e-a2f7-a82d1b846eb7', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: SATT': ['064a6c6a-0556-4ff1-8d4d-c8cf3141131a', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: SELFNET': ['c2c2fdb7-8562-4b16-a09c-f7530ce2ce78', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: sledovanitv.cz s.r.o.': ['980a4419-1336-4056-a561-268afe7907f3', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: Slovanet a.s.': ['8a312c76-9e9c-42e4-b38c-c0adbd6c6a93', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: SWAN, a. s.': ['5b8544f8-784a-473b-97ad-159a2f95d0fb', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: Tesatel': ['69253de6-3935-4c48-9557-5a1e930f30de', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: HBO GO special': ['b59ee559-45b9-46a0-a40c-7f41ab6e53e9', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: HBO GO Vip/Club Czech Republic': ['a215610d-aecb-4357-934f-403813a7566c', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: HBO Development Czech': ['ad729e98-c792-4bce-9588-106f11ce3b90', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovakia: HBO GO VIP/Club Slovakia': ['2e61999a-1b77-4ed2-b531-081dfdd3bee0', 'sk', 'sk', 'SVK', 'SLO', False, ''],
   'Slovenija: Ario d.o.o.': ['660cd5e3-4630-4283-ad5d-50b65ebdeea8', 'si', 'si', 'SVN', 'SLV', False, ''],
   'Slovenija: HBO GO Promo (si)': ['5d4cc09d-2947-48c0-ac65-91d52786907d', 'si', 'si', 'SVN', 'SLV', False, ''],
   'Slovenija: HBO GO Vip/Club Slovenia': ['eb266b63-532b-4c53-bf9b-b7190d5f75db', 'si', 'si', 'SVN', 'SLV', False, ''],
   'Slovenija: KRS CATV Selnica-Ruše': ['f196f33a-d8ce-47b9-91b8-af8864a34dbc', 'si', 'si', 'SVN', 'SLV', False, ''],
   'Slovenija: T-2 d.o.o.': ['7d442a4b-1c7c-4f4d-a991-7a80ad4e9094', 'si', 'si', 'SVN', 'SLV', False, ''],
   'Slovenija: Telekom Slovenije': ['2387fe14-c430-45f5-a23d-7c22ec5670aa', 'si', 'si', 'SVN', 'SLV', False, ''],
   'Slovenija: Telemach': ['93a542b5-b4d8-4c76-bf3b-1eb261e39cfe', 'si', 'si', 'SVN', 'SLV', False, ''],

}
#0 operator id,  1 domain, 2 short code, 3 long code, 4 def language, 5 web
op_id = op_ids[operator][0]
xbmc.log(DEBUG_ID_STRING+"OPERATOR ID: " + op_id)

COUNTRY_ID = op_ids[operator][3]
xbmc.log(DEBUG_ID_STRING+"OPERATOR COUNTRY_ID: " + op_ids[operator][3])
COUNTRY_CODE_SHORT = op_ids[operator][2]
xbmc.log(DEBUG_ID_STRING+"OPERATOR COUNTRY_CODE_SHORT: " + op_ids[operator][2])
COUNTRY_CODE = op_ids[operator][3]
xbmc.log(DEBUG_ID_STRING+"OPERATOR COUNTRY_CODE: " + op_ids[operator][3])
IS_WEB = op_ids[operator][5]
xbmc.log(DEBUG_ID_STRING+"OPERATOR IS HBO GO WEB: " + str(IS_WEB))
DEFAULT_LANGUAGE = op_ids[operator][4]
xbmc.log(DEBUG_ID_STRING+"DEFAULT HBO GO LANGUAGE: " + DEFAULT_LANGUAGE)
DOMAIN_CODE = op_ids[operator][1]
REDIRECT_URL = op_ids[operator][6]
xbmc.log(DEBUG_ID_STRING+"HBO GO REDIRECT URL: " + REDIRECT_URL)

# API URLS
LANGUAGE_CODE = DEFAULT_LANGUAGE

if __language__(32000) == 'ENG':  # only englih or the default language for the selected operator is allowed
    LANGUAGE_CODE = 'ENG'

#check if default language is forced
if __settings__.getSetting('deflang') == 'true':
    LANGUAGE_CODE = DEFAULT_LANGUAGE

ACCEPT_LANGUAGE = 'en-us,en;q=0.8'


API_PLATFORM = 'COMP'
# API_PLATFORM = 'MOBI'
# API_PLATFORM = 'APPLE'
# API_PLATFORM = 'SONY'

LICENSE_SERVER = 'https://lic.drmtoday.com/license-proxy-widevine/cenc/'

API_HOST = COUNTRY_CODE_SHORT + 'api.hbogo.eu'
API_HOST_REFERER = 'https://hbogo.' + DOMAIN_CODE + '/'
API_HOST_ORIGIN = 'https://www.hbogo.' + DOMAIN_CODE
API_HOST_GATEWAY = 'https://gateway.hbogo.eu'
API_HOST_GATEWAY_REFERER = 'https://gateway.hbogo.eu/signin/form'

API_URL_SILENTREGISTER = 'https://' + COUNTRY_CODE_SHORT + '.hbogo.eu/services/settings/silentregister.aspx'

API_URL_SETTINGS = 'https://' + API_HOST + '/v7/Settings/json/' + LANGUAGE_CODE + '/'+API_PLATFORM
API_URL_AUTH_WEBBASIC = 'https://api.ugw.hbogo.eu/v3.0/Authentication/' + COUNTRY_CODE + '/JSON/' + LANGUAGE_CODE + '/'+API_PLATFORM
API_URL_AUTH_OPERATOR = 'https://' + COUNTRY_CODE_SHORT + 'gwapi.hbogo.eu/v2.1/Authentication/json/' + LANGUAGE_CODE + '/'+API_PLATFORM
API_URL_CUSTOMER_GROUP = 'https://' + API_HOST + '/v7/CustomerGroup/json/' + LANGUAGE_CODE + '/' + API_PLATFORM + '/'
API_URL_GROUPS = 'https://' + API_HOST + '/v5/Groups/json/' + LANGUAGE_CODE + '/'+API_PLATFORM
API_URL_CONTENT='http://'+API_HOST+'/v5/Content/json/'+LANGUAGE_CODE + '/' + API_PLATFORM + '/'
API_URL_PURCHASE = 'https://' + API_HOST + '/v5/Purchase/Json/' + LANGUAGE_CODE + '/'+API_PLATFORM
API_URL_SEARCH = 'https://' + API_HOST + '/v5/Search/Json/' + LANGUAGE_CODE + '/' + API_PLATFORM + '/'

individualization = ""
goToken = ""
customerId = ""
GOcustomerId = ""
sessionId = '00000000-0000-0000-0000-000000000000'
FavoritesGroupId = ""

loggedin_headers = {
    'User-Agent': UA,
    'Accept': '*/*',
    'Accept-Language': ACCEPT_LANGUAGE,
    'Referer': API_HOST_REFERER,
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Origin': API_HOST_ORIGIN,
    'X-Requested-With': 'XMLHttpRequest',
    'GO-Language': LANGUAGE_CODE,
    'GO-requiredPlatform': GO_REQUIRED_PLATFORM,
    'GO-Token': '',
    'GO-SessionId': '',
    'GO-swVersion': GO_SW_VERSION,
    'GO-CustomerId': '',
    'Connection': 'keep-alive',
    'Accept-Encoding': ''
}


def storeIndiv(indiv, custid):
    global individualization
    global customerId

    individualization = __settings__.getSetting('individualization')
    if individualization == "":
        __settings__.setSetting('individualization', indiv)
        individualization = indiv

    customerId = __settings__.getSetting('customerId')
    if customerId == "":
        __settings__.setSetting('customerId', custid)
        customerId = custid


# FavoritesGroupId
def storeFavgroup(favgroupid):
    global FavoritesGroupId

    FavoritesGroupId = __settings__.getSetting('FavoritesGroupId')
    if FavoritesGroupId == "":
        __settings__.setSetting('FavoritesGroupId', favgroupid)
        FavoritesGroupId = favgroupid


# silent registration
def SILENTREGISTER():
    global goToken
    global individualization
    global customerId
    global sessionId

    req = urllib2.Request(API_URL_SILENTREGISTER, None, loggedin_headers)

    opener = urllib2.build_opener()
    f = opener.open(req)
    jsonrsp = json.loads(f.read())

    if jsonrsp['Data']['ErrorMessage']:
        xbmcgui.Dialog().ok(LB_ERROR, jsonrsp['Data']['ErrorMessage'])

    indiv = jsonrsp['Data']['Customer']['CurrentDevice']['Individualization']
    custid = jsonrsp['Data']['Customer']['CurrentDevice']['Id'];
    storeIndiv(indiv, custid)

    sessionId = jsonrsp['Data']['SessionId']
    return jsonrsp


def GETFAVORITEGROUP():
    global FavoritesGroupId

    req = urllib2.Request(API_URL_SETTINGS, None, loggedin_headers)

    opener = urllib2.build_opener()
    f = opener.open(req)
    jsonrsp = json.loads(f.read())

    favgroupId = jsonrsp['FavoritesGroupId']
    storeFavgroup(favgroupId)


def save_obj(obj, name ):
    folder = xbmc.translatePath("special://temp")
    xbmc.log(DEBUG_ID_STRING + "Saving: " + folder + name + '.pkl')
    with open(folder + name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name):
    folder = xbmc.translatePath("special://temp")
    xbmc.log(DEBUG_ID_STRING + "Trying to load: "+folder + name + '.pkl')
    try:
        with open(folder + name + '.pkl', 'rb') as f:
            return pickle.load(f)
    except:
        xbmc.log(DEBUG_ID_STRING + "OBJECT RELOAD ERROR")
        return None


def LOGIN():
    global sessionId
    global goToken
    global customerId
    global GOcustomerId
    global individualization
    global loggedin_headers
    global FavoritesGroupId

    username = __settings__.getSetting('username')
    password = __settings__.getSetting('password')
    customerId = __settings__.getSetting('customerId')
    individualization = __settings__.getSetting('individualization')
    FavoritesGroupId = __settings__.getSetting('FavoritesGroupId')

    if (individualization == "" or customerId == ""):
      jsonrsp = SILENTREGISTER()

    if (FavoritesGroupId == ""):
      GETFAVORITEGROUP()

    if (username == "" or password == ""):
      xbmcgui.Dialog().ok(LB_ERROR, LB_NOLOGIN)
      xbmcaddon.Addon(id='plugin.video.hbogoeu').openSettings()
      return

    login_hash = hashlib.sha224(individualization + customerId + FavoritesGroupId + username + password + op_id).hexdigest()
    xbmc.log(DEBUG_ID_STRING + "LOGIN HASH: " + login_hash)

    loaded_session=load_obj(__addon_id__ + "_session")

    if loaded_session != None:
        # sesion exist if valid restore
        xbmc.log(DEBUG_ID_STRING + "SAVED SESSION LOADED")
        if loaded_session["hash"] == login_hash:
            xbmc.log(DEBUG_ID_STRING + "HASH IS VALID")
            if time.time() < (loaded_session["time"]+(SESSION_VALIDITY*60*60)):
                xbmc.log(DEBUG_ID_STRING + "NOT EXPIRED RESTORING...")
                #valid loaded sesion restor and exit login
                xbmc.log(DEBUG_ID_STRING + "Restoring login from saved: " + str(loaded_session))
                loggedin_headers = loaded_session["headers"]
                sessionId=loggedin_headers['GO-SessionId']
                goToken=loggedin_headers['GO-Token']
                GOcustomerId=loggedin_headers['GO-CustomerId']
                xbmc.log(DEBUG_ID_STRING + "Login restored - Token" + str(goToken))
                xbmc.log(DEBUG_ID_STRING + "Login restored - Customer Id" + str(GOcustomerId))
                xbmc.log(DEBUG_ID_STRING + "Login restored - Session Id" + str(sessionId))
                return

    headers = {
        'Origin': API_HOST_GATEWAY,
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': ACCEPT_LANGUAGE,
        'User-Agent': UA,
        'GO-Token': '',
        'Accept': 'application/json',
        'GO-SessionId': '',
        'Referer': API_HOST_GATEWAY_REFERER,
        'Connection': 'keep-alive',
        'GO-CustomerId': '00000000-0000-0000-0000-000000000000',
        'Content-Type': 'application/json',
    }

    if IS_WEB:
        url = API_URL_AUTH_WEBBASIC
    else:
        url = API_URL_AUTH_OPERATOR

    if len(REDIRECT_URL) > 0:
        xbmc.log(DEBUG_ID_STRING + "OPERATOR WITH LOGIN REDIRECT DETECTED, THE LOGIN WILL PROBABLY FAIL, NOT IMPLEMENTED, more details https://github.com/arvvoid/plugin.video.hbogoeu  ISSUE #5 ")
        xbmcgui.Dialog().ok("INFORMATION", "OPERATOR WITH LOGIN REDIRECTION DETECTED, THE LOGIN WILL PROBABLY FAIL. PLEASE REPORT THE OUTCOME. TO FIND OUT MORE ABOUTE THE ISSUE AND/OR CONTRIBUTE GO TO https://github.com/arvvoid/plugin.video.hbogoeu  ISSUE #5 ")
        # EXPLANATION
        # ------------
        # For a few operators the login is not performed directly using the hbogo api. Instead the user is redirected to the operator website
        # the login is performed there, and then the operator login the user on hbogo and redirect back.
        # What exactly happens and how, will have to be figured out and then implemented in the add-on for those operators to work.
        # For more information go to https://github.com/arvvoid/plugin.video.hbogoeu  ISSUE #5

    data_obj = {
        "Action": "L",
        "AppLanguage": None,
        "ActivationCode": None,
        "AllowedContents": [],
        "AudioLanguage": None,
        "AutoPlayNext": False,
        "BirthYear": 1,
        "CurrentDevice": {
            "AppLanguage": "",
            "AutoPlayNext": False,
            "Brand": "Chromium",
            "CreatedDate": "",
            "DeletedDate": "",
            "Id": "00000000-0000-0000-0000-000000000000",
            "Individualization": individualization,
            "IsDeleted": False,
            "LastUsed": "",
            "Modell": "71",
            "Name": "",
            "OSName": "Ubuntu",
            "OSVersion": "undefined",
            "Platform": API_PLATFORM,
            "SWVersion": "3.3.9.6418.2100",
            "SubtitleSize": ""
        },
        "CustomerCode": "",
        "DebugMode": False,
        "DefaultSubtitleLanguage": None,
        "EmailAddress": username,
        "FirstName": "",
        "Gender": 0,
        "Id": "00000000-0000-0000-0000-000000000000",
        "IsAnonymus": True,
        "IsPromo": False,
        "Language": LANGUAGE_CODE,
        "LastName": "",
        "Nick": "",
        "NotificationChanges": 0,
        "OperatorId": op_id,
        "OperatorName": "",
        "OperatorToken": "",
        "ParentalControl": {
            "Active": False,
            "Password": "",
            "Rating": 0,
            "ReferenceId": "00000000-0000-0000-0000-000000000000"
        },
        "Password": password,
        "PromoCode": "",
        "ReferenceId": "00000000-0000-0000-0000-000000000000",
        "SecondaryEmailAddress": "",
        "SecondarySpecificData": None,
        "ServiceCode": "",
        "SubscribeForNewsletter": False,
        "SubscState": None,
        "SubtitleSize": "",
        "TVPinCode": "",
        "ZipCode": ""
    }

    data = json.dumps(data_obj)
    # xbmc.log(DEBUG_ID_STRING+"PERFORMING LOGIN: " + str(data))
    xbmc.log(DEBUG_ID_STRING+"PERFORMING LOGIN")
    r = requests.post(url, headers=headers, data=data)
    jsonrspl = json.loads(r.text)

    try:
        if jsonrspl['ErrorMessage']:
            xbmc.log(DEBUG_ID_STRING+"LOGIN ERROR: "+str(jsonrspl['ErrorMessage']))
            xbmcgui.Dialog().ok(LB_ERROR, jsonrspl['ErrorMessage'])
            return
    except:
        pass

    customerId = jsonrspl['Customer']['CurrentDevice']['Id']
    individualization = jsonrspl['Customer']['CurrentDevice']['Individualization']

    sessionId = jsonrspl['SessionId']
    if sessionId == '00000000-0000-0000-0000-000000000000':
        xbmc.log(DEBUG_ID_STRING+"GENERIC LOGIN ERROR")
        xbmcgui.Dialog().ok(LB_ERROR, LB_LOGIN_ERROR)
        return
    else:
        goToken = jsonrspl['Token']
        GOcustomerId = jsonrspl['Customer']['Id']
        xbmc.log(DEBUG_ID_STRING+"Login sucess - Token" + str(goToken))
        xbmc.log(DEBUG_ID_STRING+"Login sucess - Customer Id" + str(GOcustomerId))
        xbmc.log(DEBUG_ID_STRING+"Login sucess - Session Id" + str(sessionId))
        loggedin_headers['GO-SessionId'] = str(sessionId)
        loggedin_headers['GO-Token'] = str(goToken)
        loggedin_headers['GO-CustomerId'] = str(GOcustomerId)
        #save the session with validity of 2h to not relogin every run of the add-on
        saved_session = {

            "hash": login_hash,
            "headers": loggedin_headers,
            "time": time.time()

        }
        xbmc.log(DEBUG_ID_STRING + "SAVING SESSION: " + str(saved_session))
        save_obj(saved_session, __addon_id__+"_session")

def CATEGORIES():
    global FavoritesGroupId

    addCat(LB_SEARCH, LB_SEARCH, '', 4)

    if (FavoritesGroupId == ""):
        GETFAVORITEGROUP()

    if (FavoritesGroupId != ""):
        addCat(LB_MYPLAYLIST, API_URL_CUSTOMER_GROUP + FavoritesGroupId + '/-/-/-/1000/-/-/false',
               md + 'FavoritesFolder.png', 1)

    req = urllib2.Request(API_URL_GROUPS, None, loggedin_headers)
    opener = urllib2.build_opener()
    f = opener.open(req)
    jsonrsp = json.loads(f.read())

    try:
        if jsonrsp['ErrorMessage']:
            xbmcgui.Dialog().ok(LB_ERROR, jsonrsp['ErrorMessage'])
    except:
        pass

    for cat in jsonrsp['Items']:
        addCat(cat['Name'].encode('utf-8', 'ignore'),
               cat['ObjectUrl'].replace('/0/{sort}/{pageIndex}/{pageSize}/0/0', '/0/0/1/1024/0/0'),
               md + 'DefaultFolder.png', 1)


def LIST(url):
    xbmc.log(DEBUG_ID_STRING+"List: " + str(url))
    global sessionId
    global loggedin_headers

    if sessionId == '00000000-0000-0000-0000-000000000000':
        LOGIN()

    req = urllib2.Request(url, None, loggedin_headers)
    opener = urllib2.build_opener()
    f = opener.open(req)
    jsonrsp = json.loads(f.read())

    try:
        if jsonrsp['ErrorMessage']:
            xbmcgui.Dialog().ok(LB_ERROR, jsonrsp['ErrorMessage'])
    except:
        pass
    # If there is a subcategory / genres
    if len(jsonrsp['Container']) > 1:
        for Container in range(0, len(jsonrsp['Container'])):
            addCat(jsonrsp['Container'][Container]['Name'].encode('utf-8', 'ignore'),
                   jsonrsp['Container'][Container]['ObjectUrl'], md + 'DefaultFolder.png', 1)
    else:
        for title in jsonrsp['Container'][0]['Contents']['Items']:
            if title['ContentType'] == 1 or title['ContentType'] == 3:  # 1=MOVIE/EXTRAS, 2=SERIES(serial), 3=SERIES(episode)
                addLink(title,5)
            else:
                addDir(title, 2,"tvshow")


def SEASON(url):
    xbmc.log(DEBUG_ID_STRING+"Season: " + str(url))
    req = urllib2.Request(url, None, loggedin_headers)
    opener = urllib2.build_opener()
    f = opener.open(req)
    jsonrsp = json.loads(f.read())

    try:
        if jsonrsp['ErrorMessage']:
            xbmcgui.Dialog().ok(LB_ERROR, jsonrsp['ErrorMessage'])
    except:
        pass
    for season in jsonrsp['Parent']['ChildContents']['Items']:
        addDir(season, 3, "season")


def EPISODE(url):
    xbmc.log(DEBUG_ID_STRING+"Episode: " + str(url))
    req = urllib2.Request(url, None, loggedin_headers)
    opener = urllib2.build_opener()
    f = opener.open(req)
    jsonrsp = json.loads(f.read())

    try:
        if jsonrsp['ErrorMessage']:
            xbmcgui.Dialog().ok(LB_ERROR, jsonrsp['ErrorMessage'])
    except:
        pass

    for episode in jsonrsp['ChildContents']['Items']:
        addLink(episode, 5)


def PLAY(url):
    xbmc.log(DEBUG_ID_STRING+"Play: " + str(url))
    global goToken
    global individualization
    global customerId
    global GOcustomerId
    global sessionId
    global loggedin_headers

    if sessionId == '00000000-0000-0000-0000-000000000000':
        LOGIN()

    purchase_payload = '<Purchase xmlns="go:v5:interop"><AllowHighResolution>true</AllowHighResolution><ContentId>' + cid + '</ContentId><CustomerId>' + GOcustomerId + '</CustomerId><Individualization>' + individualization + '</Individualization><OperatorId>' + op_id + '</OperatorId><ClientInfo></ClientInfo><IsFree>false</IsFree><UseInteractivity>false</UseInteractivity></Purchase>'
    xbmc.log(DEBUG_ID_STRING+"Purchase payload: " + str(purchase_payload))
    purchase_headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': '',
        'Accept-Language': ACCEPT_LANGUAGE,
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'GO-CustomerId': str(GOcustomerId),
        'GO-requiredPlatform': GO_REQUIRED_PLATFORM,
        'GO-SessionId': str(sessionId),
        'GO-swVersion': GO_SW_VERSION,
        'GO-Token': str(goToken),
        'Host': API_HOST,
        'Referer': API_HOST_REFERER,
        'Origin': API_HOST_ORIGIN,
        'User-Agent': UA
    }
    xbmc.log(DEBUG_ID_STRING+"Requesting purchase: " + str(API_URL_PURCHASE))
    req = urllib2.Request(API_URL_PURCHASE, purchase_payload, purchase_headers)
    opener = urllib2.build_opener()
    f = opener.open(req)
    jsonrspp = json.loads(f.read())
    xbmc.log(DEBUG_ID_STRING+"Purchase response: " + str(jsonrspp))

    try:
        if jsonrspp['ErrorMessage']:
            xbmc.log(DEBUG_ID_STRING+"Purchase error: " + str(jsonrspp['ErrorMessage']))
            xbmcgui.Dialog().ok(LB_ERROR, jsonrspp['ErrorMessage'])
    except:
        pass

    MediaUrl = jsonrspp['Purchase']['MediaUrl'] + "/Manifest"
    xbmc.log(DEBUG_ID_STRING+"Media Url: " + str(jsonrspp['Purchase']['MediaUrl'] + "/Manifest"))
    PlayerSessionId = jsonrspp['Purchase']['PlayerSessionId']
    xbmc.log(DEBUG_ID_STRING+"PlayerSessionId: " + str(jsonrspp['Purchase']['PlayerSessionId']))
    x_dt_auth_token = jsonrspp['Purchase']['AuthToken']
    xbmc.log(DEBUG_ID_STRING+"Auth token: " + str(jsonrspp['Purchase']['AuthToken']))
    dt_custom_data = base64.b64encode(
        "{\"userId\":\"" + GOcustomerId + "\",\"sessionId\":\"" + PlayerSessionId + "\",\"merchant\":\"hboeurope\"}")

    li = xbmcgui.ListItem(iconImage=thumbnail, thumbnailImage=thumbnail, path=MediaUrl)
    license_headers = 'dt-custom-data=' + dt_custom_data + '&x-dt-auth-token=' + x_dt_auth_token + '&Origin=' + API_HOST_ORIGIN + '&Content-Type='
    license_key = LICENSE_SERVER + '|' + license_headers + '|R{SSM}|JBlicense'
    xbmc.log(DEBUG_ID_STRING+"Licence key: " + str(license_key))
    protocol = 'ism'
    drm = 'com.widevine.alpha'
    is_helper = inputstreamhelper.Helper(protocol, drm=drm)
    is_helper.check_inputstream()
    li.setProperty('inputstreamaddon', 'inputstream.adaptive')
    li.setProperty('inputstream.adaptive.manifest_type', protocol)
    li.setProperty('inputstream.adaptive.license_type', drm)
    li.setProperty('inputstream.adaptive.license_data', 'ZmtqM2xqYVNkZmFsa3Izag==')
    li.setProperty('inputstream.adaptive.license_key', license_key)
    xbmc.log(DEBUG_ID_STRING+"Play url: " + str(li))
    xbmcplugin.setResolvedUrl(__handle__, True, li)


def SEARCH():
    keyb = xbmc.Keyboard(search_string, LB_SEARCH_DESC)
    keyb.doModal()
    searchText = ''
    if (keyb.isConfirmed()):
        searchText = urllib.quote_plus(keyb.getText())
        if searchText == "":
            addCat(LB_SEARCH_NORES, LB_SEARCH_NORES, md + 'DefaultFolderBack.png', '')
        else:
            __settings__.setSetting('lastsearch', searchText)
            xbmc.log(DEBUG_ID_STRING+"Performing search: " + str(API_URL_SEARCH + searchText.decode('utf-8', 'ignore').encode('utf-8', 'ignore') + '/0'))
            req = urllib2.Request(
                API_URL_SEARCH + searchText.decode('utf-8', 'ignore').encode('utf-8', 'ignore') + '/0', None,
                loggedin_headers)
            opener = urllib2.build_opener()
            f = opener.open(req)
            jsonrsp = json.loads(f.read())
            xbmc.log(str(jsonrsp))

            try:
                if jsonrsp['ErrorMessage']:
                    xbmc.log(DEBUG_ID_STRING+"Search Error: " + str(jsonrsp['ErrorMessage']))
                    xbmcgui.Dialog().ok(LB_ERROR, jsonrsp['ErrorMessage'])
            except:
                pass

            br = 0
            for item in jsonrsp['Container'][0]['Contents']['Items']:
                if item['ContentType'] == 1 or item['ContentType'] == 7 or item['ContentType'] == 3:  # 1,7=MOVIE/EXTRAS, 2=SERIES(serial), 3=SERIES(episode)
                    addLink(item, 5)
                else:
                    addDir(item, 2, "tvshow")
                br = br + 1
            if br == 0:
                addCat(LB_SEARCH_NORES, LB_SEARCH_NORES, md + 'DefaultFolderBack.png', '')


def addLink(title, mode):
    xbmc.log(DEBUG_ID_STRING + "Adding Link: " + str(title) + " MODE: "+ str(mode))
    cid = title['ObjectUrl'].rsplit('/', 2)[1]

    plot = ""
    name = ""
    media_type="movie"
    if title['ContentType'] == 1:  # 1=MOVIE/EXTRAS, 2=SERIES(serial), 3=SERIES(episode)
        name = title['Name'].encode('utf-8', 'ignore')
        if force_original_names:
            name = title['OriginalName'].encode('utf-8', 'ignore')
        filename = title['OriginalName'].encode('utf-8', 'ignore') + " (" + str(title['ProductionYear']) + ")"
        if force_scraper_names:
            name = filename
        plot = title['Abstract'].encode('utf-8', 'ignore')
        if 'AvailabilityTo' in title:
            if title['AvailabilityTo'] is not None:
                plot = plot + ' ' + LB_FILM_UNTILL + ' ' + title['AvailabilityTo'].encode('utf-8', 'ignore')
    elif title['ContentType'] == 3:
        media_type = "episode"
        name = title['SeriesName'].encode('utf-8', 'ignore') + " - " + str(title['SeasonIndex']) + " " + LB_SEASON + ", " + LB_EPISODE + " " + str(title['Index'])
        if force_original_names:
            name = title['OriginalName'].encode('utf-8', 'ignore')
        filename = title['Tracking']['ShowName'].encode('utf-8', 'ignore') + " - S" + str(title['Tracking']['SeasonNumber']) + "E" + str(title['Tracking']['EpisodeNumber'])
        if force_scraper_names:
            name = filename
        plot = title['Abstract'].encode('utf-8', 'ignore')
        if 'AvailabilityTo' in title:
            plot = plot + ' ' + LB_EPISODE_UNTILL + ' ' + title['AvailabilityTo'].encode('utf-8', 'ignore')

    u = __addonurl__ + "?url=" + urllib.quote_plus(title['ObjectUrl']) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(
        filename) + "&cid=" + cid + "&thumbnail=" + title['BackgroundUrl']

    ok = True
    liz = xbmcgui.ListItem(name, iconImage=title['BackgroundUrl'], thumbnailImage=title['BackgroundUrl'])
    liz.setArt({'thumb': title['BackgroundUrl'], 'poster': title['BackgroundUrl'], 'banner': title['BackgroundUrl'], 'fanart': title['BackgroundUrl']})
    liz.setInfo(type="Video",
                infoLabels={"mediatype": media_type, "episode": title['Tracking']['EpisodeNumber'], "season": title['Tracking']['SeasonNumber'], "tvshowtitle": title['Tracking']['ShowName'], "plot": plot, "mpaa": str(title['AgeRating']) + '+', "rating": title['ImdbRate'], "cast": [title['Cast'].split(', ')][0], "director": title['Director'],
                            "writer": title['Writer'], "duration": title['Duration'], "genre": title['Genre'], "title": name, "originaltitle": title['OriginalName'],
                            "year": title['ProductionYear']})
    liz.addStreamInfo('video', {'width': 1920, 'height': 1080})
    liz.addStreamInfo('video', {'aspect': 1.78, 'codec': 'h264'})
    liz.addStreamInfo('audio', {'codec': 'aac', 'channels': 2})
    liz.setProperty("IsPlayable", "true")
    ok = xbmcplugin.addDirectoryItem(handle=__handle__, url=u, listitem=liz, isFolder=False)
    return ok


def addDir(item, mode, media_type):
    xbmc.log(DEBUG_ID_STRING + "Adding Dir: " + str(item) + " MODE: "+ str(mode))
    u = __addonurl__ + "?url=" + urllib.quote_plus(item['ObjectUrl']) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(item['OriginalName'].encode('utf-8', 'ignore') + " (" + str(item['ProductionYear']) + ")")
    ok = True
    liz = xbmcgui.ListItem(item['Name'].encode('utf-8', 'ignore'), iconImage="DefaultFolder.png", thumbnailImage=item['BackgroundUrl'])
    liz.setInfo(type="Video", infoLabels={"mediatype": media_type, "season": item['Tracking']['SeasonNumber'], "tvshowtitle": item['Tracking']['ShowName'], "title": item['Name'].encode('utf-8', 'ignore'), "Plot": item['Abstract'].encode('utf-8', 'ignore')})
    liz.setProperty('isPlayable', "false")
    ok = xbmcplugin.addDirectoryItem(handle=__handle__, url=u, listitem=liz, isFolder=True)
    return ok


def addCat(name, url, icon, mode):
    xbmc.log(DEBUG_ID_STRING + "Adding Cat: " + str(name) + "," + str(url) + "," + str(icon) +  " MODE: " + str(mode))
    u = __addonurl__ + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=icon)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    liz.setProperty('isPlayable', "false")
    ok = xbmcplugin.addDirectoryItem(handle=__handle__, url=u, listitem=liz, isFolder=True)
    return ok


params = dict(parse_qsl(sys.argv[2][1:]))
url = None
name = None
iconimage = None
mode = None

try:
    url = urllib.unquote_plus(params["url"])
except:
    pass
try:
    name = urllib.unquote_plus(params["name"])
except:
    pass
try:
    thumbnail = str(params["thumbnail"])
except:
    pass
try:
    mode = int(params["mode"])
except:
    pass
try:
    cid = str(params["cid"])
except:
    pass

if mode == None or url == None or len(url) < 1:
    CATEGORIES()

elif mode == 1:
    LIST(url)

elif mode == 2:
    SEASON(url)

elif mode == 3:
    EPISODE(url)

elif mode == 4:
    SEARCH()

elif mode == 5:
    PLAY(url)

elif mode == 6:
    SILENTREGISTER()

elif mode == 7:
    LOGIN()

xbmcplugin.endOfDirectory(__handle__)
