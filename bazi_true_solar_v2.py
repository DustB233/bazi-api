#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: 钉钉、抖音或微信pythontesting 钉钉群21734177
# CreateDate: 2019-2-21

import argparse
import collections
import pprint
import datetime

import math

# location/time helpers
import pytz
# geocoding (optional). We avoid network by default; only used if you pass --geocode.
try:
    from geopy.geocoders import Nominatim  # type: ignore
    from geopy.exc import GeocoderServiceError, GeocoderInsufficientPrivileges  # type: ignore
except Exception:  # pragma: no cover
    Nominatim = None
    GeocoderServiceError = Exception
    GeocoderInsufficientPrivileges = Exception

from lunar_python import Lunar, Solar
from colorama import init

from datas import *
from sizi import summarys
from common import *
from yue import months

def get_gen(gan, zhis):
    zhus = []
    zhongs = []
    weis = []
    result = ""
    for item in zhis:
        zhu = zhi5_list[item][0]
        if ten_deities[gan]['本'] == ten_deities[zhu]['本']:
            zhus.append(item)

    for item in zhis:
        if len(zhi5_list[item]) ==1:
            continue
        zhong = zhi5_list[item][1]
        if ten_deities[gan]['本'] == ten_deities[zhong]['本']:
            zhongs.append(item)

    for item in zhis:
        if len(zhi5_list[item]) < 3:
            continue
        zhong = zhi5_list[item][2]
        if ten_deities[gan]['本'] == ten_deities[zhong]['本']:
            weis.append(item)

    if not (zhus or zhongs or weis):
        return "无根"
    else:
        result = result + "强：{}{}".format(''.join(zhus), chr(12288)) if zhus else result
        result = result + "中：{}{}".format(''.join(zhongs), chr(12288)) if zhongs else result
        result = result + "弱：{}".format(''.join(weis)) if weis else result
        return result


def gan_zhi_he(zhu):
    gan, zhi = zhu
    if ten_deities[gan]['合'] in zhi5[zhi]:
        return "|"
    return ""

def get_gong(zhis):
    result = []
    for i in range(3):
        if  gans[i] != gans[i+1]:
            continue
        zhi1 = zhis[i]
        zhi2 = zhis[i+1]
        if abs(Zhi.index(zhi1) - Zhi.index(zhi2)) == 2:
            value = Zhi[(Zhi.index(zhi1) + Zhi.index(zhi2))//2]
            #if value in ("丑", "辰", "未", "戌"):
            result.append(value)
        if (zhi1 + zhi2 in gong_he) and (gong_he[zhi1 + zhi2] not in zhis):
            result.append(gong_he[zhi1 + zhi2]) 
            
        #if (zhi1 + zhi2 in gong_hui) and (gong_hui[zhi1 + zhi2] not in zhis):
            #result.append(gong_hui[zhi1 + zhi2])             
        
    return result


def get_shens(gans, zhis, gan_, zhi_):
    
    all_shens = []
    for item in year_shens:
        if zhi_ in year_shens[item][zhis.year]:    
            all_shens.append(item)
                
    for item in month_shens:
        if gan_ in month_shens[item][zhis.month] or zhi_ in month_shens[item][zhis.month]:     
            all_shens.append(item)
                
    for item in day_shens:
        if zhi_ in day_shens[item][zhis.day]:     
            all_shens.append(item)
                
    for item in g_shens:
        if zhi_ in g_shens[item][me]:    
            all_shens.append(item) 
    if all_shens:  
        return "  神:" + ' '.join(all_shens)
    else:
        return ""
                
def jin_jiao(first, second):
    return True if Zhi.index(second) - Zhi.index(first) == 1 else False

def is_ku(zhi):
    return True if zhi in "辰戌丑未" else False  

def zhi_ku(zhi, items):
    return True if is_ku(zhi) and min(zhi5[zhi], key=zhi5[zhi].get) in items else False

def is_yang():
    return True if Gan.index(me) % 2 == 0 else False

def not_yang():
    return False if Gan.index(me) % 2 == 0 else True

def gan_ke(gan1, gan2):
    return True if ten_deities[gan1]['克'] == ten_deities[gan2]['本'] or ten_deities[gan2]['克'] == ten_deities[gan1]['本'] else False
    
description = '''

'''

parser = argparse.ArgumentParser(description=description,
                                 formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('year', action="store", help=u'year')
parser.add_argument('month', action="store", help=u'month')
parser.add_argument('day', action="store", help=u'day')
parser.add_argument('time', action="store", help=u"time (HH or HH:MM or HH:MM:SS)")
parser.add_argument('--city', help='Birth city (for 真太阳时 conversion). Example: Qingdao', default=None)
parser.add_argument('--country', help='Birth country (for 真太阳时 conversion). Example: China', default=None)
parser.add_argument('--tz', help='IANA timezone name for the birth location (recommended). Example: Asia/Shanghai', default=None)
parser.add_argument('--lon', type=float, help='Longitude in degrees (east positive). If set, skips geocoding.', default=None)
parser.add_argument('--lat', type=float, help='Latitude in degrees (optional).', default=None)
parser.add_argument('--geocode', action='store_true', default=False,
                    help='Attempt online geocoding for city/country (may fail on some networks). If omitted, use built-in city table or --lon/--lat.')
parser.add_argument('--use_dst', action='store_true', default=False,
                    help='If set, include DST when computing standard meridian. Default: DST ignored (treat input clock time as standard time).')
parser.add_argument("--start", help="start year", type=int, default=1850)
parser.add_argument("--end", help="end year", default='2030')
parser.add_argument('-b', action="store_true", default=False, help=u'直接输入八字')
parser.add_argument('-g', action="store_true", default=False, help=u'是否采用公历')
parser.add_argument('-r', action="store_true", default=False, help=u'是否为闰月，仅仅使用于农历')
parser.add_argument('-n', action="store_true", default=False, help=u'是否为女，默认为男')
parser.add_argument('--version', action='version',
                    version='%(prog)s 1.0 Rongzhong xu 2022 06 15')
def parse_time_arg(time_str):
    """Parse time argument that may be 'H', 'HH:MM', or 'HH:MM:SS' (also accepts 'HH.MM')."""
    s = str(time_str).strip()
    # support 'HH.MM' as a common user input meaning HH:MM
    if ':' not in s and s.count('.') == 1 and all(p.isdigit() for p in s.split('.')) and len(s.split('.')[1]) in (1,2):
        s = s.replace('.', ':', 1)

    parts = s.split(':')
    if len(parts) == 1:
        h, m, sec = parts[0], '0', '0'
    elif len(parts) == 2:
        h, m = parts
        sec = '0'
    elif len(parts) == 3:
        h, m, sec = parts
    else:
        raise argparse.ArgumentTypeError(f"Invalid time format: {time_str}. Use HH or HH:MM or HH:MM:SS")

    try:
        h_i, m_i, s_i = int(h), int(m), int(sec)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid time numbers: {time_str}. Use HH or HH:MM or HH:MM:SS")

    if not (0 <= h_i <= 23):
        raise argparse.ArgumentTypeError(f"Hour out of range (0-23): {h_i}")
    if not (0 <= m_i <= 59):
        raise argparse.ArgumentTypeError(f"Minute out of range (0-59): {m_i}")
    if not (0 <= s_i <= 59):
        raise argparse.ArgumentTypeError(f"Second out of range (0-59): {s_i}")
    return h_i, m_i, s_i


def _equation_of_time_minutes(dt: datetime.datetime) -> float:
    # Approximate equation of time (minutes) (Spencer formula).
    n = dt.timetuple().tm_yday
    B = 2.0 * math.pi * (n - 81) / 364.0
    return 9.87 * math.sin(2 * B) - 7.53 * math.cos(B) - 1.5 * math.sin(B)

# Built-in city -> (lon, lat) table for offline 真太阳时 conversion.
# Keys are normalized as "city,country" lowercased, trimmed.
_CITY_LONLAT = {
    "shanghai,china": (121.458060, 31.222220),
    "beijing,china": (116.397230, 39.907500),
    "shenzhen,china": (114.068300, 22.545540),
    "guangzhou,china": (113.250000, 23.116670),
    "chengdu,china": (104.066670, 30.666670),
    "tianjin,china": (117.176670, 39.142220),
    "wuhan,china": (114.266670, 30.583330),
    "dongguan,china": (113.748660, 23.017970),
    "xi'an,china": (108.928610, 34.258330),
    "nanjing,china": (118.777780, 32.061670),
    "hangzhou,china": (120.161420, 30.293650),
    "foshan,china": (113.131480, 23.026770),
    "london,uk": (-0.125740, 51.508530),
    "new york city,usa": (-74.005970, 40.714270),
    "taipei,taiwan": (121.526390, 25.053060),
    "chongqing,china": (106.557710, 29.560260),
    "hong kong,china": (114.174690, 22.278320),
    "qingdao,china": (120.380420, 36.064880),
    "shenyang,china": (123.432780, 41.792220),
    "suzhou,china": (120.595380, 31.304080),
    "singapore,singapore": (103.850070, 1.289670),
    "harbin,china": (126.650000, 45.750000),
    "hefei,china": (117.280830, 31.863890),
    "dalian,china": (121.602220, 38.912220),
    "changchun,china": (125.322780, 43.880000),
    "xiamen,china": (118.081870, 24.479790),
    "bao'an,china": (113.882880, 22.552130),
    "wuxi,china": (120.288570, 31.568870),
    "jinan,china": (116.997220, 36.668330),
    "taiyuan,china": (112.560280, 37.869440),
    "zhengzhou,china": (113.648610, 34.757780),
    "new taipei city,taiwan": (121.457030, 25.061990),
    "new territories,china": (114.110950, 22.424410),
    "shijiazhuang,china": (114.478610, 38.041390),
    "kunming,china": (102.718330, 25.038890),
    "zhongshan,china": (113.379120, 22.523060),
    "nanning,china": (108.316670, 22.816670),
    "shantou,china": (116.678760, 23.354890),
    "los angeles,usa": (-118.243680, 34.052230),
    "fuzhou,china": (119.306110, 26.061390),
    "ningbo,china": (121.549450, 29.878190),
    "puyang,china": (119.888720, 29.456790),
    "shiyan,china": (110.778060, 32.647500),
    "tangshan,china": (118.183190, 39.643810),
    "lueliang,china": (111.144360, 37.519200),
    "changzhou,china": (119.954010, 31.773590),
    "zibo,china": (118.063330, 36.790560),
    "changsha,china": (112.970870, 28.198740),
    "guiyang,china": (106.716670, 26.583330),
    "ueruemqi,china": (87.600460, 43.800960),
    "lanzhou,china": (103.839870, 36.057010),
    "huizhou,china": (114.415230, 23.111470),
    "haikou,china": (110.346510, 20.034210),
    "taichung,taiwan": (120.683900, 24.146900),
    "linyi,china": (118.342780, 35.063060),
    "baoding,china": (115.462460, 38.872880),
    "kaohsiung,taiwan": (120.313330, 22.616260),
    "brooklyn,usa": (-73.949580, 40.650100),
    "chicago,usa": (-87.650050, 41.850030),
    "wenzhou,china": (120.666820, 27.999420),
    "yunfu,china": (112.038090, 22.927870),
    "huai'an,china": (119.019170, 33.588610),
    "nanchang,china": (115.853060, 28.683960),
    "hohhot,china": (111.652220, 40.810560),
    "queens,usa": (-73.836520, 40.681490),
    "houston,usa": (-95.363270, 29.763280),
    "shaoxing,china": (120.578640, 30.002370),
    "nantong,china": (120.874720, 32.030280),
    "kowloon,china": (114.183330, 22.316670),
    "yantai,china": (121.440810, 37.476490),
    "zhuhai,china": (113.567780, 22.276940),
    "baotou,china": (109.843890, 40.651600),
    "qingyang,china": (107.644550, 35.709760),
    "kunshan,china": (120.954310, 31.377620),
    "weifang,china": (119.101940, 36.710000),
    "zunyi,china": (106.907220, 27.686670),
    "lianyungang,china": (119.215560, 34.598450),
    "ganzhou,china": (114.932600, 25.846640),
    "ordos,china": (109.781570, 39.608600),
    "jieyang,china": (116.365810, 23.541800),
    "jilin,china": (126.560800, 43.846520),
    "nanchong,china": (106.084730, 30.795080),
    "tainan,taiwan": (120.213330, 22.990830),
    "datong,china": (113.291390, 40.093610),
    "nanyang,china": (112.532780, 32.994720),
    "jiangmen,china": (113.083330, 22.583330),
    "jiangyin,china": (120.263020, 31.911020),
    "fuyang,china": (115.816670, 32.900000),
    "bayan nur,china": (107.385990, 40.741430),
    "chaozhou,china": (116.622620, 23.653960),
    "qingyuan,china": (113.033330, 23.700000),
    "tai'an,china": (117.120000, 36.185280),
    "xining,china": (101.757390, 36.625540),
    "changshu,china": (120.742210, 31.646150),
    "huainan,china": (116.996940, 32.626390),
    "phoenix,usa": (-112.074040, 33.448380),
    "lu'an,china": (116.516880, 31.735610),
    "yancheng,china": (120.157300, 33.357500),
    "taizhou,china": (119.908120, 32.490690),
    "daqing,china": (125.000000, 46.583330),
    "wuhu,china": (118.429470, 31.352590),
    "dazhou,china": (107.463080, 31.210600),
    "yangzhou,china": (119.435830, 32.397220),
    "philadelphia,usa": (-75.163620, 39.952380),
    "guilin,china": (110.296390, 25.280220),
    "zhaoqing,china": (112.460910, 23.048930),
    "mianyang,china": (104.681680, 31.467840),
    "wanzhou,china": (108.395860, 30.764510),
    "putian,china": (119.010280, 25.439440),
    "shangqiu,china": (115.650000, 34.450000),
    "san antonio,usa": (-98.493630, 29.424120),
    "yinchuan,china": (106.273060, 38.468060),
    "manhattan,usa": (-73.966250, 40.783430),
    "yiwu,china": (120.076760, 29.315060),
    "quanzhou,china": (118.585830, 24.913890),
    "jinhua,china": (119.644210, 29.106780),
    "cixi,china": (121.245700, 30.176400),
    "changde,china": (111.698440, 29.032050),
    "kaifeng,china": (114.307420, 34.798600),
    "anshan,china": (122.990000, 41.123610),
    "baoji,china": (107.237050, 34.367750),
    "suqian,china": (118.295830, 33.949170),
    "liuzhou,china": (109.406980, 24.324050),
    "zhangjiagang,china": (120.538890, 31.865000),
    "jinjiang,china": (118.574150, 24.819780),
    "bozhou,china": (115.770280, 33.877220),
    "qujing,china": (103.783330, 25.483330),
    "san diego,usa": (-117.164720, 32.715710),
    "zhanjiang,china": (110.387490, 21.233910),
    "fushun,china": (123.943630, 41.886690),
    "luoyang,china": (112.436840, 34.673450),
    "the bronx,usa": (-73.866410, 40.849850),
    "guankou,china": (113.627090, 28.158610),
    "handan,china": (114.487640, 36.609990),
    "yichang,china": (111.284720, 30.714440),
    "heze,china": (115.473580, 35.239290),
    "dallas,usa": (-96.806670, 32.783060),
    "liupanshui,china": (104.833330, 26.594440),
    "maoming,china": (110.913640, 21.666250),
    "qinzhou,china": (108.650610, 21.982470),
    "luohe,china": (114.042720, 33.563940),
    "xiangyang,china": (112.144790, 32.042200),
    "yangjiang,china": (111.962720, 21.855630),
    "yixing,china": (119.820160, 31.360590),
    "xuchang,china": (113.862990, 34.031890),
    "zigong,china": (104.776890, 29.341620),
    "xuzhou,china": (117.283860, 34.204420),
    "neijiang,china": (105.062160, 29.583540),
    "heshan,china": (112.347330, 28.569380),
    "jining,china": (116.581390, 35.405000),
    "xinyang,china": (114.065560, 32.122780),
    "liaocheng,china": (116.002470, 36.450640),
    "jinzhong,china": (112.754710, 37.684030),
    "changzhi,china": (113.105280, 36.183890),
    "tianshui,china": (105.742380, 34.579520),
    "weinan,china": (109.508910, 34.503550),
    "hong kong island,china": (114.184190, 22.263020),
    "jiaxing,china": (120.750000, 30.752200),
    "jiujiang,china": (116.002060, 29.704750),
    "birmingham,uk": (-1.899830, 52.481420),
    "anyang,china": (114.382780, 36.096000),
    "luohu district,china": (114.131490, 22.547210),
    "bijie,china": (105.286270, 27.301930),
    "zhuzhou,china": (113.150000, 27.833330),
    "shangrao,china": (117.942870, 28.451790),
    "huaibei,china": (116.791670, 33.974440),
    "meishan,china": (103.836960, 30.043920),
    "guigang,china": (109.594720, 23.116030),
    "hengyang,china": (112.618880, 26.889460),
    "yulin,china": (110.146860, 22.630500),
    "jingzhou,china": (112.190280, 30.350280),
    "xinxiang,china": (113.801510, 35.190330),
    "yichun,china": (114.400000, 27.833330),
    "xianyang,china": (108.702610, 34.337780),
    "sanya,china": (109.509470, 18.254350),
    "shaoguan,china": (113.583330, 24.800000),
    "longyan,china": (117.017750, 25.074850),
    "yongzhou,china": (111.613060, 26.423890),
    "huzhou,china": (120.093300, 30.870300),
    "wuwei,china": (102.632020, 37.926720),
    "jacksonville,usa": (-81.655650, 30.332180),
    "fort worth,usa": (-97.320850, 32.725410),
    "hanzhong,china": (107.022140, 33.075070),
    "hezhou,china": (111.566750, 24.403570),
    "zhu cheng city,china": (119.402590, 35.995020),
    "dongying,china": (118.491650, 37.462710),
    "luzhou,china": (105.425750, 28.890300),
    "san jose,usa": (-121.894960, 37.339390),
    "meizhou,china": (116.117680, 24.288590),
    "yueyang,china": (113.094810, 29.374550),
    "laiwu,china": (117.656940, 36.192780),
    "benxi,china": (123.765000, 41.288610),
    "pingdingshan,china": (113.315540, 33.730910),
    "austin,usa": (-97.743060, 30.267150),
    "bengbu,china": (117.360830, 32.940830),
    "sanhe,china": (117.068870, 39.980490),
    "xiangtan,china": (112.900000, 27.850000),
    "linfen,china": (111.518890, 36.088890),
    "victoria,china": (114.144170, 22.287500),
    "zhenjiang,china": (119.455080, 32.210860),
    "huludao,china": (120.835520, 40.752430),
    "baoshan,china": (99.163660, 25.116260),
    "rui'an,china": (120.658590, 27.776050),
    "columbus,usa": (-82.998790, 39.961180),
    "charlotte,usa": (-80.843130, 35.227090),
    "laibin,china": (109.222220, 23.747430),
    "xiaogan,china": (113.922210, 30.926890),
    "ziyang,china": (104.648110, 30.121080),
    "quzhou,china": (118.868610, 28.959440),
    "zaozhuang,china": (117.554170, 34.864720),
    "pingxiang,china": (113.853530, 27.616720),
    "indianapolis,usa": (-86.158040, 39.768380),
    "zhoushan,china": (122.204880, 29.988690),
    "qiqihar,china": (123.961540, 47.339220),
    "puning,china": (116.168690, 23.310720),
    "ankang,china": (109.017220, 32.680000),
    "langfang,china": (116.714710, 39.520790),
    "jiaozuo,china": (113.239140, 35.239250),
    "wanxian,china": (108.374070, 30.816010),
    "guang'an,china": (106.636960, 30.474130),
    "weihai,china": (122.113560, 37.509140),
    "zhabei,china": (121.459720, 31.258610),
    "xinyu,china": (114.933350, 27.804290),
    "yibin,china": (104.639940, 28.759300),
    "taicang,china": (121.093890, 31.447780),
    "san francisco,usa": (-122.419420, 37.774930),
    "chenzhou,china": (113.033330, 25.800000),
    "anqing,china": (117.047230, 30.513650),
    "xingtai,china": (114.492720, 37.062170),
    "zhaotong,china": (103.716670, 27.316670),
    "panzhihua,china": (101.712760, 26.585090),
    "chuzhou,china": (118.297780, 32.321940),
    "seattle,usa": (-122.332070, 47.606210),
    "xuancheng,china": (118.755280, 30.952500),
    "shangyu,china": (120.871110, 30.015560),
    "anshun,china": (105.933330, 26.250000),
    "wuzhou,china": (111.288480, 23.480540),
    "qinhuangdao,china": (119.589360, 39.941040),
    "shaoyang,china": (111.462140, 27.238180),
    "hegang,china": (130.290330, 47.347270),
    "ma'anshan,china": (118.510080, 31.685790),
    "shizuishan,china": (106.389200, 38.980820),
    "deyang,china": (104.381980, 31.130190),
    "yangquan,china": (113.563330, 37.857500),
    "denver,usa": (-104.984700, 39.739150),
    "zhumadian,china": (114.029440, 32.979440),
    "zhangjiakou,china": (114.871390, 40.783410),
    "washington,usa": (-77.036370, 38.895110),
    "nashville,usa": (-86.784440, 36.165890),
    "fuxin,china": (121.658890, 42.015560),
    "huangshi,china": (115.048140, 30.247060),
    "liaoyang,china": (123.173060, 41.271940),
    "baise,china": (106.626840, 23.890130),
    "binzhou,china": (118.016670, 37.366670),
    "oklahoma city,usa": (-97.516430, 35.467560),
    "yuncheng,china": (110.992780, 35.023060),
    "dezhou,china": (116.367060, 37.446610),
    "el paso,usa": (-106.486930, 31.758720),
    "sanmenxia,china": (111.192870, 34.780810),
    "e'zhou,china": (114.886550, 30.396070),
    "mudanjiang,china": (129.625940, 44.548040),
    "leshan,china": (103.763860, 29.562270),
    "rizhao,china": (119.529080, 35.414140),
    "suining,china": (105.573320, 30.508020),
    "boston,usa": (-71.059770, 42.358430),
    "portland,usa": (-122.676210, 45.523450),
    "macau,china": (113.546110, 22.200560),
    "detroit,usa": (-83.045750, 42.331430),
    "las vegas,usa": (-115.137220, 36.174970),
    "new south memphis,usa": (-90.056760, 35.086760),
    "hebi,china": (114.286160, 35.732310),
    "memphis,usa": (-90.048980, 35.149530),
    "jingmen,china": (112.204720, 31.033610),
    "dandong,china": (124.394720, 40.129170),
    "glasgow,uk": (-4.257630, 55.865150),
    "panshan,china": (122.049440, 41.188060),
    "louisville,usa": (-85.759410, 38.254240),
    "jiaozhou,china": (120.003330, 36.283890),
    "suizhou,china": (113.363060, 31.711110),
    "chizhou,china": (117.477830, 30.661340),
    "ya'an,china": (102.999000, 29.985210),
    "jinzhou,china": (121.141670, 41.107780),
    "sanming,china": (117.618610, 26.248610),
    "shuangyashan,china": (131.132730, 46.676860),
    "luancheng,china": (114.646290, 37.884520),
    "mengzi,china": (103.382120, 23.367790),
    "yingkou,china": (122.231760, 40.664720),
    "zhangzhou,china": (117.655560, 24.513330),
    "baltimore,usa": (-76.612190, 39.290380),
    "shihezi,china": (86.036940, 44.302300),
    "south boston,usa": (-71.049490, 42.333430),
    "manchester,uk": (-2.237430, 53.480950),
    "albuquerque,usa": (-106.651140, 35.084490),
    "milwaukee,usa": (-87.906470, 43.038900),
    "wenchang,china": (110.802790, 19.551580),
    "sheffield,uk": (-1.465900, 53.382970),
    "siping,china": (124.377850, 43.161430),
    "chuxiong,china": (101.545560, 25.036390),
    "huaihua,china": (110.004040, 27.563370),
    "banqiao,taiwan": (121.467190, 25.014270),
    "ulanqab,china": (113.133000, 40.993000),
    "jiamusi,china": (130.311180, 46.797110),
    "korla,china": (86.152310, 41.760550),
    "wanning,china": (110.384100, 18.799310),
    "xinzhou,china": (112.733330, 38.409170),
    "tucson,usa": (-110.926480, 32.221740),
    "pingdu,china": (119.946390, 36.784440),
    "fresno,usa": (-119.772370, 36.747730),
    "ji'an,china": (114.979270, 27.117160),
    "leeds,uk": (-1.547850, 53.796480),
    "guli,china": (120.033080, 28.881620),
    "aqsu,china": (80.279210, 41.184180),
    "tanggu,china": (117.646940, 39.021110),
    "shangluo,china": (109.930560, 33.866670),
    "qionghai,china": (110.464170, 19.242500),
    "cangzhou,china": (116.853340, 38.311240),
    "beihai,china": (109.115490, 21.483490),
    "sacramento,usa": (-121.494400, 38.581570),
    "hengshui,china": (115.683480, 37.739080),
    "guangyuan,china": (105.823000, 32.442010),
    "edinburgh,uk": (-3.196480, 55.952060),
    "xianning,china": (114.322010, 29.843470),
    "atlanta,usa": (-84.387980, 33.749000),
    "tonghua,china": (125.926390, 41.719720),
    "mianzhu, deyang, sichuan,china": (104.220570, 31.337860),
    "banan,china": (106.540000, 29.378610),
    "tuen mun,china": (113.971570, 22.391750),
    "zhangye,china": (100.451670, 38.934170),
    "kashgar,china": (75.986750, 39.467180),
    "zhoukou,china": (114.633330, 33.633330),
    "pingliang,china": (106.686110, 35.539170),
    "zhucheng,china": (119.397500, 35.994720),
    "loudi,china": (111.994440, 27.734440),
    "liverpool,uk": (-2.977940, 53.410580),
    "sha tin,china": (114.183330, 22.383330),
    "shanwei,china": (115.347500, 22.781990),
    "jianshui,china": (101.224000, 24.277400),
    "miami,usa": (-80.193660, 25.774270),
    "omaha,usa": (-95.940430, 41.256260),
    "raleigh,usa": (-78.638610, 35.772100),
    "xichang,china": (102.263410, 27.896420),
    "bristol,uk": (-2.596650, 51.455230),
    "chengguan qu,china": (91.044410, 29.638420),
    "jincheng,china": (112.832780, 35.502220),
    "taoyuan,taiwan": (121.318700, 24.989600),
    "kansas city,usa": (-94.578570, 39.099730),
    "yan'an,china": (109.491670, 36.598890),
    "long beach,usa": (-118.189230, 33.766960),
    "shouguang,china": (118.737500, 36.880000),
    "jingdezhen,china": (117.207890, 29.294700),
    "mesa,usa": (-111.822640, 33.422270),
    "jiaojiang,china": (121.473310, 28.698440),
    "staten island,usa": (-74.139860, 40.562330),
    "nanping,china": (118.173610, 26.645000),
    "longshan,china": (125.136700, 42.885450),
    "heyuan,china": (114.683330, 23.733330),
    "huangshan,china": (118.312500, 29.711390),
    "colorado springs,usa": (-104.821360, 38.833880),
    "virginia beach,usa": (-75.977990, 36.852930),
    "hsinchu,taiwan": (120.968610, 24.803610),
    "lishui,china": (119.910290, 28.460420),
    "wenshan city,china": (104.250470, 23.363060),
    "chengde,china": (117.958830, 40.951900),
    "basuo,china": (108.665650, 19.102670),
    "zhangjiajie,china": (110.478330, 29.129440),
    "bei'an,china": (126.600000, 48.266670),
    "sham shui po,china": (114.159450, 22.330230),
    "ningde,china": (119.522780, 26.661670),
    "jiuquan,china": (98.517360, 39.743180),
    "wong tai sin,china": (114.183330, 22.350000),
    "dingxi,china": (104.623030, 35.570880),
    "oakland,usa": (-122.270800, 37.804370),
    "kowloon city,china": (114.192220, 22.330470),
    "tongchuan,china": (108.950560, 34.898800),
    "tampa,usa": (-82.458430, 27.947520),
    "tulsa,usa": (-95.992770, 36.153980),
    "tseung kwan o,china": (114.249920, 22.327890),
    "guyuan,china": (106.280830, 36.006670),
    "minneapolis,usa": (-93.263840, 44.979970),
    "chaoyang,china": (120.458610, 41.570280),
    "gujangbagh,china": (79.934330, 37.109270),
    "jixi,china": (130.962170, 45.293220),
    "tongling,china": (117.783330, 30.950000),
    "taoyuan city,taiwan": (121.296960, 24.993680),
    "wichita,usa": (-97.337540, 37.692240),
    "gaomi,china": (119.752780, 36.383330),
    "arlington,usa": (-97.108070, 32.735690),
    "chongzuo,china": (107.368300, 22.381610),
    "tanzhou,china": (113.466920, 22.255030),
    "hechuan,china": (106.264610, 29.992280),
    "bakersfield,usa": (-119.018710, 35.373290),
    "xuanhua,china": (115.064630, 40.612050),
    "cardiff,uk": (-3.180000, 51.480000),
    "fenghuang,china": (109.599610, 27.935570),
    "leicester,uk": (-1.131690, 52.638600),
    "huanggang,china": (114.870350, 30.451430),
    "bradford,uk": (-1.752060, 53.793910),
    "cleveland,usa": (-81.695410, 41.499500),
    "anqiu,china": (119.192500, 36.434170),
    "new orleans,usa": (-90.075070, 29.954650),
    "keelung,taiwan": (121.740940, 25.130890),
    "jizhou,china": (115.568710, 37.550540),
    "huocheng,china": (80.871730, 44.053050),
    "aurora,usa": (-104.831920, 39.729430),
    "fengshan,taiwan": (120.361260, 22.626590),
    "lhoka,china": (91.772390, 29.243010),
    "honolulu,usa": (-157.858330, 21.306940),
    "anaheim,usa": (-117.914500, 33.835290),
    "pengze,china": (116.545720, 29.898850),
    "xilinhot,china": (116.070210, 43.938890),
    "hulunbuir,china": (119.755820, 49.211410),
    "belfast,uk": (-5.925410, 54.596820),
    "daye,china": (114.950000, 30.083330),
    "chifeng,china": (118.963610, 42.268330),
    "yunlong,china": (117.251670, 34.252810),
    "coventry,uk": (-1.512170, 52.406560),
    "qitaihe,china": (130.995300, 45.768000),
    "pizhou,china": (117.950280, 34.311390),
    "shiqi,china": (113.385210, 22.516820),
    "laixi,china": (120.526940, 36.859170),
    "west raleigh,usa": (-78.663890, 35.786820),
    "orlando,usa": (-81.379240, 28.538340),
    "tieling,china": (123.841390, 42.293060),
    "kwai chung,china": (114.138770, 22.368280),
    "hechi,china": (108.083760, 24.692850),
    "tongshan,china": (117.157070, 34.180450),
    "brent,uk": (-0.302300, 51.553060),
    "yanji,china": (129.502410, 42.888250),
    "birkenhead,uk": (-3.014790, 53.393370),
    "lincang,china": (100.094550, 23.879720),
    "nottingham,uk": (-1.150470, 52.953600),
    "xingyi,china": (104.906390, 25.096170),
    "lexington,usa": (-84.477720, 37.988690),
    "tantou,china": (113.834960, 22.751210),
    "islington,uk": (-0.103040, 51.536220),
    "tsuen wan,china": (114.113290, 22.371370),
    "reading,uk": (-0.971130, 51.456250),
    "riverside,usa": (-117.396160, 33.953350),
    "baicheng,china": (122.833020, 45.617510),
    "corpus christi,usa": (-97.396380, 27.800580),
    "lexington-fayette,usa": (-84.458550, 38.049800),
    "kingston upon hull,uk": (-0.335250, 53.744600),
    "preston,uk": (-2.704520, 53.762820),
    "lianshan,china": (120.853270, 40.764320),
    "cincinnati,usa": (-84.514390, 39.127110),
    "santa ana,usa": (-117.867830, 33.745570),
    "stockton,usa": (-121.290780, 37.957700),
    "pittsburgh,usa": (-79.995890, 40.440620),
    "saint paul,usa": (-93.093270, 44.944410),
    "changyi,china": (119.390830, 36.853610),
    "xinyi,china": (118.346170, 34.384240),
    "swansea,uk": (-3.943230, 51.620790),
    "newcastle upon tyne,uk": (-1.613960, 54.973280),
    "yangshuo,china": (110.489670, 24.780810),
    "linqu,china": (118.539720, 36.515560),
    "simao,china": (100.974810, 22.788630),
    "southend-on-sea,uk": (0.714330, 51.537820),
    "lincoln,usa": (-96.666960, 40.800000),
    "baiyin,china": (104.170230, 36.546960),
    "gaozhou,china": (110.856780, 21.919650),
    "xiuying,china": (110.293590, 20.000730),
    "anchorage,usa": (-149.900280, 61.218060),
    "ironville,usa": (-82.692380, 38.456470),
    "meads,usa": (-82.709050, 38.412580),
    "henderson,usa": (-114.981940, 36.039700),
    "greensboro,usa": (-79.791980, 36.072640),
    "dengzhou,china": (112.081940, 32.682220),
    "artux,china": (76.179710, 39.708420),
    "plano,usa": (-96.698890, 33.019840),
    "xinyuan,china": (83.249590, 43.426490),
    "tin shui wai,china": (114.002340, 22.456790),
    "newark,usa": (-74.172370, 40.735660),
    "madison,usa": (-89.401230, 43.073050),
    "st. louis,usa": (-90.197890, 38.627270),
    "enshi,china": (109.483330, 30.300000),
    "binhe,china": (112.827500, 32.688330),
    "zoucheng,china": (116.965560, 35.400560),
    "brighton,uk": (-0.139470, 50.828380),
    "ulu bedok,singapore": (103.933330, 1.333330),
    "bedok new town,singapore": (103.941670, 1.326390),
    "fangchenggang,china": (108.356610, 21.769450),
    "kaili,china": (107.979720, 26.585830),
    "neihu,taiwan": (121.588090, 25.081500),
    "xingning,china": (115.722720, 24.148300),
    "linxia chengguanzhen,china": (103.206390, 35.600280),
    "tai po,china": (114.168770, 22.450070),
    "turpan,china": (89.178860, 42.947690),
    "derby,uk": (-1.476630, 52.922770),
    "longling county,china": (98.689340, 24.586630),
    "southampton,uk": (-1.404280, 50.903950),
    "ghulja,china": (81.321510, 43.915150),
    "fuling,china": (107.393910, 29.709970),
    "chengzhong,china": (113.552840, 30.944540),
    "chula vista,usa": (-117.084200, 32.640050),
    "toledo,usa": (-83.555210, 41.663940),
    "hulan ergi,china": (123.633330, 47.204170),
    "tampines estate,singapore": (103.940280, 1.358060),
    "donghai,china": (115.642040, 22.945930),
    "jersey city,usa": (-74.077640, 40.728160),
    "reno,usa": (-119.813800, 39.529630),
    "wolverhampton,uk": (-2.122960, 52.585470),
    "fanling,china": (114.139490, 22.494870),
    "chiayi city,taiwan": (120.448890, 23.479170),
    "dongtai,china": (120.309470, 32.852310),
    "jurong town,singapore": (103.722780, 1.334170),
    "karamay,china": (84.887240, 45.584730),
    "tongliao,china": (122.265280, 43.612500),
    "chandler,usa": (-111.841250, 33.306160),
    "fort wayne,usa": (-85.128860, 41.130600),
    "plymouth,uk": (-4.143050, 50.371530),
    "nianbo,china": (102.416390, 36.480000),
    "tampines new town,singapore": (103.949720, 1.349170),
    "changle,china": (118.827500, 36.705830),
    "stoke-on-trent,uk": (-2.185380, 53.004150),
    "buffalo,usa": (-78.878370, 42.886450),
    "durham,usa": (-78.898620, 35.994030),
    "jurong west,singapore": (103.722780, 1.350280),
    "rugao,china": (120.576490, 32.370350),
    "st. petersburg,usa": (-82.679270, 27.770860),
    "irvine,usa": (-117.823110, 33.669460),
    "suicheng,china": (117.933070, 33.896300),
    "nada,china": (109.578950, 19.521340),
    "milton keynes,uk": (-0.755830, 52.041720),
    "laredo,usa": (-99.507540, 27.506410),
    "woodlands,singapore": (103.788770, 1.438010),
    "yanzhou,china": (116.828610, 35.552780),
    "laohekou,china": (111.667780, 32.385830),
    "suihua,china": (126.966560, 46.648140),
    "wafangdian,china": (122.008060, 39.618330),
    "lubbock,usa": (-101.855170, 33.577860),
    "beibei,china": (106.436450, 29.827390),
    "city of westminster,uk": (-0.135700, 51.497500),
    "gilbert,usa": (-111.789030, 33.352830),
    "shijie,china": (113.791950, 23.095460),
    "hami,china": (93.506010, 42.833930),
    "northampton,uk": (-0.883330, 52.250000),
    "sengkang new town,singapore": (103.894440, 1.391670),
    "tri-cities,usa": (-119.196170, 46.245400),
    "huayin,china": (110.066390, 34.565280),
    "jiyuan,china": (112.588150, 35.089120),
    "winston-salem,usa": (-80.244220, 36.099860),
    "glendale,usa": (-112.185990, 33.538650),
    "xiantao,china": (113.442940, 30.370800),
    "norfolk,usa": (-76.285220, 36.846810),
    "oldham,uk": (-2.118300, 53.540510),
    "hialeah,usa": (-80.278110, 25.857600),
    "garland,usa": (-96.638880, 32.912620),
    "scottsdale,usa": (-111.899030, 33.509210),
    "irving,usa": (-96.948890, 32.814020),
    "qingzhou,china": (118.479720, 36.696670),
    "yuci,china": (112.731940, 37.680280),
    "boise,usa": (-116.203450, 43.613500),
    "bole,china": (82.069930, 44.893340),
    "chesapeake,usa": (-76.274940, 36.819040),
    "dali,china": (100.212290, 25.584740),
    "north las vegas,usa": (-115.117500, 36.198860),
    "yongkang,taiwan": (120.255560, 23.024440),
    "fremont,usa": (-121.988570, 37.548270),
    "jiayuguan,china": (98.286180, 39.811210),
    "changzheng,china": (121.367790, 31.239130),
    "spokane,usa": (-117.429080, 47.659660),
    "jinchang,china": (102.193790, 38.500620),
    "bexley,uk": (0.148660, 51.441620),
    "hougang new town,singapore": (103.890830, 1.356670),
    "baton rouge,usa": (-91.187470, 30.443320),
    "upper west side,usa": (-73.975420, 40.787050),
    "richmond,usa": (-77.460260, 37.553760),
    "chang-hua,taiwan": (120.562760, 24.073270),
    "changhua,taiwan": (120.551200, 24.069200),
    "fendou,china": (124.862830, 46.641420),
    "luton,uk": (-0.417480, 51.879670),
    "jingling,china": (113.100000, 30.650000),
    "heihe,china": (127.490160, 50.244130),
    "tongchuanshi,china": (109.084950, 35.074740),
    "paradise,usa": (-115.146660, 36.097190),
    "tacoma,usa": (-122.444290, 47.252880),
    "xintai,china": (117.751940, 35.900560),
    "yishun new town,singapore": (103.831110, 1.433330),
    "wuxue,china": (115.552500, 29.850580),
    "wuhai,china": (106.815830, 39.684420),
    "yintai,china": (109.097020, 35.115240),
    "jamaica,usa": (-73.805690, 40.691490),
    "san bernardino,usa": (-117.289770, 34.108340),
    "archway,uk": (-0.134150, 51.567330),
    "salt lake city,usa": (-111.891050, 40.760780),
    "longgang,china": (114.263260, 22.722890),
    "ma on shan,china": (114.240790, 22.406130),
    "huntsville,usa": (-86.585940, 34.730400),
    "yingtan,china": (117.000000, 28.233330),
    "des moines,usa": (-93.609110, 41.600540),
    "zitong,china": (105.829910, 30.178200),
    "fontana,usa": (-117.435050, 34.092230),
    "zhubei,taiwan": (121.007780, 24.838330),
    "luojiang,china": (104.504840, 31.304970),
    "modesto,usa": (-120.996880, 37.639100),
    "lijiang,china": (100.220720, 26.868790),
    "hailar,china": (119.700000, 49.200000),
    "daliang,china": (113.250300, 22.840670),
    "rochester,usa": (-77.615560, 43.154780),
    "bade,taiwan": (121.283720, 24.929810),
    "bachuan,china": (106.050460, 29.848630),
    "hangu,china": (117.789170, 39.248890),
    "maryvale,usa": (-112.177650, 33.501990),
    "portsmouth,uk": (-1.091250, 50.798990),
    "gunan,china": (106.648000, 29.023100),
    "oxnard,usa": (-119.177050, 34.197500),
    "worcester,usa": (-71.802290, 42.262590),
    "jinghong,china": (100.769700, 22.002650),
    "gongheyong,china": (113.794520, 22.759230),
    "nanchuan,china": (107.103350, 29.152010),
    "bishan,china": (106.224760, 29.594910),
    "xizhi,taiwan": (121.659850, 25.066150),
    "gaoping,china": (106.102940, 30.775760),
    "moreno valley,usa": (-117.230590, 33.937520),
    "little rock,usa": (-92.289590, 34.746480),
    "fayetteville,usa": (-78.878360, 35.052660),
    "huntington beach,usa": (-117.999230, 33.660300),
    "tallahassee,usa": (-84.280730, 30.438260),
    "swindon,uk": (-1.781160, 51.557970),
    "yonkers,usa": (-73.897890, 40.930400),
    "cypress,usa": (-95.697170, 29.969110),
    "nyingchi,china": (94.355090, 29.648850),
    "yuen long san hui,china": (114.033330, 22.433330),
    "yuen long,china": (114.026210, 22.445180),
    "beiliu,china": (110.349170, 22.707220),
    "punggol,singapore": (103.906940, 1.414440),
    "dudley,uk": (-2.083330, 52.500000),
    "changji,china": (87.304610, 44.007820),
    "amarillo,usa": (-101.831300, 35.222000),
    "aberdeen,uk": (-2.098140, 57.143690),
    "duyun,china": (107.516670, 26.266670),
    "kaiyuan,china": (103.303720, 23.697670),
    "mentougou,china": (116.093070, 39.938190),
    "akron,usa": (-81.519010, 41.081440),
    "lushui,china": (98.858530, 25.823200),
    "jijiang,china": (106.250010, 29.289930),
    "hanfeng,china": (108.403100, 31.169460),
    "vancouver,usa": (-122.661490, 45.638730),
    "birmingham,usa": (-86.802490, 33.520660),
    "peicheng,china": (116.924720, 34.736110),
    "montgomery,usa": (-86.299970, 32.366810),
    "grand rapids,usa": (-85.668090, 42.963360),
    "kowloon city centre,china": (114.188890, 22.329790),
    "ezhou,china": (114.833330, 30.400000),
    "zhengding,china": (114.565560, 38.145010),
    "yongchuan,china": (105.893920, 29.353760),
    "hepu,china": (109.200110, 21.659210),
    "aihui,china": (127.481190, 49.979460),
    "fuding,china": (120.213990, 27.327340),
    "humen,china": (113.673060, 22.818990),
    "haicheng,china": (122.747540, 40.851580),
    "peoria,usa": (-112.237380, 33.580600),
    "providence,usa": (-71.412830, 41.823990),
    "choa chu kang new town,singapore": (103.749720, 1.382500),
    "knoxville,usa": (-83.920740, 35.960640),
    "jinshanlu,china": (88.132860, 47.850500),
    "sunrise manor,usa": (-115.073060, 36.211080),
    "danshui,taiwan": (121.442900, 25.171960),
    "guixi,china": (107.345450, 30.333550),
    "laizhou,china": (119.942170, 37.180730),
    "grand prairie,usa": (-96.997780, 32.745960),
    "sutton,uk": (-0.200000, 51.350000),
    "shreveport,usa": (-93.750180, 32.525150),
    "huixing,china": (106.614860, 29.684030),
    "brownsville,usa": (-97.497480, 25.901750),
    "changyuan,china": (105.588270, 29.404990),
    "overland park,usa": (-94.670790, 38.982230),
    "shangri-la,china": (99.707790, 27.825110),
    "newport news,usa": (-76.429750, 36.980380),
    "yangcheng,china": (106.256040, 29.999680),
    "dunhuang,china": (94.683330, 40.166670),
    "zaoyang,china": (112.754170, 32.127220),
    "baishan,china": (126.419650, 41.938530),
    "mobile,usa": (-88.043050, 30.694360),
    "st helens,uk": (-2.733330, 53.450000),
    "fort lauderdale,usa": (-80.143380, 26.122310),
    "santa clarita,usa": (-118.542590, 34.391660),
    "tsing yi town,china": (114.100000, 22.350000),
    "zhenping chengguanzhen,china": (112.233210, 33.033140),
    "anda,china": (125.301610, 46.448670),
    "chattanooga,usa": (-85.309680, 35.045630),
    "crawley,uk": (-0.183120, 51.113030),
    "shulin,taiwan": (121.421990, 24.990850),
    "pingwu county,china": (104.527380, 32.407320),
    "qianjiang,china": (112.891900, 30.421000),
    "ipswich,uk": (1.155450, 52.059170),
    "east flatbush,usa": (-73.930420, 40.653710),
    "spring valley,usa": (-115.245000, 36.108030),
    "santa rosa,usa": (-122.714430, 38.440470),
    "eugene,usa": (-123.086750, 44.052070),
    "zhenzhou,china": (119.169990, 32.280340),
    "tempe,usa": (-111.909310, 33.414770),
    "xindi,china": (113.466670, 29.816670),
    "oceanside,usa": (-117.379480, 33.195870),
    "fengcheng,china": (107.060190, 29.825870),
    "salem,usa": (-123.035100, 44.942900),
    "wigan,uk": (-2.637060, 53.542960),
    "garden grove,usa": (-117.941450, 33.773910),
    "rancho cucamonga,usa": (-117.593110, 34.106400),
    "cape coral,usa": (-81.949530, 26.562850),
    "jiutai,china": (125.832780, 44.152500),
    "croydon,uk": (-0.100000, 51.383330),
    "east new york,usa": (-73.882360, 40.666770),
    "licheng,china": (113.824650, 23.295490),
    "warrington,uk": (-2.580240, 53.392540),
    "walsall,uk": (-1.983960, 52.585280),
    "mansfield,uk": (-1.200000, 53.133330),
    "sioux falls,usa": (-96.727960, 43.543690),
    "dongling,china": (123.575830, 41.814440),
    "ontario,usa": (-117.650890, 34.063340),
    "fort collins,usa": (-105.084420, 40.585260),
    "springfield,usa": (-93.298240, 37.215330),
    "sunderland,uk": (-1.382220, 54.904650),
    "yuen long kau hui,china": (114.031990, 22.448310),
    "laiyang,china": (120.713610, 36.975830),
    "ilford,uk": (0.072780, 51.557650),
    "hollywood,usa": (-118.326740, 34.098340),
    "elk grove,usa": (-121.371620, 38.408800),
    "clarksville,usa": (-87.359450, 36.529770),
    "wan chai,china": (114.172580, 22.281420),
    "pembroke pines,usa": (-80.223940, 26.003150),
    "ulanhot,china": (122.083330, 46.083330),
    "songcheng,china": (120.001110, 26.881940),
    "deer valley,usa": (-112.134880, 33.683930),
    "murfreesboro,usa": (-86.390270, 35.845620),
    "hengshan,china": (130.898080, 45.208370),
    "slough,uk": (-0.595410, 51.509490),
    "port saint lucie,usa": (-80.350330, 27.293930),
    "corona,usa": (-117.566440, 33.875290),
    "bournemouth,uk": (-1.879500, 50.720480),
    "peterborough,uk": (-0.247770, 52.573640),
    "tongzhou,china": (116.661830, 39.903950),
    "anbu,china": (116.680920, 23.448950),
    "mckinney,usa": (-96.615270, 33.197620),
    "ning'er,china": (101.036830, 23.040530),
    "oxford,uk": (-1.255960, 51.752220),
    "newport,uk": (-2.998350, 51.587740),
    "lancaster,usa": (-118.136740, 34.698040),
    "tacheng,china": (82.958470, 46.745350),
    "cary,usa": (-78.781120, 35.791540),
    "alexandria,usa": (-77.046920, 38.804840),
    "zhicheng,china": (111.504720, 30.295560),
    "ang mo kio new town,singapore": (103.839720, 1.380280),
    "tempe junction,usa": (-111.943480, 33.414210),
    "palmdale,usa": (-118.116460, 34.579430),
    "hayward,usa": (-122.080800, 37.668820),
    "bukit batok new town,singapore": (103.763680, 1.359030),
    "aberdeen,china": (114.152890, 22.248020),
    "salinas,usa": (-121.655500, 36.677740),
    "nanpiao,china": (120.747920, 41.098220),
    "enfield town,uk": (-0.084970, 51.651470),
    "lizhi,china": (107.395210, 29.703170),
    "york,uk": (-1.082710, 53.957630),
    "yizhou,china": (108.666670, 24.500000),
    "sunnyvale,usa": (-122.036350, 37.368830),
    "telford,uk": (-2.449260, 52.676590),
    "lianghu,china": (120.898450, 29.991520),
    "beipiao,china": (120.779170, 41.791940),
    "guangshui,china": (113.997800, 31.619900),
    "fu'an,china": (119.644460, 27.091310),
    "frisco,usa": (-96.823610, 33.150670),
    "zhaodong,china": (125.955200, 46.052230),
    "wujiaqu,china": (87.521740, 44.162790),
    "east chattanooga,usa": (-85.249120, 35.065350),
    "pasadena,usa": (-95.209100, 29.691060),
    "sanshui,china": (112.891610, 23.154860),
    "jackson,usa": (-90.184810, 32.298760),
    "boshan,china": (117.833330, 36.483330),
    "yangchun,china": (111.783330, 22.166670),
    "pomona,usa": (-117.752280, 34.055290),
    "dingzhou,china": (114.986800, 38.514730),
    "pengpu,china": (121.436700, 31.285500),
    "washington heights,usa": (-73.935410, 40.850100),
    "lakewood,usa": (-105.081370, 39.704710),
    "chenghua,china": (116.770070, 23.461320),
    "longfeng,china": (125.103800, 46.531680),
    "bukit merah estate,singapore": (103.823060, 1.284170),
    "escondido,usa": (-117.086420, 33.119210),
    "astoria,usa": (-73.930140, 40.772050),
    "poole,uk": (-1.984580, 50.714290),
    "burnley,uk": (-2.233330, 53.800000),
    "borough park,usa": (-73.996810, 40.633990),
    "harrow,uk": (-0.332080, 51.578350),
    "huddersfield,uk": (-1.784160, 53.649040),
    "dunhua,china": (128.228610, 43.369540),
    "valencia,usa": (-118.609530, 34.443610),
    "rockford,usa": (-89.094000, 42.271130),
    "dundee,uk": (-2.974890, 56.469130),
    "sujiatun,china": (123.339170, 41.659170),
    "east hampton,usa": (-76.331610, 37.037370),
    "honggang,china": (124.884470, 46.397400),
    "joliet,usa": (-88.083400, 41.525190),
    "savannah,usa": (-81.099830, 32.083540),
    "paterson,usa": (-74.171810, 40.916770),
    "bridgeport,usa": (-73.189450, 41.179230),
    "naperville,usa": (-88.147290, 41.785860),
    "taozhou,china": (119.408650, 30.906410),
    "blackburn,uk": (-2.483330, 53.750000),
    "xinji,china": (115.219070, 37.925950),
    "cambridge,uk": (0.116670, 52.200000),
    "taishan,china": (112.779900, 22.251350),
    "gainesville,usa": (-82.324830, 29.651630),
    "kampong pasir ris,singapore": (103.931940, 1.378330),
    "blackpool,uk": (-3.050000, 53.816670),
    "basildon,uk": (0.457820, 51.568440),
    "mesquite,usa": (-96.599160, 32.766800),
    "acheng,china": (126.951910, 45.545580),
    "hailin,china": (129.385390, 44.571490),
    "yong'an,china": (109.459490, 31.018940),
    "syracuse,usa": (-76.147420, 43.048120),
    "nanjin,china": (106.265290, 29.984970),
    "torrance,usa": (-118.340630, 33.835850),
    "surprise,usa": (-112.333220, 33.630590),
    "norwich,uk": (1.298340, 52.627830),
    "middlesbrough,uk": (-1.234830, 54.576230),
    "metairie terrace,usa": (-90.163960, 29.978540),
    "columbia,usa": (-81.034810, 34.000710),
    "jieshou,china": (115.361080, 33.263380),
    "bolton,uk": (-2.433330, 53.583330),
    "yushu,china": (97.008930, 33.001180),
    "orange,usa": (-117.853110, 33.787790),
    "gongzhuling,china": (124.819790, 43.500750),
    "fullerton,usa": (-117.925340, 33.870290),
    "killeen,usa": (-97.727800, 31.117120),
    "shuizhai,china": (115.764990, 23.929610),
    "mcallen,usa": (-98.230010, 26.203410),
    "shanhaiguan,china": (119.753950, 40.001190),
    "bellevue,usa": (-122.200680, 47.610380),
    "stockport,uk": (-2.157610, 53.409790),
    "huadian,china": (126.741070, 42.972130),
    "liuzhi,china": (105.426000, 26.234200),
    "fuyu,china": (124.816670, 45.183330),
    "metairie,usa": (-90.152850, 29.984090),
    "chaohu,china": (117.866670, 31.600000),
    "bukit panjang new town,singapore": (103.764720, 1.379720),
    "liangping,china": (107.766100, 30.661080),
    "doilungdeqen,china": (90.991770, 29.655050),
    "jieshi,china": (115.830580, 22.810270),
    "hejiang,china": (105.833590, 28.811610),
    "hampton,usa": (-76.345220, 37.029870),
    "wuyishan,china": (118.030660, 27.759950),
    "miramar,usa": (-80.232270, 25.987310),
    "jiashan,china": (120.925830, 30.849180),
    "huinong,china": (106.769440, 39.233330),
    "van nuys,usa": (-118.448970, 34.186670),
    "west valley city,usa": (-112.001050, 40.691610),
    "gejiu,china": (103.153720, 23.360850),
    "jiagedaqi,china": (124.116670, 50.416670),
    "tumxuk,china": (79.061180, 39.869840),
    "west bromwich,uk": (-1.994500, 52.518680),
    "dayton,usa": (-84.191610, 39.758950),
    "shiqiao,china": (113.357690, 22.946400),
    "olathe,usa": (-94.819130, 38.881400),
    "shenglilu,china": (105.877500, 29.350480),
    "warren,usa": (-83.013040, 42.490440),
    "jiawang,china": (117.441940, 34.432780),
    "thornton,usa": (-104.971920, 39.868040),
    "hastings,uk": (0.580090, 50.855680),
    "high wycombe,uk": (-0.749340, 51.629070),
    "carrollton,usa": (-96.890280, 32.953730),
    "puqi,china": (113.883330, 29.716670),
    "charleston,usa": (-79.932750, 32.776320),
    "midland,usa": (-102.077910, 31.997350),
    "wugang,china": (110.631980, 26.727900),
    "gloucester,uk": (-2.243100, 51.865680),
    "waco,usa": (-97.146670, 31.549330),
    "zhalantun,china": (122.736510, 48.009450),
    "sterling heights,usa": (-83.030200, 42.580310),
    "fuji,china": (105.373910, 29.148190),
    "dawukou,china": (106.395830, 39.041940),
    "majie,china": (102.638000, 25.031900),
    "hepo,china": (115.829910, 23.430770),
    "denton,usa": (-97.133070, 33.214840),
    "shangzhi,china": (128.002420, 45.205620),
    "shuangcheng,china": (126.307110, 45.379800),
    "exeter,uk": (-3.527510, 50.723600),
    "cedar rapids,usa": (-91.644070, 42.008330),
    "dongyang,china": (120.225280, 29.267780),
    "nantou,china": (113.292610, 22.721710),
    "new haven,usa": (-72.928160, 41.308150),
    "jiazi,china": (116.073180, 22.879320),
    "roseville,usa": (-121.288010, 38.752120),
    "kembangan,singapore": (103.911350, 1.322280),
    "songjiang,china": (121.223260, 31.034430),
    "visalia,usa": (-119.292060, 36.330230),
    "tottenham,uk": (-0.067940, 51.603730),
    "wuda,china": (106.711670, 39.499440),
    "santo antonio,china": (113.543940, 22.202080),
    "salford,uk": (-2.290420, 53.487710),
    "coral springs,usa": (-80.270600, 26.271190),
    "newcastle under lyme,uk": (-2.233330, 53.000000),
    "thousand oaks,usa": (-118.837590, 34.170560),
    "leiyang,china": (112.859080, 26.402380),
    "elizabeth,usa": (-74.210700, 40.663990),
    "stamford,usa": (-73.538730, 41.053430),
    "concord,usa": (-122.031070, 37.977980),
    "shuanglonghu,china": (106.606840, 29.716170),
    "shache,china": (77.240560, 38.416670),
    "norman,usa": (-97.439480, 35.222570),
    "alhambra,usa": (-112.134320, 33.498380),
    "athens,usa": (-83.377940, 33.960950),
    "jiangyou,china": (104.716670, 31.766670),
    "tengyue,china": (98.512760, 24.994920),
    "shajing,china": (113.819030, 22.746280),
    "jinfeng,china": (116.600540, 28.238500),
    "kent,usa": (-122.234840, 47.380930),
    "simi valley,usa": (-118.781480, 34.269450),
    "jingzhi,china": (119.387500, 36.310000),
    "danshui,china": (114.467160, 22.798400),
    "solihull,uk": (-1.780940, 52.414260),
    "east los angeles,usa": (-118.172020, 34.023900),
    "macheng,china": (115.022130, 31.180130),
    "ala'er,china": (81.265660, 40.541840),
    "santa clara,usa": (-121.955240, 37.354110),
    "nossa senhora de fatima,china": (113.548310, 22.207690),
    "sunset park,usa": (-74.012410, 40.645480),
    "topeka,usa": (-95.678040, 39.048330),
    "huicheng,china": (116.289880, 23.038450),
    "watford,uk": (-0.396020, 51.655310),
    "xiazhen,china": (117.111670, 34.802220),
    "haimen,china": (116.612190, 23.193460),
    "saint peters,uk": (1.416670, 51.366670),
    "abilene,usa": (-99.733140, 32.448740),
    "shahecheng,china": (114.505830, 36.938330),
    "yuanlin,taiwan": (120.576080, 23.956710),
    "koreatown,usa": (-118.300910, 34.057790),
    "lecheng,china": (113.350410, 25.128000),
    "nancun,china": (120.133890, 36.532780),
    "jiupu,china": (122.950000, 41.066670),
    "jiaohe,china": (127.334730, 43.721330),
    "huangzhou,china": (114.800000, 30.450000),
    "sheepshead bay,usa": (-73.944580, 40.591220),
    "xiulin,china": (112.400000, 29.716670),
    "zhoucun,china": (117.816670, 36.816670),
    "amherst,usa": (-78.799760, 42.978390),
    "victorville,usa": (-117.291160, 34.536110),
    "burton upon trent,uk": (-1.642630, 52.807280),
    "xiangcheng,china": (100.562480, 25.466870),
    "colchester,uk": (0.904210, 51.889210),
    "vallejo,usa": (-122.256640, 38.104090),
    "longshui,china": (105.762050, 29.565550),
    "lafayette,usa": (-92.019840, 30.224090),
    "lianhe,china": (129.274260, 47.133330),
    "chico,usa": (-121.837480, 39.728490),
    "north stamford,usa": (-73.543460, 41.138150),
    "hartford,usa": (-72.685090, 41.763710),
    "berkeley,usa": (-122.272750, 37.871590),
    "xilin hot,china": (116.033330, 43.966670),
    "west palm beach,usa": (-80.053370, 26.715340),
    "toa payoh new town,singapore": (103.850000, 1.336110),
    "lichuan,china": (108.850000, 30.300000),
    "allentown,usa": (-75.490180, 40.608430),
    "bao'an centre,china": (113.916300, 22.579530),
    "zhaoyuan,china": (120.409970, 37.364970),
    "evansville,usa": (-87.555850, 37.974760),
    "palm bay,usa": (-80.588660, 28.034460),
    "lhasa,china": (91.100000, 29.650000),
    "xunchang,china": (104.714980, 28.454330),
    "nanbin,china": (108.109130, 29.999400),
    "fargo,usa": (-96.789800, 46.877190),
    "eastbourne,uk": (0.284530, 50.768710),
    "shaoshan,china": (112.516670, 27.916670),
    "wushan,china": (109.876390, 31.077490),
    "shunyi,china": (116.647830, 40.121750),
    "rotherham,uk": (-1.356780, 53.430120),
    "clearwater,usa": (-82.800100, 27.965850),
    "independence,usa": (-94.415510, 39.091120),
    "longjing,china": (129.423070, 42.771310),
    "billings,usa": (-108.500690, 45.783290),
    "ann arbor,usa": (-83.740880, 42.277560),
    "serangoon,singapore": (103.897500, 1.362780),
    "serangoon new town,singapore": (103.870830, 1.350830),
    "el monte,usa": (-118.027570, 34.068620),
    "gulin,china": (105.810380, 28.042230),
    "cheltenham,uk": (-2.079720, 51.900060),
    "chenggu,china": (107.325830, 33.149170),
    "harlem,usa": (-73.945420, 40.807880),
    "westminster,usa": (-105.037200, 39.836650),
    "dasha,china": (113.441800, 23.110370),
    "yakeshi,china": (120.733330, 49.283330),
    "san tung chung hang,china": (113.943070, 22.278750),
    "round rock,usa": (-97.678900, 30.508260),
    "wilmington,usa": (-77.946040, 34.235560),
    "east harlem,usa": (-73.942500, 40.794720),
    "baisha,china": (106.118900, 29.062260),
    "anliu,china": (115.679530, 23.698240),
    "lengshuijiang,china": (111.429440, 27.688060),
    "tianfu,china": (122.052280, 37.263660),
    "arvada,usa": (-105.087480, 39.802760),
    "beaumont,usa": (-94.101850, 30.086050),
    "sanxia,taiwan": (121.371390, 24.934480),
    "provo,usa": (-111.658530, 40.233840),
    "mingshui,china": (117.500000, 36.716670),
    "carlsbad,usa": (-117.350590, 33.158090),
    "qiaotou,china": (101.673610, 36.935000),
    "odessa,usa": (-102.367640, 31.845680),
    "downey,usa": (-118.132570, 33.940010),
    "yuyao,china": (121.149440, 30.050000),
    "tung chung,china": (113.942430, 22.287830),
    "zhaozhou,china": (125.266060, 45.705950),
    "wansheng,china": (106.928440, 28.962900),
    "wayaobu,china": (109.659720, 37.136110),
    "pingshan,china": (114.713110, 22.993760),
    "songyuan,china": (124.827690, 45.129020),
    "maba,china": (113.598390, 24.684130),
    "doncaster,uk": (-1.131160, 53.522850),
    "elmhurst,usa": (-73.877910, 40.736490),
    "costa mesa,usa": (-117.918670, 33.641130),
    "miami gardens,usa": (-80.245600, 25.942040),
    "chesterfield,uk": (-1.416670, 53.250000),
    "north peoria,usa": (-89.584260, 40.717540),
    "fairfield,usa": (-122.039970, 38.249360),
    "neili,taiwan": (121.261390, 24.972500),
    "taonan,china": (122.784640, 45.333190),
    "lansing,usa": (-84.555530, 42.732530),
    "bushwick,usa": (-73.918750, 40.694270),
    "shaowu,china": (117.483100, 27.340890),
    "mengmao,china": (97.864990, 24.001390),
    "wuzhishan,china": (109.501300, 18.782290),
    "gravesend,usa": (-73.965140, 40.597600),
    "elgin,usa": (-88.281190, 42.037250),
    "xigang,china": (106.348050, 38.552580),
    "taipa,china": (113.556940, 22.155830),
    "west jordan,usa": (-111.939100, 40.609670),
    "inglewood,usa": (-118.353130, 33.961680),
    "chelmsford,uk": (0.469580, 51.735750),
    "tuscaloosa,usa": (-87.569170, 33.209840),
    "encheng,china": (112.304240, 22.186590),
    "richardson,usa": (-96.729720, 32.948180),
    "zhuji,china": (120.242330, 29.718770),
    "lowell,usa": (-71.316170, 42.633420),
    "east independence,usa": (-94.355230, 39.095560),
    "gresham,usa": (-122.431480, 45.498180),
    "antioch,usa": (-121.805790, 38.004920),
    "cambridge,usa": (-71.105610, 42.375100),
    "high point,usa": (-80.005320, 35.955690),
    "datun,china": (116.901740, 34.809230),
    "manchester,usa": (-71.454790, 42.995640),
    "geylang,singapore": (103.886890, 1.319530),
    "sembawang estate,singapore": (103.828610, 1.450830),
    "qingnian,china": (115.710870, 36.840920),
    "temecula,usa": (-117.148360, 33.493640),
    "mendip,uk": (-2.626600, 51.237200),
    "linshui,china": (114.204720, 36.424720),
    "hailun,china": (126.924750, 47.446630),
    "murrieta,usa": (-117.213920, 33.553910),
    "wakefield,uk": (-1.497680, 53.683310),
    "centennial,usa": (-104.876920, 39.579160),
    "shilong,china": (113.847220, 23.114440),
    "didao,china": (130.836930, 45.347250),
    "walthamstow,uk": (-0.020770, 51.590670),
    "pueblo,usa": (-104.609140, 38.254450),
    "jianchang,china": (116.639780, 27.558310),
    "hulan,china": (126.578360, 45.893260),
    "zhongxiang,china": (112.583060, 31.166110),
    "pearland,usa": (-95.286050, 29.563570),
    "dehui,china": (125.694270, 44.536740),
    "waterbury,usa": (-73.051500, 41.558150),
    "greeley,usa": (-104.709130, 40.423310),
    "west covina,usa": (-117.938950, 34.068620),
    "enterprise,usa": (-115.241940, 36.025250),
    "hanjia,china": (108.161320, 29.295240),
    "taibai,china": (108.357830, 30.824820),
    "dagenham,uk": (0.166670, 51.550000),
    "xuyong,china": (105.434520, 28.169920),
    "north charleston,usa": (-79.974810, 32.854620),
    "nehe,china": (124.870160, 48.479300),
    "everett,usa": (-122.202080, 47.978980),
    "douliu,taiwan": (120.543330, 23.709440),
    "college station,usa": (-96.334410, 30.627980),
    "jalai nur,china": (117.700000, 49.450000),
    "pompano beach,usa": (-80.124770, 26.237860),
    "basingstoke,uk": (-1.087080, 51.262490),
    "maidstone,uk": (0.516670, 51.266670),
    "tieli,china": (128.048040, 46.975440),
    "shaping,china": (112.957760, 22.770190),
    "south fulton,usa": (-84.672940, 33.592590),
    "norwalk,usa": (-118.081730, 33.902240),
    "sutton coldfield,uk": (-1.816670, 52.566670),
    "bedford,uk": (-0.466320, 52.134590),
    "boulder,usa": (-105.270550, 40.014990),
    "anning,china": (102.484960, 24.922710),
    "broken arrow,usa": (-95.790820, 36.052600),
    "daly city,usa": (-122.461920, 37.705770),
    "longjiang,china": (123.196000, 47.336010),
    "buhe,china": (112.229790, 30.287570),
    "toufen,taiwan": (120.909420, 24.687530),
    "xinghua,china": (119.834170, 32.939170),
    "nantou,taiwan": (120.663870, 23.915660),
    "chengtangcun,china": (117.190710, 35.083570),
    "sandy springs,usa": (-84.378540, 33.924270),
    "burbank,usa": (-118.308970, 34.180840),
    "green bay,usa": (-88.019830, 44.519160),
    "santa maria,usa": (-120.435720, 34.953030),
    "yidu,china": (118.424540, 36.771210),
    "zhonghe,china": (108.989010, 28.450490),
    "universal city,usa": (-118.353410, 34.138900),
    "puyang chengguanzhen,china": (115.027900, 35.706220),
    "daxing,china": (116.326930, 39.740250),
    "yezhou,china": (109.723330, 30.603690),
    "wichita falls,usa": (-98.493390, 33.913710),
    "lakeland,usa": (-81.949800, 28.039470),
    "pailou,china": (108.385800, 30.796410),
    "pulandian,china": (121.966940, 39.395280),
    "clovis,usa": (-119.702920, 36.825230),
    "wuchuan,china": (110.765910, 21.457130),
    "salaqi,china": (110.510830, 40.541390),
    "lewisville,usa": (-96.994170, 33.046230),
    "jishu,china": (126.800000, 44.316670),
    "woking,uk": (-0.558930, 51.319030),
    "yuxi,china": (102.542220, 24.355000),
    "lincoln,uk": (-0.537920, 53.226830),
    "bashan,china": (116.050170, 27.768230),
    "tongren,china": (102.016000, 35.514830),
    "tyler,usa": (-95.301060, 32.351260),
    "el cajon,usa": (-116.962530, 32.794770),
    "gangu chengguanzhen,china": (105.326320, 34.735640),
    "san mateo,usa": (-122.325530, 37.562990),
    "brandon,usa": (-82.285920, 27.937800),
    "taitung,taiwan": (121.144570, 22.759910),
    "rialto,usa": (-117.370320, 34.106400),
    "xincheng,china": (82.932490, 41.714970),
    "davenport,usa": (-90.577640, 41.523640),
    "edison,usa": (-74.412100, 40.518720),
    "hillsboro,usa": (-122.989830, 45.522890),
    "jishou,china": (109.733460, 28.319250),
    "shuifu,china": (104.407830, 28.632150),
    "hedong,china": (115.780100, 23.919600),
    "worcester,uk": (-2.220010, 52.189350),
    "las cruces,usa": (-106.778340, 32.312320),
    "bath,uk": (-2.361720, 51.375100),
    "south bend,usa": (-86.250010, 41.683380),
    "kallang,singapore": (103.866670, 1.333330),
    "albany,usa": (-73.756230, 42.652580),
    "gillingham,uk": (0.548630, 51.389140),
    "huacheng,china": (115.613090, 24.067030),
    "new bedford,usa": (-70.927010, 41.635260),
    "vista,usa": (-117.242540, 33.200040),
    "davie,usa": (-80.233100, 26.062870),
    "chinatown,usa": (-122.408580, 37.796600),
    "lianjiang,china": (110.281720, 21.646730),
    "linxi,china": (118.449540, 39.711830),
    "renton,usa": (-122.217070, 47.482880),
    "xinzhai,china": (118.616670, 36.400000),
    "roanoke,usa": (-79.941430, 37.270970),
    "kangding,china": (101.956900, 30.002220),
    "becontree,uk": (0.129000, 51.552900),
    "qincheng,china": (116.530080, 27.212700),
    "menghuan,china": (98.583750, 24.435320),
    "san angelo,usa": (-100.437040, 31.463770),
    "xixiang,china": (107.764000, 32.987030),
    "kenosha,usa": (-87.821190, 42.584740),
    "dongsheng,china": (109.977630, 39.816090),
    "clinton township,usa": (-82.919920, 42.586980),
    "wangkui,china": (126.476570, 46.832140),
    "erie,usa": (-80.085060, 42.129220),
    "hualien city,taiwan": (121.604440, 23.976940),
    "meihekou,china": (125.678760, 42.528690),
    "xinle,china": (114.685310, 38.348980),
    "worthing,uk": (-0.375380, 50.817950),
    "linghe,china": (119.076940, 36.364170),
    "portsmouth heights,usa": (-76.368830, 36.820980),
    "richmond hill,usa": (-73.831250, 40.699830),
    "xingcheng,china": (120.716670, 40.616670),
    "alief,usa": (-95.596330, 29.711060),
    "spring hill,usa": (-82.525460, 28.476880),
    "renqiu,china": (116.100860, 38.709410),
    "suifenhe,china": (131.147750, 44.399820),
    "compton,usa": (-118.220070, 33.895850),
    "xinshi,china": (113.140980, 31.047040),
    "league city,usa": (-95.094930, 29.507450),
    "flint,usa": (-83.687460, 43.012530),
    "chengzihe,china": (131.004890, 45.336110),
    "xishan,china": (113.500000, 27.666670),
    "allen,usa": (-96.670550, 33.103170),
    "yeyuan,china": (118.500000, 36.416670),
    "dorchester,usa": (-71.074500, 42.297320),
    "guanhu,china": (117.995280, 34.425280),
    "jiudian,china": (120.204120, 36.991800),
    "rochdale,uk": (-2.155200, 53.617660),
    "xinxing,china": (105.322160, 34.775970),
    "mission viejo,usa": (-117.672000, 33.600020),
    "fangshan,china": (115.996580, 39.686990),
    "jinniu,china": (100.574350, 25.800620),
    "caotun,taiwan": (120.687660, 23.976990),
    "vacaville,usa": (-121.987740, 38.356580),
    "ventura,usa": (-119.293170, 34.278340),
    "houzhen,china": (118.965820, 36.991360),
    "highlands ranch,usa": (-104.969430, 39.553880),
    "lawton,usa": (-98.390330, 34.608690),
    "beaverton,usa": (-122.803710, 45.487060),
    "zhudong,taiwan": (121.090830, 24.731670),
    "gongguan,china": (109.600000, 21.800000),
    "south gate,usa": (-118.212020, 33.954740),
    "portsmouth,usa": (-76.298270, 36.835430),
    "sparks,usa": (-119.752690, 39.534910),
    "nanxi,china": (104.979580, 28.842090),
    "queenstown estate,singapore": (103.802500, 1.294170),
    "lubu,china": (112.282980, 23.172330),
    "jinsha,china": (121.073550, 32.089820),
    "yuma,usa": (-114.624400, 32.725320),
    "ducheng,china": (111.528400, 23.242120),
    "shenjiamen,china": (122.298020, 29.957630),
    "brockton,usa": (-71.018380, 42.083430),
    "boli,china": (130.584520, 45.752900),
    "xiaoshan,china": (120.258830, 30.167460),
    "xingguo,china": (105.668610, 34.858610),
    "royal leamington spa,uk": (-1.520000, 52.285200),
    "dearborn,usa": (-83.176310, 42.322260),
    "federal way,usa": (-122.312620, 47.322320),
    "lee's summit,usa": (-94.382170, 38.910840),
    "asheville,usa": (-82.554020, 35.600950),
    "romford,uk": (0.185820, 51.575150),
    "spokane valley,usa": (-117.239370, 47.673230),
    "wuchang,china": (127.160390, 44.927540),
    "fordham,usa": (-73.898470, 40.859270),
    "livonia,usa": (-83.352710, 42.368370),
    "roswell,usa": (-84.361590, 34.023160),
    "orem,usa": (-111.694650, 40.296900),
    "dunhou,china": (114.900000, 27.050000),
    "bayan hot,china": (105.668610, 38.838610),
    "harlow,uk": (0.111580, 51.776550),
    "ximeicun,china": (118.385800, 24.987730),
    "daxi,taiwan": (121.290430, 24.883730),
    "yilan,taiwan": (121.753000, 24.757000),
    "yishui,china": (118.628060, 35.784720),
    "fall river,usa": (-71.155050, 41.701490),
    "zhongduo,china": (108.764160, 28.846600),
    "lawrence,usa": (-95.235250, 38.971670),
    "the woodlands,usa": (-95.489380, 30.157990),
    "fangcheng chengguanzhen,china": (113.001200, 33.253220),
    "west albany,usa": (-73.778450, 42.683130),
    "daotian,china": (118.897780, 36.833890),
    "yakima,usa": (-120.505900, 46.602070),
    "baijiantan,china": (85.139420, 45.692980),
    "yunnanyi,china": (100.689000, 25.424500),
    "shuangliao,china": (123.500690, 43.510670),
    "quincy,usa": (-71.002270, 42.252880),
    "flatbush,usa": (-73.959030, 40.652050),
    "dalai,china": (124.300000, 45.500000),
    "hesperia,usa": (-117.300880, 34.426390),
    "carson,usa": (-118.282020, 33.831410),
    "tangwu,china": (118.859720, 36.446670),
    "boca raton,usa": (-80.083100, 26.358690),
    "jiayue,china": (119.176110, 36.023610),
    "santa monica,usa": (-118.491380, 34.019490),
    "changping,china": (116.234710, 40.216120),
    "san marcos,usa": (-117.166140, 33.143370),
    "lianzhou,china": (112.371200, 24.781860),
    "boyle heights,usa": (-118.205350, 34.033900),
    "nuneaton,uk": (-1.465230, 52.523230),
    "high peak,uk": (-1.845360, 53.367970),
    "yingqiu,china": (118.992850, 36.526630),
    "plantation,usa": (-80.231840, 26.134210),
    "lynn,usa": (-70.949490, 42.466760),
    "clementi housing estate,singapore": (103.764720, 1.315830),
    "darlington,uk": (-1.550390, 54.524290),
    "miami beach,usa": (-80.130050, 25.790650),
    "dongcun,china": (121.159720, 36.776670),
    "arden-arcade,usa": (-121.378540, 38.602500),
    "longmont,usa": (-105.101930, 40.167210),
    "danjiangkou,china": (111.508610, 32.542780),
    "bai'anba,china": (108.437170, 30.762830),
    "santa barbara,usa": (-119.698190, 34.420830),
    "zhongshu,china": (103.766670, 24.516670),
    "southport,uk": (-3.010080, 53.645810),
    "huazhou,china": (110.583330, 21.633330),
    "redding,usa": (-122.391680, 40.586540),
    "xingren,china": (105.233330, 25.433330),
    "longquan,china": (102.161300, 24.671930),
    "yatou,china": (122.437620, 37.156600),
    "tanfang,china": (118.670870, 36.699770),
    "lingyuan,china": (119.401110, 41.240000),
    "macon,usa": (-83.632400, 32.840690),
    "gaoyou,china": (119.441820, 32.789330),
    "yulinshi,china": (109.737530, 38.291810),
    "meridian,usa": (-116.391510, 43.612110),
    "san leandro,usa": (-122.156080, 37.724930),
    "hanting,china": (119.210830, 36.770830),
    "greenville,usa": (-77.366350, 35.612660),
    "chester,uk": (-2.891890, 53.190500),
    "xihe,china": (113.465850, 31.686350),
    "duobao,china": (112.689520, 30.670000),
    "stevenage,uk": (-0.202560, 51.902240),
    "sishui,china": (117.275830, 35.648890),
    "edmond,usa": (-97.478100, 35.652830),
    "wembley,uk": (-0.296860, 51.552420),
    "gantang,china": (111.973060, 27.437500),
    "luomen,china": (105.024720, 34.754170),
    "huaidian,china": (115.033330, 33.433330),
    "nampa,usa": (-116.563460, 43.540720),
    "grays,uk": (0.325210, 51.475660),
    "trenton,usa": (-74.742940, 40.217050),
    "sandy hills,usa": (-111.850770, 40.581060),
    "fujin,china": (132.029570, 47.247230),
    "huaicheng,china": (112.176290, 23.919520),
    "micheng,china": (100.487250, 25.342940),
    "lucheng,china": (117.280570, 31.233570),
    "hede,china": (120.261760, 33.772200),
    "chengxiang,china": (109.570630, 31.397980),
    "harrogate,uk": (-1.537300, 53.990780),
    "nandajie,china": (105.892370, 29.337730),
    "lengshuitan,china": (111.595590, 26.411100),
    "hartlepool,uk": (-1.210280, 54.685540),
    "newton,usa": (-71.209220, 42.337040),
    "toms river,usa": (-74.197920, 39.953730),
    "wangqing,china": (129.763340, 43.310770),
    "carmel,usa": (-86.118040, 39.978370),
    "xiazhuang,china": (119.835560, 36.449170),
    "dongxing,china": (107.966670, 21.550000),
    "linjiacun,china": (119.650280, 35.993890),
    "zhoujiaba,china": (108.366420, 30.843490),
    "waukegan,usa": (-87.844790, 42.363630),
    "deltona,usa": (-81.263670, 28.900540),
    "honghe,china": (118.918060, 36.402780),
    "hawthorne,usa": (-118.352570, 33.916400),
    "baixi,china": (104.549170, 28.699700),
    "fort smith,usa": (-94.398550, 35.385920),
    "suffolk,usa": (-76.584960, 36.728360),
    "sugar land,usa": (-95.634950, 29.619680),
    "livermore,usa": (-121.768010, 37.681870),
    "lidu,china": (107.294770, 29.738610),
    "nashua,usa": (-71.467570, 42.765370),
    "yingchuan,china": (113.463890, 34.162780),
    "yingge,taiwan": (121.350700, 24.956080),
    "gusong,china": (105.237700, 28.313300),
    "reading,usa": (-75.926870, 40.335650),
    "hanchuan,china": (113.766670, 30.650000),
    "tiefu,china": (118.033330, 34.533330),
    "qiongshan,china": (110.353840, 20.008640),
    "xiangxiang,china": (112.533330, 27.733330),
    "deqing,china": (119.959900, 30.544850),
    "indio,usa": (-116.216770, 33.720700),
    "rio rancho,usa": (-106.664470, 35.233380),
    "enchanted hills,usa": (-106.592960, 35.336760),
    "santa fe,usa": (-105.937800, 35.686980),
    "sandy,usa": (-111.884100, 40.591610),
    "xujiang,china": (116.320110, 26.839450),
    "whittier,usa": (-118.032840, 33.979180),
    "canarsie,usa": (-73.900690, 40.643720),
    "bishan new town,singapore": (103.848750, 1.350400),
    "kirkland,usa": (-122.208740, 47.681490),
    "mishan,china": (131.883330, 45.550000),
    "nenjiang,china": (125.219670, 49.174050),
    "menifee,usa": (-117.146420, 33.728350),
    "fulham,uk": (-0.199300, 51.480260),
    "londonderry county borough,uk": (-7.309170, 54.997210),
    "newport beach,usa": (-117.928950, 33.618910),
    "tracy,usa": (-121.426180, 37.739870),
    "citrus heights,usa": (-121.281060, 38.707120),
    "bend,usa": (-121.315310, 44.058170),
    "menglang,china": (99.910290, 22.562140),
    "canton,usa": (-83.482160, 42.308650),
    "lehigh acres,usa": (-81.624800, 26.625350),
    "greenburgh,usa": (-73.842910, 41.032870),
    "shizilu,china": (118.828890, 35.171110),
    "jiangshan,china": (120.529170, 36.678060),
    "zhaogezhuang,china": (118.411910, 39.765380),
    "bloomington,usa": (-93.298280, 44.840800),
    "west town,usa": (-87.674930, 41.893810),
    "anlong,china": (105.516670, 25.100000),
    "puli,taiwan": (120.969520, 23.966390),
    "germantown,usa": (-77.271650, 39.173160),
    "clifton,usa": (-74.163760, 40.858430),
    "miaoli,taiwan": (120.823670, 24.564270),
    "qamdo,china": (97.179820, 31.130400),
    "grimsby,uk": (-0.075530, 53.565390),
    "nanfeng,china": (111.797230, 23.726950),
    "cannock,uk": (-2.030850, 52.690450),
    "duluth,usa": (-92.106580, 46.783270),
    "champaign,usa": (-88.243380, 40.116420),
    "zhonggulou,china": (108.384130, 30.824910),
    "longnan,china": (104.917030, 33.397910),
    "helong,china": (128.997220, 42.539740),
    "near north side,usa": (-87.634500, 41.900030),
    "hemel hempstead,uk": (-0.449750, 51.753680),
    "chino,usa": (-117.688940, 34.012230),
    "nanding,china": (118.055830, 36.748330),
    "ogden,usa": (-111.973830, 41.223000),
    "guozhen,china": (107.359040, 34.365910),
    "redwood city,usa": (-122.236350, 37.485220),
    "bellingham,usa": (-122.488220, 48.759550),
    "qufu,china": (116.991110, 35.596670),
    "o'fallon,usa": (-90.699850, 38.810610),
    "hoover,usa": (-86.811380, 33.405390),
    "laojunmiao,china": (97.733330, 39.833330),
    "melbourne,usa": (-80.608110, 28.083630),
    "danbury,usa": (-73.454010, 41.394820),
    "dacheng,china": (109.392750, 19.509270),
    "st albans,uk": (-0.333330, 51.750000),
    "east norwalk,usa": (-73.398450, 41.105650),
    "edinburg,usa": (-98.163340, 26.301740),
    "sunrise,usa": (-80.113100, 26.133970),
    "dazhong,china": (120.457800, 33.199730),
    "liaolan,china": (119.875280, 36.674440),
    "redditch,uk": (-1.945690, 52.306500),
    "jinxiang,china": (120.606250, 27.432650),
    "dongxia,china": (118.582680, 36.749180),
    "degan,china": (106.231570, 29.278460),
    "xiannue,china": (119.560480, 32.428060),
    "cicero,usa": (-87.753940, 41.845590),
    "yinma,china": (119.462500, 36.660830),
    "hemet,usa": (-116.973070, 33.747610),
    "south shields,uk": (-1.432300, 54.998590),
    "derry,uk": (-7.309340, 54.998100),
    "lingdong,china": (131.144930, 46.554280),
    "nanzhang chengguanzhen,china": (111.827520, 31.783940),
    "san pedro,usa": (-118.292290, 33.735850),
    "ahwatukee foothills,usa": (-111.984030, 33.341710),
    "johns creek,usa": (-84.198580, 34.028930),
    "mission,usa": (-98.325290, 26.215910),
    "troy,usa": (-83.149930, 42.605590),
    "buena park,usa": (-117.998120, 33.867510),
    "xucheng,china": (110.166430, 20.330250),
    "wensu,china": (80.236120, 41.275480),
    "hecun,china": (114.111110, 36.533330),
    "mid-city,usa": (-118.360580, 34.041260),
    "ningyang,china": (116.791390, 35.764170),
    "jinshi,china": (111.870120, 29.604870),
    "weston-super-mare,uk": (-2.976650, 51.346030),
    "palm coast,usa": (-81.207840, 29.584970),
    "yuanping,china": (112.757500, 38.715280),
    "sioux city,usa": (-96.400310, 42.499990),
    "aoxi,china": (115.836430, 27.425890),
    "liping,china": (109.131390, 26.231110),
    "halifax,uk": (-1.850000, 53.716670),
    "changqing,china": (116.727220, 36.557500),
    "dali old town,china": (100.158940, 25.688630),
    "xindian,china": (118.294440, 36.797500),
    "yima,china": (111.883890, 34.738060),
    "lake forest,usa": (-117.689220, 33.646970),
    "qiaoguan,china": (118.883890, 36.564440),
    "merced,usa": (-120.482970, 37.302160),
    "nangong,china": (115.388810, 37.354640),
    "lueshun,china": (121.266670, 38.800000),
    "longview,usa": (-94.740490, 32.500700),
    "anguo,china": (116.819440, 34.830560),
    "bryan,usa": (-96.369960, 30.674360),
    "shiwan,china": (113.077000, 23.001070),
    "edmonton,uk": (-0.057980, 51.625610),
    "beckenham,uk": (-0.025260, 51.408780),
    "westland,usa": (-83.400210, 42.324200),
    "tamworth,uk": (-1.695870, 52.633990),
    "donghe,china": (106.301260, 32.233410),
    "huaiyang,china": (114.517030, 37.761450),
    "tangping,china": (111.935370, 22.031770),
    "warwick,usa": (-71.416170, 41.700100),
    "scunthorpe,uk": (-0.654370, 53.579050),
    "yudong,china": (106.519440, 29.385000),
    "farmington hills,usa": (-83.377160, 42.485310),
    "san tan valley,usa": (-111.528000, 33.191100),
    "mount pleasant,usa": (-79.862590, 32.794070),
    "changning,china": (104.920870, 28.577730),
    "xiugu,china": (116.776370, 27.911320),
    "cranston,usa": (-71.437280, 41.779820),
    "largo,usa": (-82.788420, 27.909790),
    "feicheng,china": (117.967500, 35.260560),
    "shanting,china": (117.457780, 35.075280),
    "homestead,usa": (-80.477560, 25.468720),
    "junlian,china": (104.511620, 28.171060),
    "south suffolk,usa": (-76.590230, 36.717090),
    "avondale,usa": (-112.349600, 33.435600),
    "nianzhuang,china": (117.772220, 34.297220),
    "tustin,usa": (-117.826170, 33.745850),
    "yingjiang,china": (97.936710, 24.710220),
    "mountain view,usa": (-122.083850, 37.386050),
    "napa,usa": (-122.285530, 38.297140),
    "zhuanghe,china": (122.991110, 39.700830),
    "loushanguan,china": (106.822000, 28.136800),
    "somerville,usa": (-71.099500, 42.387600),
    "baoying,china": (119.309170, 33.229170),
    "kendall,usa": (-80.317270, 25.679270),
    "dashiqiao,china": (122.502510, 40.637320),
    "panshi,china": (126.057430, 42.937190),
    "huanglou,china": (118.605540, 36.647090),
    "dushan,china": (107.533330, 25.833330),
    "rikaze,china": (88.883330, 29.250000),
    "sha tin wai,china": (114.197530, 22.377560),
    "stockton-on-tees,uk": (-1.318700, 54.568480),
    "parma,usa": (-81.722910, 41.404770),
    "new rochelle,usa": (-73.782350, 40.911490),
    "lynchburg,usa": (-79.142250, 37.413750),
    "medford,usa": (-122.875590, 42.326520),
    "deerfield beach,usa": (-80.099770, 26.318410),
    "songlou,china": (116.602390, 34.572310),
    "taixing,china": (120.013610, 32.166670),
    "sylmar,usa": (-118.449250, 34.307780),
    "pleasanton,usa": (-121.874680, 37.662430),
    "tangjiazhuang,china": (118.450990, 39.743260),
    "yanta,china": (115.667220, 36.241110),
    "belmont cragin,usa": (-87.768670, 41.931700),
    "brooklyn park,usa": (-93.356340, 45.094130),
    "zhuangyuan,china": (120.827470, 37.305530),
    "wuyang,china": (116.247220, 31.992500),
    "xiongzhou,china": (114.300000, 25.116670),
    "chaigou,china": (119.624170, 36.248890),
    "goodyear,usa": (-112.358210, 33.435320),
    "kennewick,usa": (-119.137230, 46.211250),
    "shitanjing,china": (106.343890, 39.234170),
    "tumen,china": (129.841990, 42.965620),
    "alameda,usa": (-122.260870, 37.770990),
    "jurong east,singapore": (103.739950, 1.328880),
    "qinggang,china": (106.236180, 29.467700),
    "hengbei,china": (115.725460, 23.879680),
    "carlisle,uk": (-2.938200, 54.895100),
    "town 'n' country,usa": (-82.577320, 28.010570),
    "bellflower,usa": (-118.117010, 33.881680),
    "yishan,china": (118.696630, 36.221070),
    "youhao,china": (128.835650, 47.853060),
    "chino hills,usa": (-117.758880, 33.993800),
    "pingyi,china": (117.630830, 35.500560),
    "wulong,china": (107.760560, 29.324310),
    "linping,china": (120.297220, 30.422500),
    "alafaya,usa": (-81.211400, 28.564100),
    "bukit timah,singapore": (103.791000, 1.328000),
    "springdale,usa": (-94.128810, 36.186740),
    "shap pat heung,china": (114.035810, 22.424800),
    "huankou,china": (116.669720, 34.870000),
    "linkou,china": (130.273320, 45.276200),
    "racine,usa": (-87.782850, 42.726130),
    "gateshead,uk": (-1.601680, 54.962090),
    "huangmei,china": (116.024960, 30.192350),
    "hammond,usa": (-87.500040, 41.583370),
    "milpitas,usa": (-121.906620, 37.428270),
    "songling,china": (120.717580, 31.193300),
    "jishui,china": (115.400000, 33.733330),
    "lisburn,uk": (-6.035270, 54.523370),
    "shulan,china": (126.948270, 44.411340),
    "paisley,uk": (-4.432540, 55.831730),
    "damiao,china": (117.363790, 34.264110),
    "jiexiu,china": (111.912500, 37.024440),
    "gary,usa": (-87.346430, 41.593370),
    "putney,uk": (-0.218140, 51.460720),
    "scranton,usa": (-75.664900, 41.409160),
    "pok fu lam,china": (114.129240, 22.268610),
    "baldwin park,usa": (-117.960900, 34.085290),
    "hunchun,china": (130.356890, 42.867360),
    "auburn,usa": (-122.228450, 47.307320),
    "fishers,usa": (-86.013870, 39.955590),
    "shrewsbury,uk": (-2.752080, 52.710090),
    "saint joseph,usa": (-94.846630, 39.768610),
    "sandu,china": (109.215000, 19.789400),
    "liangxiang,china": (116.132950, 39.735980),
    "zhaodun,china": (117.856990, 34.302700),
    "fenghua,china": (121.406400, 29.656280),
    "pharr,usa": (-98.183620, 26.194800),
    "fylde,uk": (-2.916670, 53.833330),
    "upland,usa": (-117.648390, 34.097510),
    "yaxing,china": (109.262730, 19.447780),
    "yangliuqing,china": (116.999720, 39.137500),
    "folsom,usa": (-121.176060, 38.677960),
    "qiuji,china": (118.000000, 33.800000),
    "baytown,usa": (-94.977430, 29.735500),
    "qingquan,china": (115.255930, 30.451130),
    "san ramon,usa": (-121.978020, 37.779930),
    "camden,usa": (-75.119620, 39.925950),
    "bracknell,uk": (-0.750540, 51.413630),
    "lake charles,usa": (-93.204400, 30.213090),
    "kalamazoo,usa": (-85.587230, 42.291710),
    "shouxian,china": (116.458840, 34.846480),
    "brick,usa": (-74.137080, 40.059280),
    "arlington heights,usa": (-87.980630, 42.088360),
    "plymouth,usa": (-93.455510, 45.010520),
    "lintong,china": (109.208920, 34.378030),
    "south ozone park,usa": (-73.819020, 40.670100),
    "doral,usa": (-80.355330, 25.819540),
    "waterford,usa": (-83.411810, 42.693030),
    "kageleke,china": (79.601280, 37.300960),
    "kanjia,china": (119.582080, 36.372270),
    "yinzhu,china": (119.975280, 35.878610),
    "battersea,uk": (-0.155470, 51.474750),
    "crewe,uk": (-2.441610, 53.097870),
    "evanston,usa": (-87.690060, 42.041140),
    "chatham,uk": (0.527860, 51.378910),
    "manteca,usa": (-121.216050, 37.797430),
    "wyoming,usa": (-85.705310, 42.913360),
    "shangmei,china": (111.295560, 27.742780),
    "loveland,usa": (-105.074980, 40.397760),
    "cheektowaga,usa": (-78.754750, 42.903390),
    "hove,uk": (-0.167200, 50.830880),
    "kings bridge,usa": (-73.905140, 40.878710),
    "bismarck,usa": (-100.783740, 46.808330),
    "xinying,taiwan": (120.310560, 23.306940),
    "perris,usa": (-117.228650, 33.782520),
    "maozhou,china": (113.812880, 22.763610),
    "bethlehem,usa": (-75.370460, 40.625930),
    "huilong,china": (121.655000, 31.811110),
    "nam cheong,china": (114.153890, 22.327990),
    "beidao,china": (105.893330, 34.568610),
    "aylesbury,uk": (-0.814580, 51.816650),
    "east kilbride,uk": (-4.176690, 55.764120),
    "yanggu,china": (115.775280, 36.110560),
    "kowloon west end,china": (114.185140, 22.328480),
    "schaumburg,usa": (-88.083410, 42.033360),
    "gastonia,usa": (-81.187300, 35.262080),
    "union city,usa": (-122.019130, 37.595770),
    "shancheng,china": (116.081670, 34.795280),
    "zhangzhai,china": (116.950000, 34.616670),
    "nanma,china": (118.154860, 36.184780),
    "bolingbrook,usa": (-88.068400, 41.698640),
    "yuanshang,china": (120.345560, 36.768330),
    "iowa city,usa": (-91.530170, 41.661130),
    "suixi,china": (116.774730, 33.890670),
    "layton,usa": (-111.971050, 41.060220),
    "xinmin,china": (122.825280, 41.990830),
    "missouri city,usa": (-95.537720, 29.618570),
    "appleton,usa": (-88.415380, 44.261930),
    "zhangzhuang,china": (117.005560, 34.519440),
    "shelby,usa": (-83.032980, 42.670870),
    "gucheng chengguanzhen,china": (111.634760, 32.266040),
    "xianshuigu,china": (117.382780, 38.985000),
    "fort myers,usa": (-81.840590, 26.621680),
    "boynton beach,usa": (-80.066430, 26.525350),
    "yunyang,china": (112.714220, 33.447430),
    "jonesboro,usa": (-90.704280, 35.842300),
    "south lawndale,usa": (-87.712550, 41.843640),
    "huayuan,china": (117.206560, 28.286350),
    "lanxi,china": (119.471560, 29.215880),
    "logan square,usa": (-87.699220, 41.923370),
    "genhe,china": (121.516670, 50.783330),
    "luocheng,china": (104.028620, 29.384810),
    "rapid city,usa": (-103.231010, 44.080540),
    "warner robins,usa": (-83.626640, 32.615740),
    "heguan,china": (118.573790, 36.889980),
    "rochester hills,usa": (-83.149930, 42.658370),
    "canary wharf,uk": (-0.020850, 51.505190),
    "juegang,china": (121.185520, 32.317370),
    "decatur,usa": (-88.954800, 39.840310),
    "southfield,usa": (-83.221870, 42.473370),
    "rugby,uk": (-1.264170, 52.370920),
    "shixing,china": (114.065720, 24.948240),
    "dongdu,china": (117.700000, 35.850000),
    "saint george,usa": (-113.584120, 37.104150),
    "yanjia,china": (106.997340, 29.827580),
    "new britain,usa": (-72.779540, 41.661210),
    "dongkan,china": (119.830830, 33.999720),
    "dingcheng,china": (115.039440, 32.127220),
    "daytona beach,usa": (-81.022830, 29.210810),
    "franklin,usa": (-86.868890, 35.925060),
    "wusu,china": (84.676230, 44.431050),
    "miyang,china": (103.442780, 24.404170),
    "jiangzhuang,china": (119.794170, 36.494440),
    "beichengqu,china": (113.153610, 40.439440),
    "xinzhi,china": (111.704720, 36.498890),
    "turlock,usa": (-120.846590, 37.494660),
    "temple,usa": (-97.342780, 31.098230),
    "west ridge,usa": (-87.692840, 41.999750),
    "apple valley,usa": (-117.185880, 34.500830),
    "zhoucheng,china": (116.311670, 35.912220),
    "purley,uk": (-0.112010, 51.336780),
    "lynwood,usa": (-118.211460, 33.930290),
    "waukesha,usa": (-88.231480, 43.011680),
    "caidian,china": (114.033330, 30.583330),
    "guildford,uk": (-0.574270, 51.235360),
    "gulfport,usa": (-89.092820, 30.367420),
    "xiuyan,china": (123.274440, 40.292780),
    "pawtucket,usa": (-71.382560, 41.878710),
    "lauderhill,usa": (-80.213380, 26.140360),
    "peckham,uk": (-0.069690, 51.474030),
    "rock hill,usa": (-81.025080, 34.924870),
    "luohuang,china": (106.435140, 29.346620),
    "shangsi,china": (107.979530, 22.156270),
    "silver spring,usa": (-77.026090, 38.990670),
    "barnsley,uk": (-1.483330, 53.550000),
    "west gulfport,usa": (-89.094200, 30.404090),
    "changtu,china": (124.095450, 42.778840),
    "huashan,china": (116.735830, 34.630000),
    "flower mound,usa": (-97.096960, 33.014570),
    "anlu,china": (113.678330, 31.257500),
    "yilan,china": (129.560810, 46.322300),
    "linjiang,china": (108.219640, 31.099560),
    "centreville,usa": (-77.428880, 38.840390),
    "passaic,usa": (-74.128480, 40.856770),
    "guiping,china": (110.074340, 23.394830),
    "riverview,usa": (-82.326480, 27.866140),
    "redlands,usa": (-117.182540, 34.055570),
    "missoula,usa": (-113.994000, 46.872150),
    "rancho cordova,usa": (-121.302730, 38.589070),
    "lowestoft,uk": (1.751670, 52.475230),
    "kuandian,china": (124.784720, 40.728610),
    "shenzhen city centre,china": (114.077100, 22.535890),
    "gosport,uk": (-1.129020, 50.795090),
    "poyang,china": (116.667540, 28.992420),
    "yongfeng,china": (112.169430, 27.454930),
    "gongchangling,china": (123.450000, 41.116670),
    "jimo,china": (120.462220, 36.389720),
    "new braunfels,usa": (-98.124450, 29.703000),
    "cherry hill,usa": (-75.030730, 39.934840),
    "baiquan,china": (126.082310, 47.606590),
    "jiangyan,china": (120.142780, 32.506110),
    "maidenhead,uk": (-0.719860, 51.522790),
    "shiguai,china": (110.285560, 40.705830),
    "flagstaff,usa": (-111.651270, 35.198070),
    "haining,china": (120.686380, 30.536290),
    "shankou,china": (109.716670, 21.600000),
    "stafford,uk": (-2.116360, 52.805210),
    "muncie,usa": (-85.386360, 40.193380),
    "pan'an,china": (105.111670, 34.754720),
    "uxbridge,uk": (-0.482110, 51.548900),
    "southall,uk": (-0.371300, 51.508960),
    "mira mesa,usa": (-117.143920, 32.915600),
    "woodland hills,usa": (-118.605920, 34.168340),
    "weston,usa": (-80.399770, 26.100370),
    "mengcheng chengguanzhen,china": (116.566050, 33.266110),
    "xinhe,china": (119.593060, 36.925000),
    "shima,china": (105.924410, 28.987730),
    "fengping,china": (98.517700, 24.397350),
    "frederick,usa": (-77.410540, 39.414270),
    "pasco,usa": (-119.100570, 46.239580),
    "chengxian chengguanzhen,china": (105.732940, 33.747750),
    "pittsburg,usa": (-121.884680, 38.027980),
    "xininglu,china": (84.904250, 44.339570),
    "ridgewood,usa": (-73.905690, 40.700100),
    "palatine,usa": (-88.034240, 42.110300),
    "xuantan,china": (105.569740, 29.208560),
    "jiehu,china": (118.455000, 35.542780),
    "north richland hills,usa": (-97.228900, 32.834300),
    "kissimmee,usa": (-81.416670, 28.304680),
    "xiaoshi,china": (124.120920, 41.297110),
    "royal tunbridge wells,uk": (0.262560, 51.133210),
    "walnut creek,usa": (-122.064960, 37.906310),
    "cordova,usa": (-89.776200, 35.155650),
    "yunmen,china": (106.323760, 30.082740),
    "mount vernon,usa": (-73.837080, 40.912600),
    "heishan,china": (122.112780, 41.689170),
    "conroe,usa": (-95.456050, 30.311880),
    "dothan,usa": (-85.390490, 31.223230),
    "northridge,usa": (-118.536750, 34.228340),
    "waterloo,usa": (-92.342960, 42.492760),
    "pengcheng,china": (114.170000, 36.431110),
    "wenjiang,china": (104.563390, 28.388120),
    "maple grove,usa": (-93.455790, 45.072460),
    "mingguang,china": (117.963780, 32.780170),
    "ninghai,china": (121.424720, 29.289170),
    "framingham,usa": (-71.416170, 42.279260),
    "wimbledon,uk": (-0.208050, 51.422120),
    "redondo beach,usa": (-118.388410, 33.849180),
    "bossier city,usa": (-93.732120, 32.515990),
    "stamford hill,uk": (-0.073340, 51.568720),
    "yorba linda,usa": (-117.813110, 33.888630),
    "chaihe,china": (129.678260, 44.759800),
    "minggang,china": (114.048610, 32.458610),
    "tangzhai,china": (116.591110, 34.432780),
    "xunyang,china": (109.365280, 32.823890),
    "yanghe,china": (106.247760, 38.278520),
    "woodbury,usa": (-92.959380, 44.923860),
    "dongfeng,china": (125.528850, 42.673870),
    "eau claire,usa": (-91.498490, 44.811350),
    "jiang'an,china": (105.068300, 28.733350),
    "zhenlai,china": (123.197910, 45.849630),
    "waldorf,usa": (-76.939140, 38.624560),
    "shuangfengqiao,china": (106.627120, 29.718590),
    "forest hills,usa": (-73.850140, 40.716210),
    "songjianghe,china": (127.478950, 42.185900),
    "davis,usa": (-121.740520, 38.544910),
    "glen burnie,usa": (-76.624690, 39.162610),
    "camarillo,usa": (-119.037600, 34.216390),
    "luorong,china": (109.608610, 24.405830),
    "victoria,usa": (-97.003600, 28.805270),
    "lueeyang chengguanzhen,china": (106.154960, 33.332050),
    "gaithersburg,usa": (-77.201370, 39.143440),
    "wenling,china": (121.384160, 28.375240),
    "rossendale,uk": (-2.276900, 53.684560),
    "fuqing,china": (119.374690, 25.729400),
    "caohe,china": (115.433460, 30.229700),
    "gaoliu,china": (118.500000, 36.800000),
    "pingzhuang,china": (119.288890, 42.037220),
    "south san francisco,usa": (-122.407750, 37.654660),
    "tianliu,china": (118.783330, 37.000000),
    "lushar,china": (101.563280, 36.484160),
    "wanggou,china": (116.492130, 34.671470),
    "fengkou,china": (113.333460, 30.082680),
    "shajing town,china": (113.807550, 22.738460),
    "kenner,usa": (-90.241740, 29.994090),
    "jackson heights,usa": (-73.885410, 40.755660),
    "rockville,usa": (-77.152760, 39.084000),
    "liuhe,china": (125.745440, 42.284730),
    "lincoln park,usa": (-87.647830, 41.921700),
    "yuba city,usa": (-121.616910, 39.140450),
    "hanyin chengguanzhen,china": (108.504720, 32.891390),
    "palo alto,usa": (-122.143020, 37.441880),
    "wacheng neighborhood,china": (114.516670, 33.783330),
    "casas adobes,usa": (-110.995100, 32.323410),
    "marysville,usa": (-122.177080, 48.051760),
    "duoba,china": (101.533740, 36.657950),
    "shaozhuang,china": (118.316550, 36.747010),
    "south jordan,usa": (-111.929660, 40.562170),
    "tailai,china": (123.408490, 46.390040),
    "lishi,china": (106.262000, 29.078880),
    "chengyang,china": (118.832780, 35.579440),
    "sanchazi,china": (126.600280, 42.081670),
    "daxu,china": (117.552660, 34.282390),
    "oshkosh,usa": (-88.542610, 44.024710),
    "qaraqash,china": (79.734380, 37.272460),
    "taihe,china": (106.048900, 30.099490),
    "north little rock,usa": (-92.267090, 34.769540),
    "lianyuan,china": (111.664170, 27.688330),
    "bayside,usa": (-73.777080, 40.768440),
    "folkestone,uk": (1.167340, 51.081690),
    "qipan,china": (118.221130, 34.244690),
    "tangxiang,china": (105.723630, 29.702260),
    "huinan,china": (126.261390, 42.622500),
    "bayonne,usa": (-74.114310, 40.668710),
    "brixton,uk": (-0.106520, 51.465930),
    "hounslow,uk": (-0.360920, 51.468390),
    "eagan,usa": (-93.166890, 44.804130),
    "beimeng,china": (119.495560, 36.604440),
    "delray beach,usa": (-80.072820, 26.461460),
    "chingford,uk": (0.000510, 51.630330),
    "muling,china": (130.517070, 44.916470),
    "huanren,china": (125.366670, 41.264720),
    "qionghu,china": (112.355050, 28.841220),
    "huanan,china": (130.546420, 46.236240),
    "xiaolingwei,china": (118.854000, 32.032440),
    "johnson city,usa": (-82.353470, 36.313440),
    "ganshui,china": (106.711110, 28.742220),
    "dale city,usa": (-77.311090, 38.637060),
    "cedar park,usa": (-97.820290, 30.505200),
    "yaoji,china": (117.816670, 34.066670),
    "qiantang,china": (106.316500, 30.184240),
    "mengyin,china": (117.926390, 35.706940),
    "parkchester,usa": (-73.860410, 40.838990),
    "atascocita,usa": (-95.176600, 29.998830),
    "jietou,china": (98.653240, 25.427400),
    "saint cloud,usa": (-94.162490, 45.560800),
    "ellicott city,usa": (-76.798310, 39.267330),
    "xiangcheng chengguanzhen,china": (113.477800, 33.847030),
    "bayiji,china": (117.683330, 34.266670),
    "finchley,uk": (-0.195180, 51.600960),
    "laguna niguel,usa": (-117.707550, 33.522530),
    "saint charles,usa": (-90.481230, 38.783940),
    "harlingen,usa": (-97.696100, 26.190630),
    "shangkou,china": (118.883060, 36.965560),
    "ligezhuang,china": (120.142780, 36.357780),
    "wrexham,uk": (-2.991320, 53.046640),
    "dashitou,china": (128.511390, 43.306670),
    "huanghua,china": (119.457780, 35.889170),
    "babu,china": (111.516670, 24.416670),
    "wufeng,taiwan": (120.698000, 24.063700),
    "yebaishou,china": (119.640830, 41.397500),
    "huaiyuan chengguanzhen,china": (117.165660, 32.958930),
    "san clemente,usa": (-117.611990, 33.426970),
    "west lynchburg,usa": (-79.178080, 37.403200),
    "middletown,usa": (-74.117090, 40.394280),
    "framingham center,usa": (-71.437010, 42.297320),
    "torquay,uk": (-3.525220, 50.461980),
    "bianzhuang,china": (118.044720, 34.848610),
    "suyangshan,china": (117.755560, 34.392780),
    "schenectady,usa": (-73.939570, 42.814240),
    "hepingjie,china": (126.915830, 42.059720),
    "liuxin,china": (117.115000, 34.368610),
    "loughborough,uk": (-1.200000, 52.766670),
    "caoqiao,china": (118.110380, 34.340500),
    "fengrun,china": (118.138220, 39.826640),
    "cheyenne,usa": (-104.820250, 41.139980),
    "broomfield,usa": (-105.086650, 39.920540),
    "ames,usa": (-93.619940, 42.034710),
    "park slope,usa": (-73.985970, 40.670100),
    "shawnee,usa": (-94.720240, 39.041670),
    "kunyang,china": (120.565830, 27.665830),
    "cricklewood,uk": (-0.215490, 51.556700),
    "reseda,usa": (-118.536470, 34.201120),
    "conway,usa": (-92.442100, 35.088700),
    "tianzhuang,china": (119.736670, 36.795830),
    "east orange,usa": (-74.204870, 40.767320),
    "lingao,china": (109.687170, 19.908730),
    "portage park,usa": (-87.765060, 41.957810),
    "skokie,usa": (-87.733390, 42.033360),
    "shikang,china": (109.316670, 21.766670),
    "kingswood,uk": (-2.508330, 51.452780),
    "fenggang,china": (116.214560, 27.545660),
    "west bloomfield township,usa": (-83.383560, 42.568910),
    "tamarac,usa": (-80.249770, 26.212860),
    "youngstown,usa": (-80.649520, 41.099780),
    "taunton,uk": (-3.102930, 51.014940),
    "lodi,usa": (-121.272450, 38.130200),
    "north hollywood,usa": (-118.378970, 34.172230),
    "picheng,china": (117.966670, 34.466670),
    "renzhao,china": (120.203610, 36.638610),
    "changli,china": (119.160300, 39.706470),
    "kaihua,china": (104.277210, 23.369500),
    "yunmeng chengguanzhen,china": (113.765450, 31.062510),
    "waterlooville,uk": (-1.030400, 50.880670),
    "mansfield,usa": (-97.141680, 32.563190),
    "santa cruz,usa": (-122.030800, 36.974120),
    "pico rivera,usa": (-118.096730, 33.983070),
    "madera,usa": (-120.060720, 36.961340),
    "janesville,usa": (-89.018720, 42.682790),
    "west des moines,usa": (-93.711330, 41.577210),
    "macclesfield,uk": (-2.125640, 53.260230),
    "montebello,usa": (-118.105350, 34.009460),
    "bognor regis,uk": (-0.679780, 50.782060),
    "newtownabbey,uk": (-5.908580, 54.659830),
    "dengbu,china": (116.817170, 28.208400),
    "yangcun,china": (117.060280, 39.363890),
    "magong,taiwan": (119.586270, 23.565400),
    "georgetown,usa": (-97.677230, 30.632690),
    "lulou,china": (116.766670, 34.716670),
    "alpharetta,usa": (-84.294090, 34.075380),
    "kettering,uk": (-0.725710, 52.398360),
    "lorain,usa": (-82.182370, 41.452820),
    "baihecun,china": (107.235920, 22.113210),
    "bowling green,usa": (-86.443600, 36.990320),
    "guanyin,china": (104.394160, 29.099260),
    "flatlands,usa": (-73.934860, 40.621220),
    "dundalk,usa": (-76.520520, 39.250660),
    "buckley,uk": (-3.083330, 53.166670),
    "mabai,china": (104.450810, 23.012790),
    "eden prairie,usa": (-93.470790, 44.854690),
    "north bergen,usa": (-74.012080, 40.804270),
    "great yarmouth,uk": (1.730520, 52.608310),
    "nanlong,china": (106.063090, 31.353330),
    "mitcham,uk": (-0.168310, 51.403220),
    "florence-graham,usa": (-118.244380, 33.967720),
    "youxi,china": (106.144280, 29.209360),
    "waltham,usa": (-71.235610, 42.376490),
    "west hartford,usa": (-72.742040, 41.762040),
    "changcheng,china": (119.451670, 36.090560),
    "shanwang,china": (118.711000, 36.545400),
    "rogers,usa": (-94.118540, 36.332020),
    "botou,china": (116.566670, 38.073660),
    "carol city,usa": (-80.245600, 25.940650),
    "liuku,china": (98.855670, 25.850500),
    "baoqing,china": (132.189700, 46.324520),
    "mong kok,china": (114.171360, 22.319350),
    "shizhai,china": (116.638890, 34.805560),
    "encinitas,usa": (-117.291980, 33.036990),
    "jinggou,china": (119.551850, 36.281760),
    "runcorn,uk": (-2.731240, 53.341740),
    "fanlou,china": (116.852480, 34.480910),
    "east village,usa": (-73.987360, 40.729270),
    "ashford,uk": (0.873760, 51.146480),
    "haverhill,usa": (-71.077280, 42.776200),
    "jupiter,usa": (-80.094210, 26.934220),
    "council bluffs,usa": (-95.860830, 41.261940),
    "wellington,usa": (-80.241440, 26.658680),
    "tonypandy,uk": (-3.455440, 51.622020),
    "miaojie,china": (100.279830, 25.312320),
    "kaitong,china": (123.081080, 44.809130),
    "west coon rapids,usa": (-93.349670, 45.159690),
    "zhangjiachuan,china": (106.209020, 34.987560),
    "pingnan,china": (110.389290, 23.541800),
    "north miami,usa": (-80.186710, 25.890090),
    "hamilton,usa": (-84.561340, 39.399500),
    "deqen,china": (90.718750, 29.961780),
    "songyang,china": (113.031940, 34.455490),
    "yucheng,china": (116.465280, 34.928890),
    "north port,usa": (-82.235930, 27.044220),
    "shuikou,china": (115.895810, 23.983720),
    "tulare,usa": (-119.347340, 36.207730),
    "coon rapids,usa": (-93.287730, 45.119970),
    "millcreek,usa": (-111.875490, 40.686890),
    "shuangyang,china": (125.659480, 43.522590),
    "nianzishan,china": (122.887880, 47.513440),
    "la habra,usa": (-117.946170, 33.931960),
    "blaine,usa": (-93.234950, 45.160800),
    "pingyin,china": (116.445280, 36.283060),
    "bin xian,china": (127.460530, 45.742740),
    "qingshuping,china": (112.020560, 27.380830),
    "lake elsinore,usa": (-117.327260, 33.668080),
    "zhaobaoshan,china": (121.687530, 29.969500),
    "hushitai,china": (123.502660, 41.941750),
    "zhangji,china": (117.375560, 34.137500),
    "huoqiu chengguanzhen,china": (116.293900, 32.354730),
    "mudu,china": (120.518570, 31.255970),
    "fengyi,china": (100.311810, 25.583990),
    "nandu,china": (110.823330, 22.852500),
    "taoluo,china": (119.370280, 35.273890),
    "yingshang chengguanzhen,china": (116.270130, 32.629450),
    "ellesmere port town,uk": (-2.901340, 53.278750),
    "carmichael,usa": (-121.328280, 38.617130),
    "scarborough,uk": (-0.404430, 54.279660),
    "xiangzhou,china": (119.418890, 36.164440),
    "yongning,china": (108.483590, 22.761010),
    "hancheng,china": (112.352220, 32.518610),
    "lishu,china": (124.333710, 43.307270),
    "oroqen zizhiqi,china": (123.716670, 50.566670),
    "taylor,usa": (-83.269650, 42.240870),
    "xianju,china": (120.731680, 28.854700),
    "burnsville,usa": (-93.277720, 44.767740),
    "jianguang,china": (115.783600, 28.193770),
    "monterey park,usa": (-118.122850, 34.062510),
    "widnes,uk": (-2.734060, 53.361800),
    "dongning,china": (131.118410, 44.084360),
    "dashi,china": (106.222270, 30.093720),
    "castro valley,usa": (-122.086350, 37.694100),
    "aldershot,uk": (-0.763890, 51.248270),
    "irvington,usa": (-74.234870, 40.732320),
    "tianchang,china": (114.015560, 37.998060),
    "rocklin,usa": (-121.235780, 38.790730),
    "utica,usa": (-75.232660, 43.100900),
    "xifeng,china": (124.722220, 42.737220),
    "malden,usa": (-71.066160, 42.425100),
    "national city,usa": (-117.099200, 32.678110),
    "bury,uk": (-2.300000, 53.600000),
    "nanhu,china": (119.345830, 35.487780),
    "yicheng,china": (112.256110, 31.704720),
    "bangor,uk": (-5.668020, 54.660790),
    "barking,uk": (0.083330, 51.533330),
    "financial district,usa": (-74.008570, 40.707890),
    "xiema,china": (106.368800, 29.774150),
    "yanliang,china": (109.229210, 34.659180),
    "tahe,china": (124.697610, 52.321480),
    "bethesda,usa": (-77.100260, 38.980670),
    "erdaojiang,china": (126.031940, 41.776390),
    "terre haute,usa": (-87.413910, 39.466700),
    "vineland,usa": (-75.025730, 39.486230),
    "west hollywood,usa": (-80.183940, 26.020650),
    "tianpeng,china": (103.939330, 30.986640),
    "yaowan,china": (118.066670, 34.183330),
    "brentwood,usa": (-73.246230, 40.781210),
    "lakeville,usa": (-93.242720, 44.649690),
    "mujiayingzi,china": (118.783330, 42.116670),
    "west allis,usa": (-88.007030, 43.016680),
    "redmond,usa": (-122.121510, 47.673990),
    "dingjia,china": (106.142280, 29.409000),
    "canoga park,usa": (-118.598140, 34.201120),
    "cupertino,usa": (-122.032180, 37.323000),
    "langzhong,china": (105.993810, 31.550370),
    "taylorsville,usa": (-111.938830, 40.667720),
    "castleford,uk": (-1.362560, 53.725870),
    "liancheng,china": (116.748920, 25.718260),
    "jiangbei,china": (106.635060, 29.728300),
    "bristol,usa": (-72.949270, 41.671760),
    "moore,usa": (-97.486700, 35.339510),
    "gardena,usa": (-118.308960, 33.888350),
    "petaluma,usa": (-122.636650, 38.232420),
    "bensalem,usa": (-74.951280, 40.104550),
    "hereford,uk": (-2.714820, 52.056840),
    "grand junction,usa": (-108.550650, 39.063870),
    "taitou,china": (118.633920, 37.027330),
    "gushu,china": (118.481470, 31.560550),
    "fenshui,china": (108.083330, 30.719700),
    "casper,usa": (-106.313080, 42.866630),
    "wujing,china": (118.400000, 36.450000),
    "rowlett,usa": (-96.563880, 32.902900),
    "wucheng,china": (118.174950, 29.600770),
    "yuxia,china": (108.629050, 34.061530),
    "runing,china": (114.354170, 33.001110),
    "zhijiang,china": (111.753330, 30.421390),
    "stroud,uk": (-2.200000, 51.750000),
    "gucheng,china": (118.762460, 36.953470),
    "taozhuang,china": (117.333330, 34.850000),
    "margate,uk": (1.386170, 51.381320),
    "sandaohezi,china": (85.620090, 44.325970),
    "yongbei,china": (100.780730, 26.646230),
    "la mesa,usa": (-117.023080, 32.767830),
    "pine hills,usa": (-81.453400, 28.557780),
    "dazeshan,china": (119.922240, 36.988740),
    "zhujiajiao,china": (121.056960, 31.107570),
    "wuzhen,china": (120.485100, 30.745360),
    "chelsea,uk": (-0.169360, 51.487550),
    "bensonhurst,usa": (-73.994030, 40.601770),
    "coney island,usa": (-73.994030, 40.577880),
    "rancho penasquitos,usa": (-117.115310, 32.959490),
    "valley glen,usa": (-118.420320, 34.185680),
    "meriden,usa": (-72.807040, 41.538150),
    "pontiac,usa": (-83.291050, 42.638920),
    "welwyn garden city,uk": (-0.206910, 51.801740),
    "jiangkou,china": (119.198340, 25.486940),
    "farnborough,uk": (-0.755650, 51.294240),
    "maqin county,china": (100.244960, 34.474420),
    "port orange,usa": (-80.995610, 29.138320),
    "hamden,usa": (-72.896770, 41.395930),
    "pucheng,china": (118.533330, 27.923330),
    "fountainebleau,usa": (-80.347830, 25.772880),
    "saint clair shores,usa": (-82.888810, 42.496980),
    "great falls,usa": (-111.300810, 47.500240),
    "baimajing,china": (109.218010, 19.711950),
    "tuanbao,china": (109.134650, 30.336750),
    "chapel hill,usa": (-79.055840, 35.913200),
    "canyon country,usa": (-118.472030, 34.423330),
    "wenshang,china": (116.496110, 35.727500),
    "rhondda,uk": (-3.448850, 51.658960),
    "huntington park,usa": (-118.225070, 33.981680),
    "huiqu,china": (119.049030, 36.271360),
    "coconut creek,usa": (-80.178940, 26.251750),
    "gannan,china": (123.500460, 47.920380),
    "craigavon,uk": (-6.387000, 54.447090),
    "leander,usa": (-97.853070, 30.578810),
    "hongjiang,china": (109.995560, 27.110000),
    "jian'ou,china": (118.318970, 27.041460),
    "idaho falls,usa": (-112.034140, 43.466580),
    "tashan,china": (117.566670, 34.336110),
    "san rafael,usa": (-122.531090, 37.973530),
    "jixian,china": (131.133080, 46.725940),
    "hezuo,china": (102.909440, 34.985560),
    "haizhou,china": (119.128890, 34.581670),
    "noblesville,usa": (-86.008600, 40.045590),
    "longgu,china": (116.806670, 34.903330),
    "yigou,china": (114.316670, 35.811390),
    "marietta,usa": (-84.549930, 33.952600),
    "langtoucun,china": (124.335250, 40.040680),
    "owensboro,usa": (-87.113330, 37.774220),
    "eastvale,usa": (-117.564180, 33.963580),
    "royal oak,usa": (-83.144650, 42.489480),
    "xiaoweizhai,china": (107.512500, 26.190280),
    "antu,china": (128.908480, 43.102470),
    "dubuque,usa": (-90.664570, 42.500560),
    "wallasey,uk": (-3.064970, 53.423240),
    "suozhen,china": (118.104720, 36.953890),
    "brookline,usa": (-71.121160, 42.331760),
    "novi,usa": (-83.475490, 42.480590),
    "littlehampton,uk": (-0.540780, 50.811370),
    "des plaines,usa": (-87.883400, 42.033360),
    "taifu,china": (105.637020, 28.981980),
    "carson city,usa": (-119.767400, 39.163800),
    "orland park,usa": (-87.853940, 41.630310),
    "bartlett,usa": (-89.873980, 35.204530),
    "woodland,usa": (-121.773300, 38.678520),
    "shiqiaozi,china": (119.263060, 36.161670),
    "jidong,china": (131.116370, 45.256000),
    "lehi,usa": (-111.850770, 40.391620),
    "fenyi,china": (114.668050, 27.811170),
    "white plains,usa": (-73.762910, 41.033990),
    "chonglong,china": (104.852240, 29.780620),
    "xinglongshan,china": (125.466110, 43.956110),
    "arcadia,usa": (-118.035340, 34.139730),
    "reston,usa": (-77.341100, 38.968720),
    "shibuzi,china": (119.102780, 36.123890),
    "lixian,china": (105.172500, 34.190000),
    "hongqiao,china": (112.108140, 26.768370),
    "zhutuo,china": (105.848770, 29.018400),
    "ocala,usa": (-82.140090, 29.187200),
    "dingtao,china": (115.565820, 35.074360),
    "clay,usa": (-76.172430, 43.185900),
    "dongxi,china": (106.661110, 28.761390),
    "central city,usa": (-112.058050, 33.440010),
    "south vineland,usa": (-75.028790, 39.445950),
    "sanford,usa": (-81.273120, 28.800550),
    "juye,china": (116.071680, 35.387370),
    "streatham,uk": (-0.131840, 51.428970),
    "bowie,usa": (-76.730280, 38.942780),
    "santangpu,china": (111.986940, 27.405560),
    "kokomo,usa": (-86.133600, 40.486430),
    "wayne,usa": (-74.276540, 40.925380),
    "jing'an,china": (116.922490, 34.496210),
    "bootle,uk": (-3.016670, 53.466670),
    "santee,usa": (-116.973920, 32.838380),
    "emin,china": (83.634180, 46.525820),
    "longtan,china": (108.964140, 28.757160),
    "shenliu,china": (112.164350, 29.413690),
    "dublin,usa": (-121.935790, 37.702150),
    "weymouth,uk": (-2.459910, 50.614480),
    "maocun,china": (117.250560, 34.376670),
    "huangpi,china": (114.377890, 30.884530),
    "shanhecun,china": (128.580290, 45.711310),
    "yantongshan,china": (126.009440, 43.291940),
    "guiren,china": (118.188890, 33.669720),
    "palm harbor,usa": (-82.763710, 28.078070),
    "fareham,uk": (-1.179290, 50.851620),
    "morley,uk": (-1.598770, 53.740130),
    "cheshunt,uk": (-0.030260, 51.700200),
    "siu lek yuen,china": (114.212560, 22.381740),
    "zhongxing,china": (118.679170, 33.703890),
    "langxiang,china": (128.868490, 46.949850),
    "midwest city,usa": (-97.396700, 35.449510),
    "center city,usa": (-75.159230, 39.951200),
    "margate,usa": (-80.206440, 26.244530),
    "south whittier,usa": (-118.039170, 33.950150),
    "bageqi,china": (79.835090, 37.140710),
    "tinley park,usa": (-87.784490, 41.573370),
    "suiling,china": (127.107690, 47.234890),
    "pflugerville,usa": (-97.620000, 30.439370),
    "wenxing,china": (112.878640, 28.682080),
    "yingli,china": (118.810290, 37.065000),
    "kidderminster,uk": (-2.250000, 52.388190),
    "new brunswick,usa": (-74.451820, 40.486220),
    "grand forks,usa": (-97.032850, 47.925260),
    "baishishan,china": (127.566670, 43.583330),
    "fountain valley,usa": (-117.953670, 33.709180),
    "north hills,usa": (-118.484720, 34.236390),
    "zhuzhai,china": (116.813890, 34.761110),
    "diamond bar,usa": (-117.810340, 34.028620),
    "livingston,uk": (-3.522610, 55.902880),
    "jinji,china": (110.826110, 23.228060),
    "corby,uk": (-0.689390, 52.496370),
    "taunton,usa": (-71.089770, 41.900100),
    "oak lawn,usa": (-87.758110, 41.710870),
    "union,usa": (-74.263200, 40.697600),
    "ankeny,usa": (-93.605770, 41.729710),
    "weining,china": (104.233330, 26.850000),
    "chicopee,usa": (-72.607870, 42.148700),
    "dartford,uk": (0.214230, 51.446570),
    "castlereagh,uk": (-5.884720, 54.573500),
    "qingfu,china": (104.516220, 28.437010),
    "dewsbury,uk": (-1.629070, 53.690760),
    "daokou,china": (114.515930, 35.568950),
    "yashan,china": (109.941940, 22.197500),
    "irving park,usa": (-87.736450, 41.953360),
    "nantai,china": (122.804370, 40.924100),
    "changleng,china": (115.816670, 28.700000),
    "hutang,china": (119.490000, 31.534290),
    "berwyn,usa": (-87.793670, 41.850590),
    "sanchuan,china": (100.658940, 26.750410),
    "sitou,china": (118.411850, 36.312750),
    "stourbridge,uk": (-2.143170, 52.456080),
    "zibihu,china": (99.952670, 26.114300),
    "baidi,china": (109.590880, 31.057610),
    "gaogou,china": (119.188610, 34.017500),
    "linghai,china": (121.366670, 41.165280),
    "kendale lakes,usa": (-80.407000, 25.708160),
    "smyrna,usa": (-84.514380, 33.883990),
    "dearborn heights,usa": (-83.273260, 42.336980),
    "longshi,china": (106.457430, 30.214690),
    "xuzhuang,china": (117.457980, 34.296140),
    "porterville,usa": (-119.016770, 36.065230),
    "piscataway,usa": (-74.399040, 40.499270),
    "gongyi,china": (113.011370, 34.755340),
    "hendersonville,usa": (-86.620000, 36.304770),
    "qinnan,china": (119.913330, 33.253060),
    "gelan,china": (107.116120, 30.035890),
    "morningside heights,usa": (-73.962500, 40.810000),
    "dalianwan,china": (121.695000, 39.028610),
    "changling,china": (123.975590, 44.272950),
    "rocky mount,usa": (-77.790530, 35.938210),
    "corvallis,usa": (-123.262040, 44.564570),
    "olympia,usa": (-122.901690, 47.044910),
    "valdosta,usa": (-83.280320, 30.833340),
    "sale,uk": (-2.324430, 53.425190),
    "bonan,china": (99.528260, 25.463350),
    "hanford,usa": (-119.645680, 36.327450),
    "zhuyi,china": (109.385620, 31.025430),
    "yongqing,china": (106.126940, 34.748060),
    "castle rock,usa": (-104.856090, 39.372210),
    "linqiong,china": (103.460890, 30.415870),
    "greenwood,usa": (-86.106650, 39.613660),
    "chicago lawn,usa": (-87.696440, 41.775030),
    "hempstead,usa": (-73.618740, 40.706210),
    "novato,usa": (-122.569700, 38.107420),
    "kettering,usa": (-84.168830, 39.689500),
    "qishan,china": (117.719370, 29.844310),
    "lanshan,china": (117.725000, 33.936110),
    "shoreline,usa": (-122.341520, 47.755650),
    "anjiang,china": (110.103060, 27.319440),
    "xinqing,china": (129.523370, 48.287010),
    "paramount,usa": (-118.159790, 33.889460),
    "port arthur,usa": (-93.942330, 29.885190),
    "dorbod,china": (124.442000, 46.861350),
    "yutan,china": (112.560480, 28.258310),
    "abington,usa": (-75.117950, 40.120670),
    "anderson,usa": (-85.680250, 40.105320),
    "ahu,china": (118.603080, 34.376640),
    "tamiami,usa": (-80.398390, 25.758710),
    "halesowen,uk": (-2.049380, 52.448590),
    "canterbury,uk": (1.079920, 51.279040),
    "south croydon,uk": (-0.094210, 51.362170),
    "towson,usa": (-76.601910, 39.401500),
    "bayan,china": (127.393690, 46.076220),
    "north chicopee,usa": (-72.599530, 42.183430),
    "licha,china": (119.783330, 36.057220),
    "pingjin,china": (107.544970, 30.611760),
    "uptown,usa": (-87.652620, 41.965900),
    "sarasota,usa": (-82.530650, 27.336430),
    "shilin,china": (103.332370, 24.818780),
    "liguo,china": (117.332960, 34.552870),
    "huangnihe,china": (128.023890, 43.558330),
    "cypress hills,usa": (-73.891250, 40.677050),
    "west haven,usa": (-72.947050, 41.270650),
    "rosemead,usa": (-118.072850, 34.080570),
    "edgewater,usa": (-87.663950, 41.983370),
    "highland,usa": (-117.208650, 34.128340),
    "manzhouli,china": (117.433330, 49.600000),
    "huguo,china": (105.366630, 28.586260),
    "liuji,china": (117.052780, 34.358330),
    "mount prospect,usa": (-87.937290, 42.066420),
    "liangzhai,china": (116.750000, 34.500000),
    "huyton,uk": (-2.839350, 53.411500),
    "leytonstone,uk": (0.007680, 51.568560),
    "liaozhong,china": (122.724170, 41.506110),
    "barry,uk": (-3.283800, 51.399790),
    "colton,usa": (-117.313650, 34.073900),
    "encanto,usa": (-112.078230, 33.479370),
    "wangji,china": (117.750000, 33.983330),
    "hamilton,uk": (-4.033330, 55.766670),
    "nanzhou,china": (112.406540, 29.363820),
    "pocatello,usa": (-112.445530, 42.871300),
    "bradenton,usa": (-82.574820, 27.498930),
    "pasir ris new town,singapore": (103.947780, 1.372220),
    "rogers park,usa": (-87.666720, 42.008640),
    "weymouth,usa": (-70.939770, 42.220930),
    "port charlotte,usa": (-82.090640, 26.976170),
    "yunjin,china": (105.643290, 29.081800),
    "normal,usa": (-88.990630, 40.514200),
    "spring,usa": (-95.417160, 30.079940),
    "allapattah,usa": (-80.223940, 25.814540),
    "gravesend,uk": (0.371060, 51.442060),
    "richland,usa": (-119.284460, 46.285690),
    "eastleigh,uk": (-1.350000, 50.966670),
    "euless,usa": (-97.081950, 32.837070),
    "sau mau ping,china": (114.234970, 22.320200),
    "blue springs,usa": (-94.281610, 39.016950),
    "east pensacola heights,usa": (-87.179970, 30.428810),
    "meikle earnock,uk": (-4.033330, 55.750000),
    "hacienda heights,usa": (-117.968680, 33.993070),
    "fangcun,china": (117.473610, 34.086390),
    "xihu,taiwan": (120.479180, 23.956830),
    "ozone park,usa": (-73.843750, 40.676770),
    "yongjian,china": (100.212440, 25.425430),
    "mingcun,china": (119.640830, 36.753610),
    "briarwood,usa": (-73.815290, 40.709350),
    "lingcheng,china": (118.113610, 33.816390),
    "cathedral city,usa": (-116.465290, 33.779740),
    "elyria,usa": (-82.107650, 41.368380),
    "pensacola,usa": (-87.216910, 30.421310),
    "wheaton,usa": (-88.107010, 41.866140),
    "commerce city,usa": (-104.933870, 39.808320),
    "acton,uk": (-0.276200, 51.509010),
    "jinding,china": (99.440610, 26.439030),
    "hoboken,usa": (-74.032360, 40.743990),
    "watsonville,usa": (-121.756890, 36.910230),
    "lake havasu city,usa": (-114.322450, 34.483900),
    "qingxichang,china": (108.904420, 28.404170),
    "washington,uk": (-1.516670, 54.900000),
    "braintree,uk": (0.552920, 51.878190),
    "buzhuang,china": (119.556600, 36.912180),
    "little havana,usa": (-80.233060, 25.768060),
    "shiquan,china": (108.236390, 33.040830),
    "revere,usa": (-71.011990, 42.408430),
    "yangtun,china": (116.883330, 34.883330),
    "zhangfeng,china": (97.801910, 24.190640),
    "west new york,usa": (-74.014310, 40.787880),
    "chaozhou,taiwan": (120.540670, 22.549870),
    "yucaipa,usa": (-117.043090, 34.033630),
    "yousuo,china": (100.067710, 26.025270),
    "gilroy,usa": (-121.568280, 37.005780),
    "zhaozhuang,china": (116.455560, 34.738890),
    "poinciana,usa": (-81.458410, 28.140290),
    "university of texas,usa": (-97.738890, 30.286040),
    "kingsport,usa": (-82.561820, 36.548430),
    "tangzhang,china": (117.253950, 34.147790),
    "levittown,usa": (-74.828770, 40.155110),
    "palm beach gardens,usa": (-80.138650, 26.823390),
    "lingwu,china": (106.340170, 38.101910),
    "taoyuan,china": (117.770280, 33.852780),
    "milford,usa": (-73.056500, 41.222320),
    "beisu,china": (114.806890, 38.154790),
    "delano,usa": (-119.247050, 35.768840),
    "west sacramento,usa": (-121.530230, 38.580460),
    "wulingyuan,china": (110.544070, 29.349360),
    "malingshan,china": (118.356500, 34.203510),
    "huntersville,usa": (-80.842850, 35.410690),
    "perth amboy,usa": (-74.265420, 40.506770),
    "sherman oaks,usa": (-118.449250, 34.151120),
    "hualong,china": (118.588640, 36.945890),
    "dianbu,china": (120.351110, 36.701670),
    "southaven,usa": (-90.012590, 34.988980),
    "brentwood,uk": (0.305560, 51.621270),
    "saint peters,usa": (-90.626510, 38.800330),
    "puji,china": (119.721110, 36.131940),
    "downtown dc,usa": (-77.019910, 38.893500),
    "harrisonburg,usa": (-78.868920, 38.449570),
    "peabody,usa": (-70.928660, 42.527870),
    "placentia,usa": (-117.870340, 33.872240),
    "lenexa,usa": (-94.733570, 38.953620),
    "desoto,usa": (-96.856950, 32.589860),
    "burlington,usa": (-79.437800, 36.095690),
    "south hill,usa": (-122.270120, 47.141210),
    "xingqiao,china": (120.251710, 30.399430),
    "esher,uk": (-0.366930, 51.369690),
    "elkhart,usa": (-85.976670, 41.681990),
    "la crosse,usa": (-91.239580, 43.801360),
    "oak park,usa": (-87.784500, 41.885030),
    "songlingcun,china": (118.271430, 40.293940),
    "florissant,usa": (-90.322610, 38.789220),
    "sammamish,usa": (-122.080400, 47.641770),
    "yunshan,china": (120.226110, 36.824170),
    "dapeng,china": (117.075220, 34.284360),
    "sanzhuang,china": (119.171670, 35.503330),
    "wakefield,usa": (-73.852360, 40.897880),
    "se,china": (113.547330, 22.190890),
    "matilda estate,singapore": (103.902780, 1.399440),
    "zhawa,china": (79.628970, 37.214210),
    "jitai,china": (118.738660, 36.757240),
    "hoffman estates,usa": (-88.079800, 42.042810),
    "reigate,uk": (-0.205820, 51.237360),
    "albany park,usa": (-87.723390, 41.968360),
    "zizhuang,china": (117.488160, 34.361520),
    "liangji,china": (117.969440, 33.963890),
    "methuen,usa": (-71.190890, 42.726200),
    "glendora,usa": (-117.865340, 34.136120),
    "dunstable,uk": (-0.522880, 51.885710),
    "queens village,usa": (-73.741520, 40.726770),
    "dashahe,china": (116.624530, 34.538470),
    "brookhaven,usa": (-84.340200, 33.858440),
    "duzhou,china": (107.078400, 29.878480),
    "palm desert,usa": (-116.376970, 33.722550),
    "zhongxin,china": (101.271540, 26.616670),
    "weimiao,china": (117.066670, 34.583330),
    "joplin,usa": (-94.513280, 37.084230),
    "enid,usa": (-97.878390, 36.395590),
    "tiu keng leng,china": (114.251150, 22.298530),
    "bonita springs,usa": (-81.778700, 26.339810),
    "sao lourenco,china": (113.534880, 22.188510),
    "irondequoit,usa": (-77.579720, 43.213400),
    "zepu,china": (77.270750, 38.188670),
    "caldwell,usa": (-116.687360, 43.662940),
    "minnetonka,usa": (-93.503290, 44.913300),
    "liuquan,china": (117.298330, 34.434170),
    "morecambe,uk": (-2.861080, 54.068350),
    "pinellas park,usa": (-82.699540, 27.842800),
    "cumbernauld,uk": (-3.990510, 55.946850),
    "battle creek,usa": (-85.178160, 42.317300),
    "redhill,uk": (-0.170440, 51.240480),
    "zhefang,china": (98.283330, 24.266670),
    "horsham,uk": (-0.327570, 51.063140),
    "casa grande,usa": (-111.757350, 32.879500),
    "south shore,usa": (-87.577830, 41.761980),
    "mott haven,usa": (-73.922910, 40.808990),
    "the villages,usa": (-81.959940, 28.934080),
    "grand island,usa": (-98.342010, 40.925010),
    "sanhui,china": (106.591200, 30.081670),
    "grapevine,usa": (-97.078070, 32.934290),
    "stratford,usa": (-73.133170, 41.184540),
    "kentwood,usa": (-85.644750, 42.869470),
    "city of milford (balance),usa": (-73.061640, 41.223740),
    "dianzi,china": (119.865720, 36.901100),
    "tigard,usa": (-122.771490, 45.431230),
    "east hartford,usa": (-72.612030, 41.782320),
    "plainfield,usa": (-74.407370, 40.633710),
    "leesburg,usa": (-77.563600, 39.115660),
    "panlong,china": (105.370660, 29.500250),
    "parsippany,usa": (-74.425990, 40.857880),
    "coral gables,usa": (-80.268380, 25.721490),
    "gangshang,china": (118.118350, 34.521470),
    "guanshan,china": (117.866390, 33.798330),
    "the trails of frisco,usa": (-96.871820, 33.160870),
    "staines,uk": (-0.506060, 51.430920),
    "the hammocks,usa": (-80.444500, 25.671490),
    "shuijiang,china": (107.284430, 29.247600),
    "buckeye,usa": (-112.583780, 33.370320),
    "flagami,usa": (-80.316160, 25.762320),
    "guanzhuang,china": (119.193890, 36.263330),
    "batley,uk": (-1.633700, 53.702910),
    "catalina foothills,usa": (-110.918700, 32.297850),
    "shanji,china": (117.595560, 34.204720),
    "lhuenzhub,china": (91.261660, 29.893100),
    "wellingborough,uk": (-0.694460, 52.302730),
    "clacton-on-sea,uk": (1.155970, 51.789670),
    "north la crosse,usa": (-91.248190, 43.846350),
    "burien,usa": (-122.346790, 47.470380),
    "hanyuan,china": (106.250350, 32.834000),
    "havertown,usa": (-75.308520, 39.980950),
    "dunfermline,uk": (-3.458870, 56.071560),
    "logan,usa": (-111.834390, 41.735490),
    "south peabody,usa": (-70.949490, 42.509820),
    "aliso viejo,usa": (-117.727120, 33.565040),
    "bletchley,uk": (-0.734710, 51.993340),
    "harrisburg,usa": (-76.884420, 40.273700),
    "galveston,usa": (-94.797700, 29.301350),
    "keighley,uk": (-1.906640, 53.867910),
    "poway,usa": (-117.035860, 32.962820),
    "edina,usa": (-93.349950, 44.889690),
    "minnetonka mills,usa": (-93.441900, 44.941070),
    "nanjian,china": (100.514370, 25.044930),
    "naxi,china": (105.364880, 28.774220),
    "zhenxi,china": (107.464520, 29.899290),
    "hayes,uk": (-0.423400, 51.515790),
    "lohas park,china": (114.272450, 22.293150),
    "stonecrest,usa": (-84.134850, 33.708490),
    "cerritos,usa": (-118.064790, 33.858350),
    "yongxin,china": (106.533330, 28.966670),
    "redford,usa": (-83.296600, 42.383370),
    "east honolulu,usa": (-157.717340, 21.289060),
    "paignton,uk": (-3.567890, 50.435650),
    "sunnyside,usa": (-73.935420, 40.739820),
    "changdian,china": (116.583390, 34.775860),
    "wharton,usa": (-75.157120, 39.926780),
    "whitman,usa": (-75.155460, 39.916780),
    "downers grove,usa": (-88.011170, 41.808920),
    "azusa,usa": (-117.907560, 34.133620),
    "xinglou,china": (117.827780, 34.566670),
    "wilson,usa": (-77.915540, 35.721270),
    "monroe,usa": (-92.119300, 32.509310),
    "bridgend,uk": (-3.577220, 51.505830),
    "llanelli,uk": (-4.161910, 51.681950),
    "parker,usa": (-104.761360, 39.518600),
    "mihe,china": (118.528720, 36.620960),
    "la mirada,usa": (-118.012010, 33.917240),
    "maizhokunggar,china": (91.728890, 29.837740),
    "kirkcaldy,uk": (-3.159990, 56.116830),
    "minot,usa": (-101.296270, 48.232510),
    "aloha,usa": (-122.867050, 45.494280),
    "shuanghe,china": (105.569420, 29.320740),
    "guangshun,china": (105.526530, 29.374830),
    "gaoliang,china": (108.302240, 30.823940),
    "saginaw,usa": (-83.950810, 43.419470),
    "bedford,usa": (-97.143070, 32.844020),
    "novena,singapore": (103.843800, 1.316970),
    "rancho santa margarita,usa": (-117.603100, 33.640860),
    "dongcheng,china": (109.456100, 19.708680),
    "murray,usa": (-111.887990, 40.666890),
    "gao'an,china": (107.461970, 30.290190),
    "cuyahoga falls,usa": (-81.484560, 41.133940),
    "coeur d'alene,usa": (-116.780470, 47.677680),
    "bloomfield,usa": (-74.185420, 40.806770),
    "bromsgrove,uk": (-2.059830, 52.335740),
    "jiawang zhen,china": (117.467640, 34.422020),
    "rowland heights,usa": (-117.905340, 33.976120),
    "covina,usa": (-117.890340, 34.090010),
    "stillwater,usa": (-97.058370, 36.115610),
    "eltham,uk": (0.052250, 51.450610),
    "sittingbourne,uk": (0.732820, 51.341280),
    "haiyang,china": (118.176980, 29.786120),
    "niagara falls,usa": (-79.056710, 43.094500),
    "collierville,usa": (-89.664530, 35.042040),
    "oxford circle,usa": (-75.071840, 40.050110),
    "summerville,usa": (-80.175650, 33.018500),
    "south bel air,usa": (-76.337460, 39.533160),
    "south benfleet,uk": (0.559620, 51.552950),
    "sheboygan,usa": (-87.714530, 43.750830),
    "aspen hill,usa": (-77.073030, 39.079550),
    "gupi,china": (117.882780, 34.113890),
    "dunwoody,usa": (-84.334650, 33.946210),
    "banbury,uk": (-1.342220, 52.063200),
    "huntington,usa": (-82.445150, 38.419250),
    "maricopa,usa": (-112.047640, 33.058110),
    "ningdong,china": (106.585020, 38.161430),
    "xianfeng,china": (106.300120, 29.210040),
    "cedar hill,usa": (-96.956120, 32.588470),
    "east brunswick,usa": (-74.415980, 40.427880),
    "east lansing,usa": (-84.483870, 42.736980),
    "liutuan,china": (119.383330, 36.933330),
    "apopka,usa": (-81.511860, 28.676170),
    "da'an,china": (106.014760, 29.383100),
    "chenlou,china": (118.050000, 34.388890),
    "maspeth,usa": (-73.912640, 40.723160),
    "west bridgford,uk": (-1.125370, 52.929790),
    "mishawaka,usa": (-86.158620, 41.661990),
    "qing'an,china": (117.880560, 33.969440),
    "morden,uk": (-0.198370, 51.398220),
    "portage,usa": (-85.580000, 42.201150),
    "cwmbran,uk": (-3.022810, 51.654460),
    "dalu,china": (106.217700, 29.729840),
    "west orange,usa": (-74.239040, 40.798710),
    "mclean,usa": (-77.177480, 38.934280),
    "qianliu,china": (100.200000, 22.900000),
    "weiji,china": (117.950000, 34.033330),
    "wangfen,china": (118.383330, 36.550000),
    "jielong,china": (106.776630, 29.249460),
    "ceres,usa": (-120.957710, 37.594930),
    "shuangfu,china": (106.270140, 29.413590),
    "damxung,china": (91.105500, 30.477970),
    "long eaton,uk": (-1.271360, 52.898550),
    "baizi,china": (105.712970, 30.094030),
    "chesterfield,usa": (-90.577070, 38.663110),
    "barnstable,usa": (-70.299470, 41.700110),
    "salina,usa": (-97.611420, 38.840280),
    "yuexi,china": (108.159260, 30.911270),
    "inverness,uk": (-4.223980, 57.479080),
    "durham,uk": (-1.575660, 54.776760),
    "donggang,taiwan": (120.449270, 22.465150),
    "bel air south,usa": (-76.319770, 39.505060),
    "pearl city,usa": (-157.975160, 21.397340),
    "euclid,usa": (-81.526790, 41.593100),
    "cuijiaji,china": (119.713330, 36.625280),
    "texas city,usa": (-94.902700, 29.383850),
    "wauwatosa,usa": (-88.007590, 43.049460),
    "damoujia,china": (119.813260, 36.543560),
    "vermont square,usa": (-118.298960, 34.002040),
    "florin,usa": (-121.408840, 38.496020),
    "twin falls,usa": (-114.460870, 42.562970),
    "glenview,usa": (-87.787840, 42.069750),
    "northwich,uk": (-2.520250, 53.258820),
    "east providence,usa": (-71.370050, 41.813710),
    "palm springs,usa": (-116.545290, 33.830300),
    "perth,uk": (-3.431390, 56.395220),
    "san luis obispo,usa": (-120.659620, 35.282750),
    "shunhe,china": (116.557220, 34.841840),
    "gongqingcheng,china": (115.809530, 29.249150),
    "hekou,china": (116.813890, 34.577780),
    "mission district,usa": (-122.419140, 37.759930),
    "hanwang,china": (117.083330, 34.194440),
    "diaoyucheng,china": (106.266130, 29.998780),
    "lancaster,uk": (-2.799880, 54.046490),
    "kongtan,china": (104.674740, 29.144080),
    "country club,usa": (-80.317000, 25.948150),
    "gwynn oak,usa": (-76.692750, 39.332610),
    "tipton,uk": (-2.067730, 52.529560),
    "winnetka,usa": (-118.572030, 34.213340),
    "kilmarnock,uk": (-4.495810, 55.611710),
    "jeffersonville,usa": (-85.737180, 38.277570),
    "san jacinto,usa": (-116.958640, 33.783910),
    "sunlou,china": (116.583330, 34.666670),
    "qabqa,china": (100.613060, 36.281390),
    "mentor,usa": (-81.339550, 41.666160),
    "hattiesburg,usa": (-89.290340, 31.327120),
    "nanpeng,china": (106.652220, 29.334720),
    "draper,usa": (-111.863820, 40.524670),
    "yuqunweng,china": (81.620560, 43.874440),
    "wylie,usa": (-96.538880, 33.015120),
    "shaji,china": (118.133330, 33.900000),
    "marine parade,singapore": (103.907780, 1.303060),
    "laguna,usa": (-121.423840, 38.421020),
    "charlottesville,usa": (-78.476680, 38.029310),
    "dumfries,uk": (-3.611390, 55.069590),
    "sanjiao,china": (105.867650, 29.488010),
    "lacey,usa": (-122.823190, 47.034260),
    "sankeshu,china": (108.065850, 26.563700),
    "makakilo / kapolei / honokai hale,usa": (-158.096760, 21.337400),
    "littleton,usa": (-105.016650, 39.613320),
    "mangshi,china": (98.570370, 24.453290),
    "banstead,uk": (-0.206850, 51.322330),
    "beavercreek,usa": (-84.063270, 39.709230),
    "biantang,china": (117.645410, 34.423250),
    "ayr,uk": (-4.633930, 55.462730),
    "baitao,china": (107.486880, 29.550830),
    "kannapolis,usa": (-80.621730, 35.487360),
    "neath,uk": (-3.804430, 51.663170),
    "shijiao,china": (106.756110, 28.924440),
    "king's lynn,uk": (0.395160, 52.751720),
    "winchester,uk": (-1.318700, 51.065130),
    "binghamton,usa": (-75.917970, 42.098690),
    "mei foo,china": (114.138560, 22.337190),
    "brighton,usa": (-71.156440, 42.350100),
    "hell's kitchen,usa": (-73.990900, 40.764960),
    "barrow in furness,uk": (-3.227580, 54.110940),
    "chefushan,china": (117.751190, 34.475250),
    "auburn gresham,usa": (-87.653220, 41.741790),
    "yeovil,uk": (-2.632110, 50.941590),
    "city of sammamish,usa": (-122.037680, 47.604440),
    "antelope,usa": (-121.329950, 38.708240),
    "keller,usa": (-97.251680, 32.934570),
    "shuanggou,china": (117.578060, 34.035280),
    "biloxi,usa": (-88.885310, 30.396030),
    "middleton,uk": (-2.200000, 53.550000),
    "apex,usa": (-78.850290, 35.732650),
    "havant,uk": (-0.985590, 50.856700),
    "west lafayette,usa": (-86.908070, 40.425870),
    "gudong,china": (98.482970, 25.341650),
    "carshalton,uk": (-0.167550, 51.368290),
    "pingli,china": (109.345560, 32.384720),
    "zouzhuang,china": (118.050000, 34.600000),
    "cutler bay,usa": (-80.337700, 25.578300),
    "dangjiang,china": (109.116670, 21.650000),
    "ping shan,china": (114.006080, 22.441110),
    "titusville,usa": (-80.807550, 28.612220),
    "tangba,china": (105.797300, 30.016510),
    "altoona,usa": (-78.394740, 40.518680),
    "oro valley,usa": (-110.966490, 32.390910),
    "nongzhang,china": (97.882180, 24.616010),
    "saint louis park,usa": (-93.348010, 44.948300),
    "hinckley,uk": (-1.376130, 52.538900),
    "enfield,usa": (-72.591760, 41.976210),
    "tuckahoe,usa": (-77.556380, 37.590150),
    "potomac,usa": (-77.208590, 39.018170),
    "cleveland heights,usa": (-81.556240, 41.520050),
    "yanguan,china": (105.463890, 34.263890),
    "sayreville,usa": (-74.360980, 40.459270),
    "shangyun,china": (99.828380, 23.051910),
    "catford,uk": (-0.020430, 51.444910),
    "hackensack,usa": (-74.043470, 40.885930),
    "pine bluff,usa": (-92.003200, 34.228430),
    "dahuangshan,china": (117.344360, 34.293410),
    "salisbury,uk": (-1.795690, 51.069310),
    "hegou,china": (118.122220, 34.408330),
    "west seneca,usa": (-78.799750, 42.850060),
    "pontefract,uk": (-1.312690, 53.691070),
    "strongsville,usa": (-81.835690, 41.314500),
    "coachella,usa": (-116.173890, 33.680300),
    "penn hills,usa": (-79.839220, 40.501180),
    "encino,usa": (-118.501190, 34.159170),
    "shuitu,china": (106.497400, 29.782210),
    "guxian,china": (120.225580, 36.734100),
    "bentonville,usa": (-94.208820, 36.372850),
    "fort pierce,usa": (-80.325610, 27.446710),
    "bridgewater,usa": (-74.648150, 40.600790),
    "jiushan,china": (118.465000, 36.196110),
    "danville,usa": (-121.999960, 37.821590),
    "youting,china": (105.737570, 29.431280),
    "oakland park,usa": (-80.131990, 26.172310),
    "qingshanquan,china": (117.363060, 34.416390),
    "willesden,uk": (-0.233330, 51.533330),
    "attleboro,usa": (-71.285610, 41.944540),
    "caojie,china": (106.390180, 29.997550),
    "severn,usa": (-76.698300, 39.137050),
    "blacksburg,usa": (-80.413940, 37.229570),
    "haltom city,usa": (-97.269180, 32.799570),
    "brighton park,usa": (-87.698940, 41.818920),
    "lompoc,usa": (-120.457940, 34.639150),
    "beiwangli,china": (115.396390, 38.620830),
    "wesley chapel,usa": (-82.327870, 28.239730),
    "zhushan,taiwan": (120.682030, 23.755510),
    "urbandale,usa": (-93.712170, 41.626660),
    "shuanglong,china": (104.344910, 28.452080),
    "york,usa": (-76.727740, 39.962600),
    "north miami beach,usa": (-80.162550, 25.933150),
    "coatbridge,uk": (-4.024690, 55.862160),
    "el centro,usa": (-115.563050, 32.792000),
    "gaojia,china": (107.860000, 30.020350),
    "rego park,usa": (-73.852640, 40.726490),
    "caijia,china": (106.340400, 28.908890),
    "sutton in ashfield,uk": (-1.261350, 53.125420),
    "north brunswick,usa": (-74.482000, 40.454000),
    "grantham,uk": (-0.641840, 52.911490),
    "echo park,usa": (-118.260660, 34.078080),
    "north bethesda,usa": (-77.118870, 39.044550),
    "merthyr tydfil,uk": (-3.377790, 51.747940),
    "kalihi-palama,usa": (-157.875940, 21.326080),
    "lombard,usa": (-88.007840, 41.880030),
    "great sankey,uk": (-2.639940, 53.392340),
    "bountiful,usa": (-111.880770, 40.889390),
    "rizhuang,china": (120.383060, 36.950830),
    "han'airike,china": (80.117350, 37.541740),
    "north lauderdale,usa": (-80.225880, 26.217300),
    "shihao,china": (106.680690, 28.540820),
    "ashton-under-lyne,uk": (-2.098900, 53.488760),
    "jingguan,china": (106.563900, 29.895450),
    "erlin,taiwan": (120.368900, 23.900540),
    "leigh,uk": (-2.519730, 53.496420),
    "burleson,usa": (-97.320850, 32.542080),
    "ocoee,usa": (-81.543960, 28.569170),
    "leatherhead,uk": (-0.333800, 51.296520),
    "letchworth garden city,uk": (-0.226640, 51.979380),
    "juexi,china": (104.261540, 28.924100),
    "ashburn,usa": (-77.487490, 39.043720),
    "southington,usa": (-72.877600, 41.596490),
    "augusta,usa": (-81.974840, 33.470970),
    "gaozuo,china": (118.039720, 33.903060),
    "bozeman,usa": (-111.038560, 45.679650),
    "newark on trent,uk": (-0.816670, 53.066670),
    "sierra vista,usa": (-110.303690, 31.554540),
    "freeport,usa": (-73.583180, 40.657600),
    "pittsfield,usa": (-73.245380, 42.450080),
    "hilo,usa": (-155.090730, 19.729910),
    "worksop,uk": (-1.124040, 53.301820),
    "west babylon,usa": (-73.354290, 40.718160),
    "kuiya,china": (79.635750, 37.296010),
    "dekalb,usa": (-88.750360, 41.929470),
    "san bruno,usa": (-122.411080, 37.630490),
    "altamonte springs,usa": (-81.365620, 28.661110),
    "zhigou,china": (119.216670, 35.916670),
    "bowangshan,china": (105.052200, 28.307660),
    "bell gardens,usa": (-118.151460, 33.965290),
    "schertz,usa": (-98.269730, 29.552170),
    "east boston,usa": (-71.039220, 42.375100),
    "huangji,china": (116.983330, 34.433330),
    "zhengji,china": (117.038890, 34.437220),
    "jiangping,china": (108.150000, 21.600000),
    "morgan hill,usa": (-121.654390, 37.130500),
    "bothell,usa": (-122.205400, 47.762320),
    "fond du lac,usa": (-88.438830, 43.775000),
    "baichihe,china": (119.533330, 36.115560),
    "sicklerville,usa": (-74.969330, 39.717340),
    "sayreville junction,usa": (-74.330430, 40.465380),
    "farmington,usa": (-108.218690, 36.728060),
    "tushan,china": (117.836940, 34.220830),
    "bury st edmunds,uk": (0.711110, 52.246300),
    "la jolla,usa": (-117.274200, 32.847270),
    "altadena,usa": (-118.131180, 34.189730),
    "guandu,china": (109.846970, 30.955890),
    "kirkby,uk": (-2.892150, 53.481380),
    "wallsend,uk": (-1.533970, 54.991110),
    "rancho palos verdes,usa": (-118.387020, 33.744460),
    "north highlands,usa": (-121.372170, 38.685740),
    "redruth,uk": (-5.224340, 50.233150),
    "moline,usa": (-90.515130, 41.506700),
    "east concord,usa": (-71.538130, 43.242020),
    "jefferson city,usa": (-92.173520, 38.576700),
    "henrietta,usa": (-77.612220, 43.059230),
    "pu'an,china": (105.466860, 32.037280),
    "rockwall,usa": (-96.459710, 32.931230),
    "kai tak,china": (114.197410, 22.324250),
    "luobuqiongzi,china": (89.250000, 29.166670),
    "welling,uk": (0.107590, 51.462460),
    "e'erguna,china": (120.170920, 50.223620),
    "daizhuang,china": (117.852780, 34.513890),
    "rohnert park,usa": (-122.701100, 38.339640),
    "christchurch,uk": (-1.781290, 50.735830),
    "qushi,china": (98.600000, 25.216670),
    "urbana,usa": (-88.207270, 40.110590),
    "andover,uk": (-1.493930, 51.211350),
    "southglenn,usa": (-104.952760, 39.587210),
    "mali,china": (104.697810, 34.664630),
    "malianzhuang,china": (120.462510, 37.074840),
    "prescott valley,usa": (-112.315720, 34.610020),
    "joint base pearl harbor hickam,usa": (-157.947130, 21.349060),
    "state college,usa": (-77.860000, 40.793390),
    "kearny,usa": (-74.145420, 40.768430),
    "luobei,china": (130.813110, 47.576020),
    "el dorado hills,usa": (-121.082170, 38.685740),
    "tieqiao,china": (108.133620, 31.040010),
    "belleville,usa": (-89.983990, 38.520050),
    "wangyuan,china": (106.272000, 38.384080),
    "linden,usa": (-74.244590, 40.622050),
    "moorhead,usa": (-96.769510, 46.873860),
    "gutao,china": (112.178060, 37.202500),
    "woodside,usa": (-73.905410, 40.745380),
    "stretford,uk": (-2.316670, 53.450000),
    "brea,usa": (-117.900060, 33.916680),
    "riverton,usa": (-111.939100, 40.521890),
    "prescott,usa": (-112.468500, 34.540020),
    "mount laurel,usa": (-74.891000, 39.934000),
    "quxu,china": (90.732140, 29.355400),
    "yinggen,china": (109.840000, 19.038330),
    "wuduan,china": (117.095280, 34.574440),
    "the colony,usa": (-96.886390, 33.089010),
    "manassas,usa": (-77.475270, 38.750950),
    "tiancheng,china": (108.369690, 30.867610),
    "linshi,china": (107.192330, 29.666980),
    "dover,uk": (1.312570, 51.125980),
    "westfield,usa": (-72.749540, 42.125090),
    "hatfield,uk": (-0.224190, 51.763380),
    "shiji,china": (118.483330, 34.200000),
    "naliang,china": (107.866670, 21.666670),
    "baihua,china": (104.608520, 29.094220),
    "hutchinson,usa": (-97.929770, 38.060840),
    "leominster,usa": (-71.759790, 42.525090),
    "catonsville,usa": (-76.731920, 39.272050),
    "altrincham,uk": (-2.348480, 53.387520),
    "hicksville,usa": (-73.525130, 40.768430),
    "jordan,china": (114.170010, 22.305390),
    "buffalo grove,usa": (-87.959790, 42.151410),
    "guye,china": (118.450690, 39.740830),
    "woonsocket,usa": (-71.514780, 42.002880),
    "west hills,usa": (-118.643980, 34.197310),
    "xinglong,china": (109.445990, 30.657230),
    "edmonds,usa": (-122.377360, 47.810650),
    "laisu,china": (105.778020, 29.265970),
    "coity,uk": (-3.555310, 51.522000),
    "newburn,uk": (-1.744150, 54.987600),
    "boston,uk": (-0.026640, 52.976330),
    "holloway,uk": (-0.124970, 51.552370),
    "lytham st annes,uk": (-2.997000, 53.742600),
    "chengxi,china": (107.258900, 30.209210),
    "marana,usa": (-111.225380, 32.436740),
    "shelton,usa": (-73.093160, 41.316490),
    "greenock,uk": (-4.761210, 55.948380),
    "bridgwater,uk": (-3.003560, 51.128370),
    "cedar falls,usa": (-92.445470, 42.527760),
    "chatsworth,usa": (-118.601200, 34.257230),
    "chongxing,china": (106.300000, 38.033330),
    "gage park,usa": (-87.696160, 41.795030),
    "urmston,uk": (-2.354190, 53.448520),
    "beverly,usa": (-70.880050, 42.558430),
    "university,usa": (-82.439020, 28.073890),
    "coppell,usa": (-97.015010, 32.954570),
    "findlay,usa": (-83.649930, 41.044220),
    "wokingham,uk": (-0.835650, 51.411200),
    "xunsi,china": (104.560630, 28.100770),
    "campbell,usa": (-121.949960, 37.287170),
    "baisheng,china": (107.392610, 29.813510),
    "lake ridge,usa": (-77.297760, 38.687890),
    "burke,usa": (-77.271650, 38.793450),
    "mankato,usa": (-94.009150, 44.159060),
    "tuxiang,china": (109.155560, 30.712930),
    "annandale,usa": (-77.196370, 38.830390),
    "covington,usa": (-84.508550, 39.083670),
    "new city,usa": (-87.656440, 41.807530),
    "morris heights,usa": (-73.919860, 40.849820),
    "peachtree corners,usa": (-84.221590, 33.970100),
    "south valley,usa": (-106.678080, 35.010050),
    "ormond beach,usa": (-81.055890, 29.285810),
    "swadlincote,uk": (-1.557440, 52.774000),
    "trowbridge,uk": (-2.208610, 51.318890),
    "carrollwood village,usa": (-82.520930, 28.067520),
    "nanmen,china": (108.243270, 30.961870),
    "baihe,china": (108.463720, 31.263480),
    "ka'ersai,china": (79.595620, 37.484190),
    "prescot,uk": (-2.800310, 53.429480),
    "venice,usa": (-118.460080, 33.990840),
    "anyuan,china": (105.276390, 34.880830),
    "sumter,usa": (-80.341470, 33.920440),
    "annapolis,usa": (-76.491840, 38.978590),
    "wilkes-barre,usa": (-75.881310, 41.245910),
    "lincoln square,usa": (-87.689220, 41.975870),
    "la puente,usa": (-117.949510, 34.020010),
    "xili,china": (113.947860, 22.588090),
    "holyoke,usa": (-72.616200, 42.204260),
    "sherman,usa": (-96.608880, 33.635660),
    "goose creek,usa": (-80.032590, 32.981010),
    "luolong,china": (104.899060, 28.805570),
    "maplewood,usa": (-92.995220, 44.953020),
    "streamwood,usa": (-88.178410, 42.025580),
    "fitchburg,usa": (-71.802300, 42.583420),
    "hilton head island,usa": (-80.738160, 32.193820),
    "bexhill-on-sea,uk": (0.470950, 50.850230),
    "la quinta,usa": (-116.310010, 33.663360),
    "buzi,taiwan": (120.572500, 24.210130),
    "crystal lake,usa": (-88.316200, 42.241130),
    "hagerstown,usa": (-77.719990, 39.641760),
    "sihu,china": (117.971390, 34.626250),
    "san gabriel,usa": (-118.105830, 34.096110),
    "yew tee,singapore": (103.747380, 1.396650),
    "hickory,usa": (-81.341200, 35.733190),
    "mutang,china": (109.345390, 19.807550),
    "beverly cove,usa": (-70.853660, 42.553430),
    "pat heung,china": (114.092260, 22.446100),
    "winter garden,usa": (-81.586180, 28.565280),
    "carol stream,usa": (-88.134790, 41.912530),
    "yuntai,china": (107.204870, 30.138940),
    "anfu,china": (105.467420, 29.359370),
    "marlboro,usa": (-74.246260, 40.315390),
    "nanshu,china": (120.337310, 37.020140),
    "teaneck,usa": (-74.015970, 40.897600),
    "calexico,usa": (-115.498880, 32.678950),
    "florence,usa": (-87.677250, 34.799810),
    "bloxwich,uk": (-2.004310, 52.618060),
    "st. johns,usa": (-81.547740, 30.081500),
    "gangtou,china": (118.207190, 34.317430),
    "ewell,uk": (-0.249400, 51.349480),
    "shakopee,usa": (-93.526900, 44.798020),
    "zhaojia,china": (108.411640, 31.081250),
    "shuanghuai,china": (106.555800, 30.184160),
    "billerica,usa": (-71.268950, 42.558430),
    "norwich,usa": (-72.075910, 41.524260),
    "mingshan,china": (107.699210, 29.878320),
    "chenshi,china": (105.992650, 29.314460),
    "duncanville,usa": (-96.908340, 32.651800),
    "new berlin,usa": (-88.108420, 42.976400),
    "marlborough,usa": (-71.552290, 42.345930),
    "oakley,usa": (-121.712450, 37.997420),
    "sanjiang,china": (106.710560, 28.944720),
    "chenghai,china": (100.678620, 26.461720),
    "sawtelle,usa": (-118.449490, 34.036300),
    "north shields,uk": (-1.449250, 55.016460),
    "baojia,china": (108.313240, 29.438690),
    "shepherds bush,uk": (-0.221100, 51.505000),
    "romeoville,usa": (-88.089510, 41.647530),
    "culver city,usa": (-118.396470, 34.021120),
    "montclair,usa": (-74.209030, 40.825930),
    "liji,china": (117.783330, 33.766670),
    "puyallup,usa": (-122.292900, 47.185380),
    "shichuan,china": (106.822840, 29.765840),
    "huixian chengguanzhen,china": (106.080830, 33.768330),
    "woburn,usa": (-71.152280, 42.479260),
    "bremerton,usa": (-122.632640, 47.567320),
    "hallandale beach,usa": (-80.148380, 25.981200),
    "weslaco,usa": (-97.990840, 26.159520),
    "cape girardeau,usa": (-89.518150, 37.305880),
    "simei new town,singapore": (103.956110, 1.341110),
    "bullhead city,usa": (-114.568300, 35.147780),
    "north fort myers,usa": (-81.880090, 26.667290),
    "dover,usa": (-75.524370, 39.158170),
    "wenquan,china": (108.522240, 31.359110),
    "chelsea,usa": (-71.032830, 42.391760),
    "grove city,usa": (-83.092960, 39.881450),
    "keat hong village,singapore": (103.744170, 1.377780),
    "zhuyuan,china": (109.258060, 31.302160),
    "xilinji,china": (123.235220, 52.990630),
    "princeton,usa": (-80.408940, 25.538440),
    "mangbang,china": (98.670100, 24.931900),
    "lequn,china": (113.873850, 22.577640),
    "essex,usa": (-76.474960, 39.309270),
    "atlantic city,usa": (-74.423060, 39.364150),
    "pacifica,usa": (-122.486920, 37.613830),
    "baishikante,china": (77.479040, 38.459640),
    "northglenn,usa": (-104.987200, 39.885540),
    "far rockaway,usa": (-73.755130, 40.605380),
    "olney,usa": (-75.123790, 40.041220),
    "whampoa,china": (114.190210, 22.305040),
    "kensington,usa": (-73.970690, 40.646210),
    "coram,usa": (-73.001490, 40.868710),
    "wausau,usa": (-89.630120, 44.959140),
    "jinzhongzi,china": (119.258070, 36.334570),
    "hurst,usa": (-97.170570, 32.823460),
    "shili,china": (105.292470, 33.951820),
    "skelmersdale,uk": (-2.773480, 53.550240),
    "balu,china": (117.912650, 34.188680),
    "stanton,usa": (-117.993120, 33.802520),
    "renyi,china": (105.478270, 29.507430),
    "gongping,china": (109.197220, 31.126950),
    "aliamanu / salt lakes / foster village,usa": (-157.918380, 21.360220),
    "friendswood,usa": (-95.201040, 29.529400),
    "fleet,uk": (-0.833330, 51.283330),
    "the acreage,usa": (-80.267490, 26.794040),
    "west oak lane,usa": (-75.166290, 40.069280),
    "taibao,taiwan": (120.332220, 23.459440),
    "abingdon,uk": (-1.282780, 51.671090),
    "tonbridge,uk": (0.273630, 51.195320),
    "kailua,usa": (-157.740540, 21.402410),
    "ramsgate,uk": (1.417970, 51.335680),
    "rock island,usa": (-90.578750, 41.509480),
    "ilkeston,uk": (-1.309510, 52.970550),
    "whitney,usa": (-115.036300, 36.098310),
    "bailin,china": (106.460430, 28.735990),
    "oviedo,usa": (-81.208120, 28.670000),
    "carpentersville,usa": (-88.257860, 42.121140),
    "manhattan valley,usa": (-73.965000, 40.793890),
    "lake oswego,usa": (-122.670650, 45.420670),
    "muskogee,usa": (-95.369690, 35.747880),
    "jiachuan,china": (106.214940, 32.209070),
    "hobbs,usa": (-103.136040, 32.702610),
    "choi wan,china": (114.213680, 22.333850),
    "muskegon,usa": (-86.248390, 43.234180),
    "hetoudian,china": (120.573720, 37.018370),
    "xihu,china": (106.395360, 29.100230),
    "westerville,usa": (-82.929070, 40.126170),
    "glenrothes,uk": (-3.173160, 56.195140),
    "anxiang,china": (114.540460, 38.383390),
    "little elm,usa": (-96.937510, 33.162620),
    "hanover park,usa": (-88.145070, 41.999470),
    "hillsborough,usa": (-74.626820, 40.477600),
    "channelview,usa": (-95.114650, 29.776060),
    "panama city,usa": (-85.659830, 30.159460),
    "coalville,uk": (-1.370200, 52.722470),
    "waipahu,usa": (-158.009170, 21.386670),
    "wake forest,usa": (-78.509720, 35.979870),
    "huber heights,usa": (-84.124660, 39.843950),
    "canvey island,uk": (0.580900, 51.521990),
    "zhancheng,china": (117.762910, 34.175010),
    "surbiton,uk": (-0.298250, 51.391480),
    "miaozi,china": (118.231380, 36.638600),
    "martinez,usa": (-122.134130, 38.019370),
    "east meadow,usa": (-73.559020, 40.713990),
    "weixinghu,china": (105.880010, 29.244500),
    "hegeng,china": (105.869880, 29.136960),
    "hanover,usa": (-76.724140, 39.192890),
    "wheeling,usa": (-87.928960, 42.139190),
    "apache junction,usa": (-111.549580, 33.415050),
    "whitley bay,uk": (-1.447130, 55.039730),
    "pleasant grove,usa": (-111.738540, 40.364120),
    "brookfield,usa": (-88.106480, 43.060570),
    "greenford,uk": (-0.355080, 51.528660),
    "columbia heights,usa": (-77.029420, 38.925670),
    "delaware,usa": (-83.067970, 40.298670),
    "roy,usa": (-112.026330, 41.161610),
    "valley stream,usa": (-73.708460, 40.664270),
    "spanish fork,usa": (-111.654920, 40.114960),
    "stirling,uk": (-3.936820, 56.119030),
    "keizer,usa": (-123.026210, 44.990120),
    "woodlawn,usa": (-76.728030, 39.322880),
    "arnold,uk": (-1.133330, 53.000000),
    "lima,usa": (-84.105230, 40.742550),
    "spartanburg,usa": (-81.932050, 34.949570),
    "houghton-le-spring,uk": (-1.464270, 54.840340),
    "changshouhu,china": (107.237890, 29.905360),
    "bishops stortford,uk": (0.158680, 51.871130),
    "hermitage,usa": (-86.622500, 36.196170),
    "park ridge,usa": (-87.840620, 42.011140),
    "fenway/kenmore,usa": (-71.100170, 42.344910),
    "jinshan,china": (105.434440, 34.811390),
    "shahe,china": (113.979120, 22.552260),
    "winter haven,usa": (-81.732860, 28.022240),
    "aventura,usa": (-80.139210, 25.956480),
    "severna park,usa": (-76.545240, 39.070390),
    "royal palm beach,usa": (-80.230600, 26.708400),
    "leyland,uk": (-2.687580, 53.697860),
    "chadderton,uk": (-2.139840, 53.544800),
    "rushden,uk": (-0.601840, 52.289270),
    "phenix city,usa": (-85.000770, 32.470980),
    "milton,usa": (-84.300670, 34.132160),
    "jincheng,taiwan": (118.317120, 24.434150),
    "sun city,usa": (-112.271820, 33.597540),
    "lake worth beach,usa": (-80.072310, 26.617080),
    "kew gardens hills,usa": (-73.823400, 40.730020),
    "leighton buzzard,uk": (-0.658020, 51.917220),
    "jamaica plain,usa": (-71.120330, 42.309820),
    "monrovia,usa": (-117.998950, 34.148060),
    "hollister,usa": (-121.401600, 36.852450),
    "los banos,usa": (-120.849920, 37.058280),
    "sewell,usa": (-75.144340, 39.766500),
    "yingpan,china": (99.150000, 26.450000),
    "plant city,usa": (-82.114690, 28.018880),
    "yihe,china": (107.219180, 29.737340),
    "yeadon,uk": (-1.687430, 53.864370),
    "greenfield,usa": (-88.012590, 42.961400),
    "blyth,uk": (-1.508560, 55.127080),
    "marion,usa": (-91.597680, 42.034170),
    "gecheng,china": (108.660730, 31.948560),
    "mei foo sun chuen,china": (114.140180, 22.336360),
    "braintree,usa": (-71.002150, 42.203840),
    "newnan,usa": (-84.799660, 33.380670),
    "texarkana,usa": (-94.047690, 33.425130),
    "eccles,uk": (-2.333330, 53.483330),
    "warwick,uk": (-1.583330, 52.283330),
    "tsz wan shan,china": (114.200160, 22.352470),
    "jelilyuezi,china": (81.535550, 43.974900),
    "addison,usa": (-87.988960, 41.931700),
    "redcar,uk": (-1.059990, 54.616570),
    "xiluo,taiwan": (120.463370, 23.798910),
    "reynoldsburg,usa": (-82.812120, 39.954790),
    "kaki bukit estate,singapore": (103.909170, 1.337500),
    "south jordan heights,usa": (-111.949380, 40.563840),
    "odenton,usa": (-76.700250, 39.084000),
    "airdrie,uk": (-3.980250, 55.866020),
    "mableton,usa": (-84.582430, 33.818720),
    "hilton head,usa": (-80.752610, 32.216320),
    "grants pass,usa": (-123.330670, 42.439330),
    "wayao,china": (118.233330, 34.383330),
    "tange,china": (104.840620, 34.627640),
    "indian trail,usa": (-80.669240, 35.076810),
    "heston,uk": (-0.375770, 51.483630),
    "calumet city,usa": (-87.529490, 41.615590),
    "peterlee,uk": (-1.336490, 54.760320),
    "yuanyang,china": (106.557490, 29.665720),
    "guojia,china": (105.558380, 34.972760),
    "lynnwood,usa": (-122.315130, 47.820930),
    "whitestone,usa": (-73.818470, 40.794550),
    "farnham,uk": (-0.800540, 51.214440),
    "chester-le-street,uk": (-1.574080, 54.858620),
    "biyang,china": (117.946380, 29.928850),
    "beloit,usa": (-89.031780, 42.508350),
    "dunhao,china": (108.358200, 31.333010),
    "luoqi,china": (106.932060, 29.722350),
    "qina,china": (100.625130, 26.309380),
    "elixku,china": (77.370560, 38.709170),
    "great malvern,uk": (-2.325150, 52.111610),
    "south miami heights,usa": (-80.380610, 25.597610),
    "new albany,usa": (-85.824130, 38.285620),
    "liufeng,china": (105.386090, 34.734530),
    "clifton park,usa": (-73.770950, 42.865630),
    "mudong,china": (106.839280, 29.573340),
    "bake,china": (107.022900, 29.900590),
    "zhiping,china": (106.358560, 29.258310),
    "fort lee,usa": (-73.970140, 40.850930),
    "stratford,uk": (0.000000, 51.533330),
    "herne bay,uk": (1.128570, 51.373000),
    "wilmslow,uk": (-2.231480, 53.328030),
    "bartlesville,usa": (-95.980820, 36.747310),
    "dadamtu,china": (81.314170, 43.980280),
    "shetou,taiwan": (120.588310, 23.898040),
    "xianlong,china": (105.784030, 29.151070),
    "ewing,usa": (-74.799880, 40.269830),
    "san juan,usa": (-98.155290, 26.189240),
    "woodhaven,usa": (-73.857910, 40.689270),
    "hang hau,china": (114.269940, 22.318110),
    "haomen,china": (101.621990, 37.375750),
    "mission bend,usa": (-95.664950, 29.693840),
    "newton abbot,uk": (-3.611860, 50.528580),
    "san juan capistrano,usa": (-117.662550, 33.501690),
    "pahrump,usa": (-115.983910, 36.208290),
    "mangotsfield,uk": (-2.504030, 51.487800),
    "luhuan,china": (113.551940, 22.118060),
    "temple city,usa": (-118.057850, 34.107230),
    "mechanicsville,usa": (-77.373310, 37.608760),
    "billericay,uk": (0.419630, 51.628670),
    "lufkin,usa": (-94.729100, 31.338240),
    "pennsauken,usa": (-75.057950, 39.956220),
    "rome,usa": (-85.164670, 34.257040),
    "mattapan,usa": (-71.087000, 42.272320),
    "longxing,china": (106.791100, 29.701990),
    "claremont,usa": (-117.719780, 34.096680),
    "dachang,china": (109.802100, 31.268610),
    "richfield,usa": (-93.283000, 44.883300),
    "bell,usa": (-118.187020, 33.977510),
    "lewiston,usa": (-70.214780, 44.100350),
    "dunedin,usa": (-82.773230, 28.019900),
    "kendall west,usa": (-80.438800, 25.706500),
    "del rio,usa": (-100.896760, 29.362730),
    "oakville,usa": (-90.304560, 38.470050),
    "commack,usa": (-73.292890, 40.842880),
    "menomonee falls,usa": (-88.117310, 43.178900),
    "chipping sodbury,uk": (-2.393790, 51.538130),
    "moorpark,usa": (-118.882040, 34.285560),
    "hitchin,uk": (-0.284960, 51.949240),
    "gadsden,usa": (-86.006390, 34.014340),
    "issaquah,usa": (-122.032620, 47.530100),
    "serangoon garden,singapore": (103.857500, 1.363890),
    "weituo,china": (106.147010, 30.039830),
    "trumbull,usa": (-73.200670, 41.242870),
    "olive branch,usa": (-89.829530, 34.961760),
    "mooresville,usa": (-80.810070, 35.584860),
    "west torrington,usa": (-73.143720, 41.818430),
    "willowbrook,usa": (-118.255070, 33.916960),
    "leavenworth,usa": (-94.922460, 39.311110),
    "clinton,usa": (-76.898310, 38.765110),
    "walkden,uk": (-2.400000, 53.516670),
    "tyldesley,uk": (-2.467540, 53.513930),
    "cottage grove,usa": (-92.943820, 44.827740),
    "wildwood,usa": (-90.662900, 38.582830),
    "richmond west,usa": (-80.429710, 25.610500),
    "sanmiao,china": (106.127040, 30.237630),
    "oregon city,usa": (-122.606760, 45.357340),
    "goldsboro,usa": (-77.992770, 35.384880),
    "manhattan beach,usa": (-118.410910, 33.884740),
    "parkland,usa": (-122.434010, 47.155380),
    "chippenham,uk": (-2.124720, 51.460000),
    "sai kung,china": (114.266670, 22.383330),
    "zhutang,china": (99.807150, 22.715200),
    "east florence,usa": (-87.649470, 34.809530),
    "kyle,usa": (-97.877230, 29.989110),
    "kearns,usa": (-111.996330, 40.659950),
    "linton hall,usa": (-77.574990, 38.759840),
    "billingham,uk": (-1.290340, 54.588810),
    "longhe,china": (107.985080, 29.839570),
    "pontypool,uk": (-3.044440, 51.701110),
    "tupelo,usa": (-88.704640, 34.258070),
    "shimen,china": (106.033040, 29.100370),
    "hot springs,usa": (-93.055180, 34.503700),
    "wildomar,usa": (-117.280040, 33.598910),
    "wentzville,usa": (-90.852910, 38.811440),
    "caijiagang,china": (106.475080, 29.742480),
    "valrico,usa": (-82.236440, 27.937890),
    "coventry,usa": (-71.682840, 41.700100),
    "kangle,china": (109.429640, 31.112780),
    "rosenberg,usa": (-95.808560, 29.557180),
    "bettendorf,usa": (-90.515690, 41.524480),
    "ziyang chengguanzhen,china": (108.532320, 32.519170),
    "east point,usa": (-84.439370, 33.679550),
    "prattville,usa": (-86.459700, 32.464020),
    "ponte vedra beach,usa": (-81.385640, 30.239690),
    "boardman,usa": (-80.662850, 41.024230),
    "tai koo,china": (114.216310, 22.284100),
    "shidui,china": (119.308610, 36.393330),
    "yongjing,taiwan": (120.545940, 23.921480),
    "cooper city,usa": (-80.271720, 26.057310),
    "mapo,china": (117.066670, 34.516670),
    "oxon hill-glassmanor,usa": (-76.974990, 38.796150),
    "langao chengguanzhen,china": (108.893060, 32.300280),
    "accrington,uk": (-2.358630, 53.753790),
    "falkirk,uk": (-3.785350, 56.002100),
    "egypt lake-leto,usa": (-82.506190, 28.017690),
    "north lawndale,usa": (-87.718390, 41.860030),
    "oak creek,usa": (-87.863140, 42.885850),
    "peachtree city,usa": (-84.595760, 33.396780),
    "merrillville,usa": (-87.332810, 41.482810),
    "briton ferry,uk": (-3.818980, 51.631060),
    "hoddesdon,uk": (-0.011440, 51.761480),
    "bridlington,uk": (-0.191920, 54.083060),
    "la porte,usa": (-95.019370, 29.665780),
    "puqiakeqi,china": (79.705320, 37.317390),
    "heqiao,china": (116.900000, 34.452780),
    "university city,usa": (-90.309280, 38.655880),
    "yizhuang,china": (117.593670, 34.156510),
    "baiyang,china": (108.610980, 30.816400),
    "miaoyu,china": (109.646140, 30.868680),
    "upper arlington,usa": (-83.062410, 39.994510),
    "torrington,usa": (-73.121220, 41.800650),
    "tianzhong,taiwan": (120.585700, 23.858080),
    "beverly hills,usa": (-118.400360, 34.073620),
    "inver grove heights,usa": (-93.042720, 44.848020),
    "cumberland,usa": (-71.432840, 41.966770),
    "bayview-hunters point,usa": (-122.381070, 37.728550),
    "bentley,uk": (-1.150000, 53.533330),
    "pleasant hill,usa": (-122.060800, 37.947980),
    "taikoo shing,china": (114.218700, 22.286130),
    "stow,usa": (-81.440390, 41.159500),
    "lauderdale lakes,usa": (-80.208380, 26.166470),
    "la vergne,usa": (-86.581940, 36.015620),
    "winter springs,usa": (-81.308120, 28.698890),
    "yau tong,china": (114.235990, 22.295690),
    "merritt island,usa": (-80.690000, 28.359000),
    "greenpoint,usa": (-73.950970, 40.723710),
    "west little river,usa": (-80.236990, 25.857040),
    "brunswick,usa": (-81.841800, 41.238110),
    "huangdi,china": (77.448610, 38.808980),
    "haitou,china": (108.950540, 19.505630),
    "guxi,china": (105.872080, 30.330260),
    "san dimas,usa": (-117.806730, 34.106680),
    "north center,usa": (-87.678950, 41.953920),
    "queen creek,usa": (-111.634300, 33.248660),
    "kaneohe,usa": (-157.798950, 21.399940),
    "gahanna,usa": (-82.879340, 40.019230),
    "leawood,usa": (-94.616900, 38.966670),
    "tage'erqi,china": (77.257320, 38.545160),
    "wujia,china": (105.391100, 29.634820),
    "owasso,usa": (-95.854710, 36.269540),
    "longqiao,china": (107.294370, 29.710340),
    "derry village,usa": (-71.312010, 42.891750),
    "wuying,china": (105.898800, 35.014850),
    "central islip,usa": (-73.201780, 40.790650),
    "lianhua,china": (105.791080, 35.061600),
    "exmouth,uk": (-3.402330, 50.617230),
    "norristown,usa": (-75.339900, 40.121500),
    "lower west side,usa": (-87.665610, 41.854200),
    "yate,uk": (-2.418390, 51.540740),
    "dyker heights,usa": (-74.009580, 40.621490),
    "felling,uk": (-1.571520, 54.952970),
    "cottonwood heights,usa": (-111.810210, 40.619670),
    "chiswick,uk": (-0.258010, 51.492710),
    "gallatin,usa": (-86.446660, 36.388380),
    "xinmiao,china": (107.049880, 29.655280),
    "houma,usa": (-90.719530, 29.595770),
    "colwyn bay,uk": (-3.726740, 53.294830),
    "rubidoux,usa": (-117.405600, 33.996130),
    "zhelou,china": (105.816670, 24.966670),
    "radcliffe,uk": (-2.324550, 53.561780),
    "collinwood,usa": (-81.569290, 41.558380),
    "glendale heights,usa": (-88.064860, 41.914600),
    "butte,usa": (-112.534740, 46.003820),
    "dana point,usa": (-117.698110, 33.466970),
    "benton,usa": (-92.586830, 34.564540),
    "vestavia hills,usa": (-86.787770, 33.448720),
    "totton,uk": (-1.490370, 50.918770),
    "la presa,usa": (-116.997250, 32.708110),
    "oakton,usa": (-77.300820, 38.880950),
    "xintian,china": (108.401930, 30.698660),
    "irvine,uk": (-4.655080, 55.619400),
    "zhuxi,china": (105.666850, 29.536140),
    "chester,usa": (-75.357850, 39.847530),
    "studio city,usa": (-118.396470, 34.148620),
    "salisbury,usa": (-80.474230, 35.670970),
    "riviera beach,usa": (-80.058100, 26.775340),
    "liushan,china": (118.760160, 36.449720),
    "luefeng,china": (105.973060, 29.858340),
    "orangevale,usa": (-121.225780, 38.678510),
    "oswego,usa": (-88.351460, 41.682810),
    "yawa,china": (79.514290, 37.411900),
    "el mirage,usa": (-112.324600, 33.613090),
    "west lake sammamish,usa": (-122.101230, 47.577600),
    "north bel air,usa": (-76.354960, 39.539830),
    "chelmsford,usa": (-71.367280, 42.599810),
    "bay city,usa": (-83.888860, 43.594470),
    "nacogdoches,usa": (-94.655490, 31.603510),
    "shrewsbury,usa": (-71.712850, 42.295930),
    "mcminnville,usa": (-123.198720, 45.210120),
    "chorley,uk": (-2.616670, 53.650000),
    "peng siang,singapore": (103.740660, 1.379950),
    "dalton,usa": (-84.970220, 34.769800),
    "bicester,uk": (-1.153570, 51.899980),
    "haywards heath,uk": (-0.103130, 50.997690),
    "north providence,usa": (-71.466170, 41.850100),
    "oak hill,usa": (-77.401560, 38.925800),
    "deer park,usa": (-95.123820, 29.705230),
    "tai kok tsui,china": (114.163000, 22.321460),
    "shuangjiang,china": (105.745200, 30.217540),
    "holland,usa": (-86.108930, 42.787520),
    "wigston magna,uk": (-1.092480, 52.581280),
    "shuanghekou,china": (108.369580, 30.753980),
    "throgs neck,usa": (-73.819580, 40.822600),
    "northbrook,usa": (-87.828950, 42.127530),
    "hilliard,usa": (-83.158250, 40.033400),
    "wenatchee,usa": (-120.310350, 47.423460),
    "fuxing,china": (106.557140, 29.819050),
    "west fargo,usa": (-96.900360, 46.874970),
    "fair lawn,usa": (-74.131810, 40.940380),
    "kennesaw,usa": (-84.615490, 34.023430),
    "wednesfield,uk": (-2.085080, 52.596300),
    "suitland-silver hill,usa": (-76.925910, 38.846850),
    "chillum,usa": (-76.990810, 38.963720),
    "foster city,usa": (-122.271080, 37.558550),
    "mawang,china": (108.951140, 28.893310),
    "shetan,china": (107.615210, 29.989240),
    "fairborn,usa": (-84.019380, 39.820890),
    "menlo park,usa": (-122.182190, 37.453830),
    "chicago loop,usa": (-87.633300, 41.884070),
    "cibolo,usa": (-98.226960, 29.561620),
    "lawndale,usa": (-118.352570, 33.887240),
    "hinesville,usa": (-81.595950, 31.846880),
    "waxahachie,usa": (-96.848330, 32.386530),
    "strood,uk": (0.477130, 51.393230),
    "st. charles,usa": (-76.924780, 38.607280),
    "cobbs creek,usa": (-75.240180, 39.947610),
    "woodridge,usa": (-88.050340, 41.746970),
    "carrollwood,usa": (-82.492870, 28.050020),
    "windsor,uk": (-0.600000, 51.483330),
    "beigang,taiwan": (120.301620, 23.570100),
    "beidou,taiwan": (120.524260, 23.872920),
    "shuangfeng,china": (106.429630, 30.023330),
    "somerton,usa": (-75.014890, 40.123440),
    "glossop,uk": (-1.949000, 53.443250),
    "elk grove village,usa": (-87.970350, 42.003920),
    "pekin,usa": (-89.640660, 40.567540),
    "socorro,usa": (-106.303310, 31.654560),
    "elmont,usa": (-73.712910, 40.700940),
    "cramlington,uk": (-1.585980, 55.086520),
    "xiongjia,china": (108.433670, 30.901550),
    "adelanto,usa": (-117.409220, 34.582770),
    "tooele,usa": (-112.298280, 40.530780),
    "golden glades,usa": (-80.200330, 25.911760),
    "marrero,usa": (-90.100350, 29.899370),
    "baocheng,china": (109.699440, 18.640280),
    "bayandai,china": (81.248520, 43.965860),
    "foothill farms,usa": (-121.351140, 38.678770),
    "pudsey,uk": (-1.661340, 53.795380),
    "sao lazaro,china": (113.548950, 22.199900),
    "englewood,usa": (-104.987760, 39.647770),
    "copperas cove,usa": (-97.903080, 31.124060),
    "bath beach,usa": (-74.004310, 40.604550),
    "ebbw vale,uk": (-3.207920, 51.777140),
    "newbury,uk": (-1.324710, 51.401480),
    "huntington station,usa": (-73.411510, 40.853430),
    "seaside,usa": (-121.851620, 36.611070),
    "kearney,usa": (-99.081480, 40.699460),
    "redan,usa": (-84.131580, 33.745380),
    "manitowoc,usa": (-87.657580, 44.088610),
    "williamsburg,usa": (-73.953470, 40.714270),
    "ronglong,china": (105.448650, 29.435890),
    "goshen,usa": (-85.834440, 41.582270),
    "shawei,china": (114.033780, 22.519960),
    "wickford,uk": (0.523310, 51.611010),
    "jukui,china": (107.596330, 30.635880),
    "greenacres city,usa": (-80.125320, 26.623680),
    "kiryas joel,usa": (-74.167920, 41.342040),
    "washwood heath,uk": (-1.826570, 52.500540),
    "douglasville,usa": (-84.747710, 33.751500),
    "silver lake,usa": (-118.270230, 34.086680),
    "security-widefield,usa": (-104.714390, 38.747280),
    "lichfield,uk": (-1.825490, 52.681540),
    "brighouse,uk": (-1.784280, 53.703220),
    "wuhe,china": (98.667830, 24.859060),
    "university place,usa": (-122.550400, 47.235650),
    "motherwell,uk": (-3.991870, 55.789240),
    "guofu,china": (106.601390, 28.850000),
    "pullman,usa": (-117.179620, 46.731270),
    "west lawn,usa": (-87.722270, 41.772810),
    "mount lebanon,usa": (-80.049500, 40.355350),
    "alabaster,usa": (-86.816380, 33.244280),
    "jiulongshan,china": (108.250940, 31.194450),
    "farmers branch,usa": (-96.896120, 32.926510),
    "oildale,usa": (-119.019550, 35.419680),
    "la verne,usa": (-117.767840, 34.100840),
    "mason,usa": (-84.309940, 39.360060),
    "eastpointe,usa": (-82.955470, 42.468370),
    "bustleton,usa": (-75.031560, 40.082610),
    "gillette,usa": (-105.502220, 44.291090),
    "valparaiso,usa": (-87.061140, 41.473090),
    "midvale,usa": (-111.899940, 40.611060),
    "darwen,uk": (-2.464940, 53.698030),
    "zhoujia,china": (107.538480, 30.419080),
    "heba,china": (105.216250, 33.936240),
    "yongxing,china": (106.176120, 28.989680),
    "haojiaqiao,china": (106.283330, 38.016670),
    "wisbech,uk": (0.159380, 52.666220),
    "north ridgeville,usa": (-82.019030, 41.389490),
    "petersburg,usa": (-77.401930, 37.227930),
    "santa rosa beach,usa": (-86.228830, 30.396030),
    "shaodian,china": (118.433330, 34.133330),
    "ken caryl,usa": (-105.112210, 39.575820),
    "randallstown,usa": (-76.795250, 39.367330),
    "westlake,usa": (-81.917920, 41.455320),
    "mixia,china": (77.249180, 38.453960),
    "xiasi,china": (105.513260, 32.289980),
    "bangor,usa": (-68.772650, 44.798840),
    "clermont,usa": (-81.772850, 28.549440),
    "sun prairie,usa": (-89.213730, 43.183600),
    "mawu,china": (107.313370, 29.592500),
    "saybag,china": (79.658330, 37.149720),
    "greater grand crossing,usa": (-87.614850, 41.761130),
    "futian,china": (109.710680, 31.222010),
    "fairbanks,usa": (-147.716390, 64.837780),
    "dagze,china": (91.345310, 29.673290),
    "college park,usa": (-76.936920, 38.980670),
    "rongjiang,china": (101.250000, 26.550000),
    "kangkar,singapore": (103.901670, 1.376110),
    "aston,uk": (-1.883330, 52.500000),
    "springville,usa": (-111.610750, 40.165230),
    "natick,usa": (-71.349500, 42.283430),
    "massillon,usa": (-81.521510, 40.796720),
    "walla walla,usa": (-118.343020, 46.064580),
    "huzhai,china": (117.008330, 34.669440),
    "dajin,china": (108.445790, 31.509550),
    "andover,usa": (-93.291340, 45.233300),
    "hopkinsville,usa": (-87.491170, 36.865610),
    "overbrook,usa": (-75.243240, 39.989280),
    "borehamwood,uk": (-0.277620, 51.654680),
    "laramie,usa": (-105.591100, 41.311370),
    "west englewood,usa": (-87.666720, 41.778090),
    "rayleigh,uk": (0.604590, 51.585710),
    "prestwich,uk": (-2.283330, 53.533330),
    "bethel park,usa": (-80.039500, 40.327570),
    "cookeville,usa": (-85.501640, 36.162840),
    "randolph,usa": (-71.041160, 42.162600),
    "helena,usa": (-112.036110, 46.592710),
    "shunzhou,china": (100.554260, 26.621200),
    "fenhe,china": (109.522060, 31.137230),
    "montgomery village,usa": (-77.195260, 39.176770),
    "cleethorpes,uk": (-0.032250, 53.560470),
    "north olmsted,usa": (-81.923470, 41.415600),
    "lower earley,uk": (-0.919790, 51.427080),
    "shirley,uk": (-1.819520, 52.410740),
    "deeside,uk": (-3.038410, 53.200530),
    "land o' lakes,usa": (-82.457590, 28.218900),
    "falmouth,uk": (-5.071130, 50.154410),
    "longju,china": (108.635180, 30.610900),
    "guolemude,china": (94.824630, 36.429300),
    "hyde,uk": (-2.079430, 53.451310),
    "watertown,usa": (-71.182830, 42.370930),
    "glastonbury,usa": (-72.608150, 41.712320),
    "tanchang chengguanzhen,china": (104.394640, 34.044620),
    "fenggao,china": (105.675060, 29.426850),
    "baliwan,china": (105.370430, 34.847570),
    "westmont,usa": (-118.302300, 33.941400),
    "hyde park,usa": (-71.124500, 42.255650),
    "thamesmead,uk": (0.119820, 51.503720),
    "garfield,usa": (-74.113200, 40.881490),
    "dasheng,china": (118.855410, 36.320000),
    "taolin,china": (119.533950, 35.800060),
    "shek lei,china": (114.139820, 22.366130),
    "laguna hills,usa": (-117.712830, 33.612520),
    "west bend,usa": (-88.183430, 43.425280),
    "willingboro,usa": (-74.869050, 40.027890),
    "chichester,uk": (-0.780030, 50.836730),
    "barnstaple,uk": (-4.058080, 51.080220),
    "spalding,uk": (-0.151410, 52.787090),
    "mundelein,usa": (-88.003970, 42.263080),
    "centereach,usa": (-73.099550, 40.858430),
    "juneau,usa": (-134.419720, 58.301940),
    "dade,china": (108.340260, 31.212880),
    "anlan,china": (106.594170, 29.247220),
    "mount juliet,usa": (-86.518610, 36.200050),
    "naugatuck,usa": (-73.050660, 41.485930),
    "wudalike,china": (77.129730, 38.361800),
    "san luis,usa": (-114.782180, 32.487000),
    "jiuxian,china": (106.202880, 29.862030),
    "epsom,uk": (-0.270110, 51.330500),
    "brighton beach,usa": (-73.959580, 40.577880),
    "michigan city,usa": (-86.895030, 41.707540),
    "dania beach,usa": (-80.143930, 26.052310),
    "makiki / lower punchbowl / tantalus,usa": (-157.831220, 21.317560),
    "lewiston orchards,usa": (-116.975430, 46.380440),
    "chatham,usa": (-87.612550, 41.741150),
    "navarre,usa": (-86.863570, 30.401590),
    "holly springs,usa": (-78.833620, 35.651270),
    "wenxian chengguanzhen,china": (104.681390, 32.947120),
    "wenfeng,china": (109.234590, 31.404950),
    "brentwood estates,usa": (-86.779170, 36.025060),
    "galesburg,usa": (-90.371240, 40.947820),
    "songbai,china": (110.672520, 31.756850),
    "wheat ridge,usa": (-105.077210, 39.766100),
    "rutherglen,uk": (-4.213760, 55.828850),
    "zhakou,china": (109.475020, 21.706560),
    "thornton-cleveleys,uk": (-3.022440, 53.873890),
    "aberdare,uk": (-3.449180, 51.714380),
    "zhong'ao,china": (105.666450, 29.765000),
    "yengisar,china": (76.171390, 38.925830),
    "daocheng,china": (100.297400, 29.037900),
    "caerphilly,uk": (-3.218000, 51.574520),
    "gurnee,usa": (-87.902020, 42.370300),
    "myrtle beach,usa": (-78.886690, 33.689060),
    "ruislip,uk": (-0.423410, 51.573440),
    "parkersburg,usa": (-81.561510, 39.266740),
    "yushan,china": (108.425040, 29.532840),
    "miami lakes,usa": (-80.308660, 25.908710),
    "saratoga,usa": (-122.023010, 37.263830),
    "east lake,usa": (-82.694820, 28.110850),
    "pingkai,china": (108.995940, 28.425950),
    "shuangtang,china": (118.474720, 34.365290),
    "banning,usa": (-116.876410, 33.925570),
    "goleta,usa": (-119.827640, 34.435830),
    "wanghong,china": (106.225000, 38.212500),
    "lakeside,usa": (-81.768150, 30.129960),
    "long branch,usa": (-73.992360, 40.304280),
    "fair oaks,usa": (-121.272170, 38.644630),
    "lake stevens,usa": (-122.063740, 48.015100),
    "radnor,usa": (-75.359910, 40.046220),
    "ganning,china": (108.280500, 30.669110),
    "holladay,usa": (-111.824660, 40.668840),
    "herriman,usa": (-112.032990, 40.514110),
    "jinhu,taiwan": (118.421110, 24.439440),
    "south kingstown,usa": (-71.524940, 41.447180),
    "pingtan,china": (105.877820, 29.845940),
    "saint neots,uk": (-0.266670, 52.216670),
    "canning town,uk": (0.019480, 51.513630),
    "estero,usa": (-81.806750, 26.438140),
    "ithaca,usa": (-76.496610, 42.440630),
    "north tonawanda,usa": (-78.864200, 43.038670),
    "brooklyn center,usa": (-93.332730, 45.076080),
    "pikesville,usa": (-76.722470, 39.374270),
    "new iberia,usa": (-91.818730, 30.003540),
    "alamogordo,usa": (-105.960270, 32.899530),
    "parkville,usa": (-76.539690, 39.377330),
    "statesboro,usa": (-81.783170, 32.448790),
    "shagang,china": (109.033330, 21.666670),
    "morgantown,usa": (-79.955900, 39.629530),
    "xiagezhuang,china": (120.434720, 36.693060),
    "los gatos,usa": (-121.974680, 37.226610),
    "matthews,usa": (-80.723680, 35.116810),
    "tongjing,china": (106.844800, 29.856530),
    "los altos,usa": (-122.114130, 37.385220),
    "longsheng,china": (106.816390, 29.081390),
    "clearfield,usa": (-112.026050, 41.110780),
    "burgess hill,uk": (-0.132870, 50.958430),
    "owings mills,usa": (-76.780250, 39.419550),
    "hawai'i kai,usa": (-157.701750, 21.296370),
    "aiken,usa": (-81.719550, 33.560420),
    "beverley,uk": (-0.423320, 53.845870),
    "greenwich,uk": (-0.011760, 51.477850),
    "ballwin,usa": (-90.546230, 38.595050),
    "algonquin,usa": (-88.294250, 42.165580),
    "bel air north,usa": (-76.373090, 39.554290),
    "newington,usa": (-72.723710, 41.697880),
    "deal,uk": (1.402800, 51.223160),
    "anwen,china": (106.756510, 28.680010),
    "santa paula,usa": (-119.059270, 34.354170),
    "xingang,taiwan": (120.346030, 23.557360),
    "fallbrook,usa": (-117.251150, 33.376420),
    "eldersburg,usa": (-76.950260, 39.403710),
    "sherwood,usa": (-92.224320, 34.815090),
    "springfield gardens,usa": (-73.762210, 40.663120),
    "sandaoling lutiankuang wuqi nongchang,china": (92.882790, 43.014780),
    "wishaw,uk": (-3.916670, 55.766670),
    "lawrenceville,usa": (-83.987960, 33.956210),
    "kaysville,usa": (-111.938550, 41.035220),
    "granger,usa": (-86.110840, 41.753380),
    "burlingame,usa": (-122.366080, 37.584100),
    "yujia,china": (107.953770, 30.811500),
    "post falls,usa": (-116.951590, 47.717960),
    "liberty,usa": (-94.419120, 39.246110),
    "west roxbury,usa": (-71.149500, 42.279260),
    "honghu,china": (106.952040, 30.000430),
    "yanwo,china": (106.073570, 30.331780),
    "pontypridd,uk": (-3.342110, 51.602100),
    "san pablo,usa": (-122.345530, 37.962150),
    "savage,usa": (-93.336340, 44.779130),
    "poughkeepsie,usa": (-73.920970, 41.700370),
    "north royalton,usa": (-81.724570, 41.313660),
    "mengla,china": (101.563700, 21.462340),
    "chicago heights,usa": (-87.635600, 41.506150),
    "lebanon,usa": (-86.291100, 36.208110),
    "winsford,uk": (-2.523980, 53.191460),
    "hufeng,china": (106.110890, 29.715500),
    "harpenden,uk": (-0.357060, 51.816840),
    "walnut,usa": (-117.865340, 34.020290),
    "madison heights,usa": (-83.105200, 42.485870),
    "whitstable,uk": (1.025700, 51.360700),
    "deland,usa": (-81.303120, 29.028320),
    "cedar city,usa": (-113.061890, 37.677480),
    "mugala,china": (81.664250, 36.854500),
    "camberley,uk": (-0.742610, 51.337050),
    "west warwick,usa": (-71.521940, 41.696890),
    "shangpa,china": (98.951580, 26.919480),
    "chahe,china": (117.883330, 34.533330),
    "yebao,china": (105.646670, 34.937220),
    "jamestown,usa": (-79.235330, 42.097000),
    "new bern,usa": (-77.044110, 35.108490),
    "whampoa garden,china": (114.189360, 22.305340),
    "taiping,china": (97.852620, 24.661160),
    "cleburne,usa": (-97.386680, 32.347640),
    "nagqu,china": (92.057290, 31.476780),
    "fuyuan,china": (134.298430, 48.363460),
    "tianducheng,china": (120.242580, 30.388660),
    "barnet,uk": (-0.200000, 51.650000),
    "ashmont,usa": (-71.068940, 42.283430),
    "nyemo,china": (90.148490, 29.437360),
    "bedworth,uk": (-1.469090, 52.479100),
    "jelebu,singapore": (103.762860, 1.379530),
    "luoyu,china": (105.231170, 33.841030),
    "qarek,china": (76.990280, 38.372220),
    "winter park,usa": (-81.339240, 28.600000),
    "carney,usa": (-76.523580, 39.394270),
    "southlake,usa": (-97.134180, 32.941240),
    "san carlos,usa": (-122.260520, 37.507160),
    "yishikuli,china": (77.201450, 38.488890),
    "eunos,singapore": (103.898220, 1.322520),
    "anhua,china": (105.047820, 33.505280),
    "woodstock,usa": (-84.519380, 34.101490),
    "huyanghe,china": (84.833620, 44.698400),
    "east hill-meridian,usa": (-122.173690, 47.410520),
    "niles,usa": (-87.802840, 42.018920),
    "laplace,usa": (-90.481470, 30.066980),
    "westchester,usa": (-80.327270, 25.754820),
    "atascadero,usa": (-120.670730, 35.489420),
    "jingui,china": (106.416670, 38.500000),
    "heswall,uk": (-3.096480, 53.327330),
    "gloucester,usa": (-70.663130, 42.614050),
    "nicholasville,usa": (-84.573000, 37.880630),
    "highland park,usa": (-87.800340, 42.181690),
    "hucknall,uk": (-1.200000, 53.033330),
    "dachang shandao,china": (122.600000, 39.275560),
    "nuozhadu,china": (100.269250, 22.578170),
    "hengchun,taiwan": (120.743890, 22.004170),
    "tongxi,china": (106.130430, 30.000470),
    "elizabethtown,usa": (-85.859130, 37.693950),
    "austintown,usa": (-80.764520, 41.101720),
    "meijiang,china": (109.026850, 28.263560),
    "egham,uk": (-0.552390, 51.431580),
    "east palo alto,usa": (-122.141080, 37.468830),
    "caotang,china": (109.623970, 31.090230),
    "yau ma tei,china": (114.168570, 22.313800),
    "pueblo west,usa": (-104.722750, 38.350000),
    "port chester,usa": (-73.665680, 41.001760),
    "fort cavazos,usa": (-97.775610, 31.134890),
    "lagrange,usa": (-85.031330, 33.039290),
    "tuomuwusitang,china": (77.231510, 38.363090),
    "lower wong tai sin estate (i & ii),china": (114.194410, 22.339230),
    "opelika,usa": (-85.378280, 32.645410),
    "rahway,usa": (-74.277650, 40.608160),
    "sevenoaks,uk": (0.188830, 51.272660),
    "north chicago,usa": (-87.841180, 42.325580),
    "middle village,usa": (-73.881250, 40.716490),
    "kidsgrove,uk": (-2.237770, 53.086910),
    "morristown,usa": (-83.294890, 36.213980),
    "cheshire,usa": (-72.900660, 41.498990),
    "branford,usa": (-72.815100, 41.279540),
    "chaotian,china": (105.885010, 32.644620),
    "raytown,usa": (-94.463560, 39.008620),
    "xichuan,china": (106.063000, 35.030500),
    "south horizons,china": (114.148280, 22.243830),
    "thomson,singapore": (103.843610, 1.349170),
    "newtownards,uk": (-5.690920, 54.592360),
    "fruit cove,usa": (-81.641760, 30.111070),
    "didcot,uk": (-1.242140, 51.609280),
    "port huron,usa": (-82.424910, 42.970860),
    "tewksbury,usa": (-71.234220, 42.610650),
    "glenville,usa": (-74.052070, 42.929240),
    "franklin square,usa": (-73.675960, 40.707320),
    "nelson,uk": (-2.200000, 53.833330),
    "pitou,taiwan": (120.478580, 23.895000),
    "oak ridge,usa": (-84.269640, 36.010360),
    "longfellow community,usa": (-93.225570, 44.942560),
    "southgate,usa": (-83.193810, 42.213930),
    "qingxi,china": (107.457550, 29.797120),
    "east haven,usa": (-72.868430, 41.276210),
    "upper alton,usa": (-90.150660, 38.911440),
    "johnston,usa": (-71.506750, 41.821860),
    "burntwood,uk": (-1.927590, 52.680750),
    "atwater,usa": (-120.609080, 37.347720),
    "carrickfergus,uk": (-5.805800, 54.715800),
    "west falls church,usa": (-77.187870, 38.864840),
    "wutan,china": (106.062900, 29.256960),
    "williamsport,usa": (-77.001080, 41.241190),
    "fort bragg,usa": (-79.006030, 35.139000),
    "south horizons (estate),china": (114.146160, 22.244110),
    "felixstowe,uk": (1.351100, 51.963750),
    "russellville,usa": (-93.133790, 35.278420),
    "leighton hill,china": (114.183980, 22.276100),
    "kendal,uk": (-2.747570, 54.326810),
    "harker heights,usa": (-97.659740, 31.083510),
    "consett,uk": (-1.831600, 54.854040),
    "dongwenquan,china": (106.857760, 29.456090),
    "witney,uk": (-1.485400, 51.783600),
    "shizhi,china": (107.794260, 30.053040),
    "granite city,usa": (-90.148720, 38.701440),
    "milford mill,usa": (-76.769970, 39.347880),
    "ashton in makerfield,uk": (-2.650000, 53.483330),
    "layka,china": (79.731670, 37.076940),
    "kilburn,uk": (-0.191570, 51.552950),
    "lake in the hills,usa": (-88.330360, 42.181690),
    "evans,usa": (-82.130670, 33.533750),
    "fort hamilton,usa": (-74.033200, 40.618720),
    "cheadle hulme,uk": (-2.189700, 53.376100),
    "ballymena,uk": (-6.276280, 54.863570),
    "ferry pass,usa": (-87.212470, 30.510200),
    "kingman,usa": (-114.053010, 35.189440),
    "orcutt,usa": (-120.436000, 34.865260),
    "needham,usa": (-71.232830, 42.283430),
    "crown point,usa": (-87.365310, 41.416980),
    "wangu,china": (105.935510, 29.682420),
    "big spring,usa": (-101.478740, 32.250400),
    "dracut,usa": (-71.302010, 42.670370),
    "tiaoshi,china": (106.642500, 29.277220),
    "allston,usa": (-71.125890, 42.358430),
    "schererville,usa": (-87.454760, 41.478920),
    "burton,usa": (-83.616340, 42.999470),
    "ridgecrest,usa": (-117.670900, 35.622460),
    "windsor,usa": (-72.643700, 41.852600),
    "eagle pass,usa": (-100.499520, 28.709140),
    "agawam,usa": (-72.614810, 42.069540),
    "weatherford,usa": (-97.797250, 32.759300),
    "west elkridge,usa": (-76.726920, 39.207050),
    "stanford-le-hope,uk": (0.434220, 51.522740),
    "east chicago,usa": (-87.454760, 41.639200),
    "bideford,uk": (-4.208320, 51.016780),
    "rochester,uk": (0.505460, 51.387640),
    "chuk yuen,china": (114.193270, 22.345440),
    "socorro mission number 1 colonia,usa": (-106.290540, 31.636220),
    "ruidian,china": (98.408550, 25.531710),
    "norwood,usa": (-71.199500, 42.194540),
    "gangxia,china": (114.061360, 22.540330),
    "xizhou,taiwan": (120.689170, 24.276670),
    "sanqu,china": (105.621610, 29.641570),
    "qingshizui,china": (101.433330, 37.466670),
    "shipley,uk": (-1.766670, 53.833330),
    "northampton,usa": (-72.641200, 42.325090),
    "lake magdalene,usa": (-82.471760, 28.074180),
    "perry hall,usa": (-76.463570, 39.412610),
    "zhifeng,china": (105.784160, 29.654400),
    "maryville,usa": (-83.970460, 35.756470),
    "wood green,uk": (-0.116670, 51.600000),
    "hobart,usa": (-87.255040, 41.532260),
    "fresh meadows,usa": (-73.793470, 40.734820),
    "frankfort,usa": (-84.873280, 38.200910),
    "nanya,china": (108.086640, 31.084340),
    "mehlville,usa": (-90.322890, 38.508390),
    "greer,usa": (-82.227060, 34.938730),
    "macpherson,singapore": (103.884130, 1.327130),
    "yio chu kang,singapore": (103.851390, 1.391110),
    "harrison,usa": (-73.712630, 40.968990),
    "monterey,usa": (-121.894680, 36.600240),
    "west islip,usa": (-73.306230, 40.706210),
    "desert hot springs,usa": (-116.503530, 33.961730),
    "zheshan,china": (118.951350, 36.148770),
    "american fork,usa": (-111.795760, 40.376900),
    "central,usa": (-91.036770, 30.554350),
    "hadapu zhen,china": (104.223010, 34.231320),
    "newburgh,usa": (-74.010420, 41.503430),
    "mccully - moiliili,usa": (-157.831180, 21.294610),
    "chamblee,usa": (-84.298810, 33.892050),
    "millville,usa": (-75.039340, 39.402060),
    "north andover,usa": (-71.135060, 42.698700),
    "seatac,usa": (-122.292170, 47.448460),
    "elmira,usa": (-76.807730, 42.089800),
    "stockbridge,usa": (-84.233810, 33.544280),
    "glen ellyn,usa": (-88.067010, 41.877530),
    "monroeville,usa": (-79.788100, 40.421180),
    "benicia,usa": (-122.158580, 38.049370),
    "longsha,china": (108.237010, 30.639650),
    "fredericksburg,usa": (-77.460540, 38.303180),
    "suisun,usa": (-122.040240, 38.238250),
    "aberdeen,usa": (-98.486480, 45.464700),
    "cranberry township,usa": (-80.107140, 40.684960),
    "garfield heights,usa": (-81.605960, 41.417000),
    "south chicago,usa": (-87.554250, 41.739770),
    "cornelius,usa": (-80.860070, 35.486800),
    "oakdale,usa": (-92.964940, 44.963020),
    "oak forest,usa": (-87.743940, 41.602810),
    "chengjiang,china": (106.384670, 29.871940),
    "garner,usa": (-78.614170, 35.711260),
    "holmesburg,usa": (-75.027950, 40.041500),
    "drexel hill,usa": (-75.292130, 39.947060),
    "vestal,usa": (-76.053810, 42.085070),
    "north kingstown,usa": (-71.466170, 41.550100),
    "heywood,uk": (-2.219410, 53.592450),
    "leifeng,china": (112.846110, 28.200000),
    "yitang,china": (117.888890, 34.258330),
    "yinqiao zhen,china": (100.123460, 25.754290),
    "jinqiao,china": (121.593310, 31.270920),
    "brierley hill,uk": (-2.121390, 52.481730),
    "bella vista,usa": (-94.271340, 36.480700),
    "melrose,usa": (-71.066160, 42.458430),
    "muswell hill,uk": (-0.142120, 51.590540),
    "gramercy park,usa": (-73.986110, 40.737500),
    "wellesley,usa": (-71.292560, 42.296490),
    "winchester,usa": (-115.118890, 36.129970),
    "houqiao,china": (98.278020, 25.323560),
    "slidell,usa": (-89.781170, 30.275190),
    "university heights,usa": (-73.909300, 40.860100),
    "west springfield,usa": (-72.620370, 42.107040),
    "dodge city,usa": (-100.017080, 37.752800),
    "paragould,usa": (-90.497330, 36.058400),
    "maywood,usa": (-118.185350, 33.986680),
    "seguin,usa": (-97.964730, 29.568840),
    "shirley,usa": (-72.867600, 40.801490),
    "livingston,usa": (-74.314870, 40.795930),
    "round lake beach,usa": (-88.090080, 42.371690),
    "longhua,china": (106.207250, 29.210280),
    "kuangshi,china": (114.046110, 38.072500),
    "stratford-upon-avon,uk": (-1.707340, 52.191660),
    "sterling,usa": (-77.428600, 39.006220),
    "zhengxing,china": (106.129260, 29.457410),
    "guangcun,china": (109.354500, 19.641860),
    "sunbury-on-thames,uk": (-0.418170, 51.404240),
    "fountain,usa": (-104.700810, 38.682220),
    "saratoga springs,usa": (-73.784570, 43.083130),
    "newry,uk": (-6.337390, 54.178410),
    "kirkwood,usa": (-90.406780, 38.583390),
    "drexel heights,usa": (-111.028430, 32.141190),
    "chongkan,china": (105.612220, 30.155590),
    "xinsheng,china": (107.724130, 30.843670),
    "lijun,china": (106.120000, 38.185830),
    "bow,uk": (-0.016650, 51.526090),
    "fridley,usa": (-93.263280, 45.086080),
    "west scarborough,usa": (-70.387830, 43.570360),
    "queensbury,usa": (-73.613170, 43.377290),
    "roslindale,usa": (-71.124500, 42.291210),
    "ashington,uk": (-1.564120, 55.177190),
    "luotian,china": (108.559480, 30.515600),
    "rexburg,usa": (-111.789690, 43.826020),
    "shaker heights,usa": (-81.537070, 41.473940),
    "mililani town,usa": (-158.015030, 21.450400),
    "bergenfield,usa": (-73.997360, 40.927600),
    "marshalltown,usa": (-92.907980, 42.049430),
    "cambuslang,uk": (-4.160960, 55.809660),
    "hebao,china": (105.543380, 29.566170),
    "tucker,usa": (-84.217140, 33.854550),
    "nutley,usa": (-74.159870, 40.822320),
    "yunji,china": (107.340410, 29.919430),
    "port richmond,usa": (-75.100170, 39.993450),
    "kirkby in ashfield,uk": (-1.243790, 53.099820),
    "lake jackson,usa": (-95.434390, 29.033860),
    "plum,usa": (-79.749490, 40.500350),
    "willenhall,uk": (-2.059340, 52.585140),
    "burngreave,uk": (-1.457890, 53.393020),
    "xiaodu,china": (105.886780, 29.962070),
    "denton,uk": (-2.118220, 53.456780),
    "west chicago,usa": (-88.203960, 41.884750),
    "kuanchuan,china": (105.541110, 34.166390),
    "allen park,usa": (-83.211040, 42.257540),
    "wilmette,usa": (-87.722840, 42.072250),
    "imperial beach,usa": (-117.113080, 32.583940),
    "glen cove,usa": (-73.633740, 40.862320),
    "cleckheaton,uk": (-1.712940, 53.724050),
    "maryland heights,usa": (-90.429840, 38.713110),
    "mazhan,china": (98.484030, 25.211370),
    "mason city,usa": (-93.201040, 43.153570),
    "akesalayi,china": (79.689840, 37.169200),
    "crofton,usa": (-76.687470, 39.001780),
    "bearsden,uk": (-4.332790, 55.915360),
    "eagle mountain,usa": (-112.006880, 40.314120),
    "jiasi,china": (106.446910, 29.115690),
    "college point,usa": (-73.845970, 40.787600),
    "liangshui,china": (104.809090, 33.431770),
    "lindenhurst,usa": (-73.373450, 40.686770),
    "jarrow,uk": (-1.484230, 54.980360),
    "spanaway,usa": (-122.434570, 47.103990),
    "belmont,usa": (-122.275800, 37.520210),
    "hunts point,usa": (-73.884020, 40.812600),
    "holbrook,usa": (-73.078440, 40.812320),
    "new london,usa": (-72.099520, 41.355650),
    "simen,china": (105.012780, 34.622220),
    "melton mowbray,uk": (-0.886930, 52.765880),
    "paso robles,usa": (-120.691000, 35.626640),
    "xiaomian,china": (106.534350, 30.122680),
    "tualatin,usa": (-122.763990, 45.384010),
    "buzhake,china": (79.799970, 37.065680),
    "fleming island,usa": (-81.718980, 30.093300),
    "workington,uk": (-3.544130, 54.642500),
    "jiangxi,china": (105.199940, 33.999340),
    "winona,usa": (-91.639320, 44.049960),
    "agua caliente,usa": (-122.488040, 38.324080),
    "thomasville,usa": (-80.081990, 35.882640),
    "casselberry,usa": (-81.327850, 28.677780),
    "puchuan,china": (98.570070, 24.703100),
    "haverhill,uk": (0.438910, 52.082260),
    "yigai'erqi,china": (77.469150, 38.340750),
    "zuitai,china": (105.604670, 33.330830),
    "eureka,usa": (-124.163670, 40.802070),
    "east saint louis,usa": (-90.150940, 38.624500),
    "garden city,usa": (-100.872660, 37.971690),
    "alton,usa": (-90.184280, 38.890600),
    "huatugou,china": (90.867920, 38.255440),
    "maghull,uk": (-2.941170, 53.516190),
    "university park,usa": (-80.367550, 25.746490),
    "tawakule,china": (80.216540, 37.758840),
    "williston,usa": (-103.617970, 48.146970),
    "paramus,usa": (-74.075420, 40.944540),
    "back mountain,usa": (-75.996310, 41.335910),
    "qinglian,china": (109.236860, 31.190610),
    "west milford,usa": (-74.367370, 41.131210),
    "jeffersontown,usa": (-85.564400, 38.194240),
    "horn lake,usa": (-90.034810, 34.955370),
    "stoughton,usa": (-71.102270, 42.125100),
    "easton,usa": (-75.220730, 40.688430),
    "weidian,china": (105.565600, 35.102430),
    "prairieville,usa": (-90.972050, 30.302970),
    "dix hills,usa": (-73.336230, 40.804820),
    "dushi,china": (106.532830, 29.150020),
    "gladstone,usa": (-94.554680, 39.203890),
    "cutler ridge,usa": (-80.346720, 25.580660),
    "wooster,usa": (-81.936460, 40.805170),
    "bessemer,usa": (-86.954440, 33.401780),
    "merrimack,usa": (-71.493400, 42.865090),
    "lemon grove,usa": (-117.031420, 32.742550),
    "kankakee,usa": (-87.861150, 41.120030),
    "wethersfield,usa": (-72.652590, 41.714270),
    "highbury,uk": (-0.100000, 51.550000),
    "mchenry,usa": (-88.266750, 42.333350),
    "clydebank,uk": (-4.405700, 55.901370),
    "acocks green,uk": (-1.816670, 52.450000),
    "saugus,usa": (-71.010050, 42.464820),
    "stevens point,usa": (-89.574560, 44.523580),
    "west linn,usa": (-122.612310, 45.365680),
    "shuanglu,china": (105.762900, 29.485430),
    "superior,usa": (-92.104080, 46.720770),
    "tujunga,usa": (-118.288410, 34.252230),
    "east grinstead,uk": (-0.006100, 51.123820),
    "magna,usa": (-112.101610, 40.709110),
    "batavia,usa": (-88.312570, 41.850030),
    "cantonment,usa": (-87.339980, 30.608530),
    "danvers,usa": (-70.930050, 42.575090),
    "shoreview,usa": (-93.147170, 45.079130),
    "smithtown,usa": (-73.200670, 40.855930),
    "pearl,usa": (-90.132030, 32.274590),
    "dafengdong,china": (107.811390, 26.711940),
    "nantuo,china": (107.527900, 29.855380),
    "flint,uk": (-3.132310, 53.244880),
    "mansfield city,usa": (-72.233690, 41.765930),
    "fajar,singapore": (103.770590, 1.384360),
    "mercerville-hamilton square,usa": (-74.672230, 40.231260),
    "north creek,usa": (-122.176240, 47.819540),
    "carbondale,usa": (-89.216750, 37.727270),
    "westport,usa": (-73.357900, 41.141490),
    "lei tung,china": (114.157570, 22.240520),
    "kuoyiqi,china": (79.721010, 37.354530),
    "baigong jiedao,china": (108.033720, 30.294930),
    "medina,usa": (-81.863750, 41.138390),
    "bay shore,usa": (-73.245390, 40.725100),
    "kahului,usa": (-156.472930, 20.889330),
    "zhuyang,china": (105.944870, 29.064230),
    "leisure city,usa": (-80.429220, 25.495390),
    "onyar,china": (81.783080, 43.850370),
    "vernon hills,usa": (-87.979520, 42.219470),
    "xialu,china": (108.084420, 29.941670),
    "zionsville,usa": (-86.261940, 39.950870),
    "norco,usa": (-117.548660, 33.931130),
    "wasco,usa": (-119.340950, 35.594120),
    "wah fu,china": (114.136220, 22.254740),
    "fortuna foothills,usa": (-114.411890, 32.657830),
    "westhoughton,uk": (-2.524640, 53.548990),
    "barberton,usa": (-81.605120, 41.012830),
    "kingsville,usa": (-97.856110, 27.515870),
    "sangzhe,china": (108.398220, 29.278370),
    "statesville,usa": (-80.887300, 35.782640),
    "plainview,usa": (-73.467350, 40.776490),
    "laurel,usa": (-76.848310, 39.099280),
    "frome,uk": (-2.322110, 51.228340),
    "congleton,uk": (-2.212530, 53.163140),
    "south pasadena,usa": (-118.150350, 34.116120),
    "hong kah,singapore": (103.722780, 1.359440),
    "howard beach,usa": (-73.836250, 40.657880),
    "shituo,china": (107.135640, 29.716130),
    "camden town,uk": (-0.143340, 51.540570),
    "four corners,usa": (-81.647380, 28.332870),
    "south laurel,usa": (-76.850250, 39.069830),
    "asheboro,usa": (-79.813640, 35.707910),
    "ryde,uk": (-1.162100, 50.729990),
    "buenaventura lakes,usa": (-81.353130, 28.335840),
    "tianwei,taiwan": (120.524000, 23.892700),
    "bishop auckland,uk": (-1.677060, 54.655540),
    "twentynine palms,usa": (-116.054170, 34.135560),
    "zouma,china": (108.437520, 30.569600),
    "huntley,usa": (-88.428140, 42.168080),
    "northolt,uk": (-0.367780, 51.548550),
    "pennsport,usa": (-75.150450, 39.927610),
    "xenia,usa": (-83.929650, 39.684780),
    "reisterstown,usa": (-76.831900, 39.469760),
    "newton aycliffe,uk": (-1.571900, 54.618420),
    "longchi,china": (119.325320, 36.945290),
    "wuma,china": (109.376450, 30.854050),
    "central 14th street / spring road,usa": (-77.032650, 38.937070),
    "green,usa": (-81.483170, 40.945890),
    "brawley,usa": (-115.530270, 32.978660),
    "sham tseng,china": (114.050000, 22.366670),
    "yukon,usa": (-97.762540, 35.506720),
    "ellendale,usa": (-89.825920, 35.230640),
    "opportunity,usa": (-117.239910, 47.649950),
    "rhyl,uk": (-3.492280, 53.319290),
    "luotang,china": (105.264850, 33.067750),
    "hertford,uk": (-0.078540, 51.795880),
    "ramsey,usa": (-93.450000, 45.261100),
    "suitland,usa": (-76.923860, 38.848720),
    "huolu,china": (107.872540, 29.394220),
    "pleasure ridge park,usa": (-85.858300, 38.145350),
    "rosedale,usa": (-73.735410, 40.662050),
    "new lenox,usa": (-87.965610, 41.511980),
    "neenah,usa": (-88.462610, 44.185820),
    "alvin,usa": (-95.244100, 29.423850),
    "key west,usa": (-81.781630, 24.555240),
    "temple terrace,usa": (-82.389260, 28.035300),
    "owatonna,usa": (-93.226040, 44.083850),
    "staveley,uk": (-1.350000, 53.266670),
    "yanzibu,china": (117.702220, 34.505610),
    "homewood,usa": (-86.800820, 33.471770),
    "sahuarita,usa": (-110.955650, 31.957580),
    "maple valley,usa": (-122.046410, 47.392720),
    "coleraine,uk": (-6.666670, 55.133330),
    "farnworth,uk": (-2.400000, 53.550000),
    "hazelwood,usa": (-90.370950, 38.771440),
    "shanghuang,china": (109.484160, 31.320470),
    "lemoore,usa": (-119.782910, 36.300780),
    "baima,china": (107.539390, 29.395530),
    "mint hill,usa": (-80.647290, 35.179590),
    "qilian,china": (100.240280, 38.180560),
    "long island city,usa": (-73.948750, 40.744820),
    "cabot,usa": (-92.016530, 34.974530),
    "xituo,china": (108.217320, 30.407930),
    "rhawnhurst,usa": (-75.055730, 40.061780),
    "reedley,usa": (-119.450400, 36.596340),
    "edgewood,usa": (-76.294400, 39.418720),
    "shek kip mei estate,china": (114.165310, 22.334120),
    "meadow woods,usa": (-81.366460, 28.385560),
    "south portland,usa": (-70.240880, 43.641470),
    "zhongxing new village,taiwan": (120.685160, 23.959080),
    "west whittier-los nietos,usa": (-118.069090, 33.976000),
    "crowthorne,uk": (-0.792190, 51.370270),
    "hawarden,uk": (-3.025780, 53.184780),
    "bramhall,uk": (-2.165390, 53.358010),
    "coulsdon,uk": (-0.140880, 51.320020),
    "zanesville,usa": (-82.013190, 39.940350),
    "colleyville,usa": (-97.155010, 32.880960),
    "bartley green,uk": (-1.997070, 52.435320),
    "hornchurch,uk": (0.216640, 51.556850),
    "st austell,uk": (-4.774420, 50.342500),
    "saddleworth,uk": (-2.004550, 53.548460),
    "ossining,usa": (-73.861520, 41.162870),
    "melrose park,usa": (-87.856730, 41.900590),
    "starkville,usa": (-88.819610, 33.450490),
    "rhosllannerchrugog,uk": (-3.058140, 53.009740),
    "fleetwood,uk": (-3.010850, 53.925270),
    "witham,uk": (0.640380, 51.800070),
    "lochearn,usa": (-76.722190, 39.340660),
    "chanhassen,usa": (-93.530790, 44.862190),
    "hercules,usa": (-122.288580, 38.017140),
    "panjim,china": (81.424700, 44.007540),
    "galt,usa": (-121.299950, 38.254640),
    "prior lake,usa": (-93.422730, 44.713300),
    "castlewood,usa": (-104.901090, 39.584710),
    "grandview,usa": (-94.533010, 38.885840),
    "yarmouth,usa": (-70.228630, 41.705670),
    "choi wan estate (i & ii),china": (114.213310, 22.333370),
    "sandusky,usa": (-82.707960, 41.448940),
    "balch springs,usa": (-96.622770, 32.728740),
    "white bear lake,usa": (-93.009940, 45.084690),
    "chaska,usa": (-93.602180, 44.789410),
    "harvey,usa": (-87.646710, 41.610030),
    "middle river,usa": (-76.439410, 39.334270),
    "ardmore,usa": (-97.143630, 34.174260),
    "lockport,usa": (-88.057840, 41.589480),
    "woodburn,usa": (-122.855370, 45.143730),
    "fuhuan,china": (106.755350, 28.833790),
    "wyandotte,usa": (-83.149920, 42.214210),
    "zhoubai,china": (108.822670, 29.529490),
    "mauldin,usa": (-82.310120, 34.778730),
    "belvidere,usa": (-88.844270, 42.263910),
    "awati,china": (77.396400, 38.608380),
    "blackheath,uk": (0.007900, 51.464700),
    "changxin,china": (106.329720, 38.674720),
    "lushan,china": (107.783330, 26.650000),
    "moscow,usa": (-117.000170, 46.732390),
    "longcheng,china": (105.973390, 35.000960),
    "west memphis,usa": (-90.184540, 35.146480),
    "mercer island,usa": (-122.222070, 47.570650),
    "elgin,uk": (-3.318430, 57.649470),
    "bridgeton,usa": (-75.234080, 39.427340),
    "xianglong,china": (106.575880, 30.261250),
    "soledad,usa": (-121.326320, 36.424690),
    "bojia,china": (111.968060, 26.467220),
    "pitsea,uk": (0.508590, 51.563870),
    "saujana,singapore": (103.767900, 1.382540),
    "citong,taiwan": (120.499650, 23.757510),
    "brownsburg,usa": (-86.397770, 39.843380),
    "saginaw township north,usa": (-84.006740, 43.460040),
    "edwardsville,usa": (-89.953160, 38.811440),
    "chalk farm,uk": (-0.149870, 51.543130),
    "woodbridge,usa": (-117.794420, 33.677240),
    "liliha - kapalama,usa": (-157.854180, 21.337350),
    "sanger,usa": (-119.555970, 36.708010),
    "san fernando,usa": (-118.438970, 34.281950),
    "rockledge,usa": (-80.725330, 28.350840),
    "hastings,usa": (-98.388390, 40.586120),
    "cave spring,usa": (-80.012820, 37.227640),
    "north tustin,usa": (-117.793940, 33.764460),
    "east amherst,usa": (-78.696700, 43.018390),
    "gar,china": (80.097580, 32.501240),
    "renhe,china": (101.016670, 26.416670),
    "whitehaven,uk": (-3.584120, 54.548970),
    "daphne,usa": (-87.903600, 30.603530),
    "whitehall township,usa": (-75.499910, 40.666760),
    "skegness,uk": (0.336300, 53.143620),
    "paducah,usa": (-88.600050, 37.083390),
    "luoping,china": (110.086790, 31.206590),
    "selby,uk": (-1.066670, 53.783330),
    "cliffside park,usa": (-73.987640, 40.821490),
    "elmwood park,usa": (-87.809230, 41.921140),
    "vineyard,usa": (-121.346920, 38.464490),
    "thetford,uk": (0.750000, 52.416670),
    "hazleton,usa": (-75.974650, 40.958420),
    "hehua,china": (98.393680, 24.970240),
    "coronado,usa": (-117.183090, 32.685890),
    "hillside,usa": (-73.786800, 40.707880),
    "eagle river,usa": (-149.567780, 61.321390),
    "south salt lake,usa": (-111.888270, 40.718840),
    "paris,usa": (-95.555510, 33.660940),
    "mo'ili'ili,usa": (-157.830020, 21.294670),
    "northport,usa": (-87.577230, 33.229010),
    "anping,china": (109.345040, 30.963840),
    "yengitam,china": (81.656940, 43.745830),
    "uniondale,usa": (-73.592910, 40.700380),
    "ponca city,usa": (-97.085590, 36.706980),
    "muskego,usa": (-88.138980, 42.905850),
    "collinsville,usa": (-89.984550, 38.670330),
    "chenjiaba,china": (108.408460, 30.807670),
    "short pump,usa": (-77.612490, 37.650420),
    "dedham,usa": (-71.166160, 42.241770),
    "de pere,usa": (-88.060380, 44.448880),
    "chentuan,china": (119.266940, 35.504720),
    "minning,china": (105.970680, 38.248700),
    "tuwaite,china": (79.768100, 37.344880),
    "caledonia,usa": (-87.924250, 42.807800),
    "yanjing,china": (106.350250, 29.944940),
    "inkster,usa": (-83.309930, 42.294200),
    "vincentown,usa": (-74.748490, 39.934000),
    "bixby,usa": (-95.883320, 35.942040),
    "newton mearns,uk": (-4.333390, 55.773340),
    "emporia,usa": (-96.181660, 38.403900),
    "fort dodge,usa": (-94.168020, 42.497470),
    "walker,usa": (-85.768090, 43.001410),
    "vale of leven,uk": (-4.579280, 55.971320),
    "wuling,china": (108.258840, 30.505950),
    "ottumwa,usa": (-92.411300, 41.020010),
    "junction city,usa": (-96.831400, 39.028610),
    "seal beach,usa": (-118.104790, 33.741410),
    "tarpon springs,usa": (-82.756770, 28.146120),
    "pianjiao,china": (100.583330, 26.016670),
    "herndon,usa": (-77.386100, 38.969550),
    "teck whye,singapore": (103.751970, 1.380300),
    "tsim sha tsui,china": (114.166670, 22.300000),
    "sachse,usa": (-96.595270, 32.976230),
    "sun city west,usa": (-112.341270, 33.661980),
    "watauga,usa": (-97.254740, 32.857910),
    "jiahanbage,china": (79.705720, 37.196520),
    "san benito,usa": (-97.631100, 26.132580),
    "forest grove,usa": (-123.110660, 45.519840),
    "hucheng,china": (107.541800, 30.814790),
    "xiyu,china": (105.303600, 34.051630),
    "palmetto bay,usa": (-80.324770, 25.621770),
    "laitan,china": (106.486240, 30.175820),
    "lixi,china": (108.611000, 28.531260),
    "staunton,usa": (-79.073200, 38.149910),
    "selma,usa": (-119.612080, 36.570780),
    "south windsor,usa": (-72.621200, 41.823710),
    "north potomac,usa": (-77.264980, 39.082890),
    "jiagao,china": (109.175960, 30.889220),
    "homer glen,usa": (-87.938110, 41.600030),
    "coral terrace,usa": (-80.304500, 25.745930),
    "ridgeland,usa": (-90.132310, 32.428480),
    "wednesbury,uk": (-2.023550, 52.551400),
    "scaggsville,usa": (-76.900250, 39.145110),
    "feltham,uk": (-0.413880, 51.446200),
    "shuangshi,china": (105.837810, 29.400310),
    "cudahy,usa": (-118.185350, 33.960570),
    "new smyrna beach,usa": (-80.927000, 29.025820),
    "south plainfield,usa": (-74.411540, 40.579270),
    "columbine,usa": (-105.069430, 39.587770),
    "wangwu,china": (109.290710, 19.656230),
    "thatcham,uk": (-1.260490, 51.403660),
    "greenbelt,usa": (-76.875530, 39.004550),
    "south riding,usa": (-77.503880, 38.920940),
    "haitang,china": (107.229910, 30.171730),
    "citrus park,usa": (-82.569820, 28.078350),
    "boca del mar,usa": (-80.146710, 26.345080),
    "shandan,china": (104.831340, 34.751060),
    "newport,usa": (-71.312830, 41.490100),
    "wofo,china": (105.787060, 29.908250),
    "norton shores,usa": (-86.263950, 43.168900),
    "barstow heights,usa": (-117.056150, 34.869710),
    "songgang,china": (113.845400, 22.778660),
    "rockville centre,usa": (-73.641240, 40.658710),
    "searcy,usa": (-91.736250, 35.250640),
    "north platte,usa": (-100.765420, 41.123890),
    "rolling meadows,usa": (-88.013130, 42.084190),
    "carteret,usa": (-74.228200, 40.577330),
    "hindley,uk": (-2.583330, 53.533330),
    "ligang,china": (106.430430, 38.646430),
    "margaret drive,singapore": (103.808390, 1.296820),
    "immokalee,usa": (-81.417300, 26.418690),
    "riverbank,usa": (-120.935490, 37.736040),
    "zion,usa": (-87.832850, 42.446130),
    "plymstock,uk": (-4.090490, 50.359990),
    "trotwood,usa": (-84.311330, 39.797280),
    "north haven,usa": (-72.859540, 41.390930),
    "summerlin south,usa": (-115.330010, 36.117080),
    "ormskirk,uk": (-2.881780, 53.566850),
    "mahwah,usa": (-74.143760, 41.088710),
    "nanling,china": (99.995630, 22.711210),
    "xingdaohu,china": (109.132070, 21.714790),
    "loma linda,usa": (-117.261150, 34.048350),
    "peekskill,usa": (-73.920420, 41.290090),
    "keystone,usa": (-82.621210, 28.155850),
    "rugeley,uk": (-1.936940, 52.759300),
    "baldwin,usa": (-73.609300, 40.656490),
    "golborne,uk": (-2.596510, 53.476930),
    "fairfax,usa": (-77.306370, 38.846220),
    "sebastian,usa": (-80.470610, 27.816410),
    "zhuojiacun,china": (113.556390, 22.161390),
    "gosforth,uk": (-1.616670, 55.000000),
    "holt,usa": (-84.515250, 42.640590),
    "muscatine,usa": (-91.043210, 41.424470),
    "elk river,usa": (-93.567180, 45.303850),
    "rock springs,usa": (-109.202900, 41.587460),
    "golden gate,usa": (-81.695090, 26.187870),
    "corsicana,usa": (-96.468870, 32.095430),
    "changdao,china": (105.336510, 34.204880),
    "huntingdon,uk": (-0.186510, 52.330490),
    "hialeah gardens,usa": (-80.324500, 25.865100),
    "waverly,usa": (-84.620810, 42.739200),
    "xingfeng,china": (105.837500, 34.861110),
    "yufengshan,china": (106.723420, 29.719750),
    "hunt valley,usa": (-76.641080, 39.499830),
    "fuquay-varina,usa": (-78.800010, 35.584320),
    "fountain hills,usa": (-111.717360, 33.611710),
    "guanba,china": (106.805890, 28.801940),
    "unionport,usa": (-73.850130, 40.827320),
    "champlin,usa": (-93.397450, 45.188850),
    "south portland gardens,usa": (-70.315330, 43.638970),
    "centerville,usa": (-84.159380, 39.628390),
    "daventry,uk": (-1.160660, 52.256880),
    "linfeng,china": (107.219710, 29.891000),
    "zhanhe,china": (100.914000, 26.858900),
    "luhe,china": (105.340210, 34.009180),
    "batang,china": (106.292710, 29.835370),
    "bainbridge island,usa": (-122.521240, 47.626210),
    "droitwich,uk": (-2.150000, 52.266670),
    "senja,singapore": (103.760730, 1.385160),
    "morrisville,usa": (-78.825560, 35.823480),
    "marshall,usa": (-94.367420, 32.544870),
    "new malden,uk": (-0.261700, 51.400650),
    "kernersville,usa": (-80.073650, 36.119860),
    "dickinson,usa": (-102.789620, 46.879180),
    "new milton,uk": (-1.665800, 50.756010),
    "old bridge,usa": (-74.365430, 40.414830),
    "fort washington,usa": (-77.023030, 38.707340),
    "lanyang,china": (109.660400, 19.461410),
    "ammanford,uk": (-3.988330, 51.792790),
    "dinuba,usa": (-119.387070, 36.543280),
    "van nest,usa": (-73.863750, 40.848430),
    "portishead,uk": (-2.769730, 51.481990),
    "barstow,usa": (-117.022820, 34.898590),
    "droylsden,uk": (-2.145430, 53.480050),
    "fairland,usa": (-76.957750, 39.076220),
    "jiuhe,china": (99.991850, 26.762690),
    "fujia,china": (105.953610, 33.818890),
    "brookings,usa": (-96.798390, 44.311360),
    "blue island,usa": (-87.680050, 41.657260),
    "faribault,usa": (-93.268830, 44.294960),
    "chestnut hill,usa": (-71.166160, 42.330650),
    "baileys crossroads,usa": (-77.129700, 38.850390),
    "arbroath,uk": (-2.587360, 56.563170),
    "ying'awati,china": (79.830310, 37.298750),
    "musselburgh,uk": (-3.049910, 55.941700),
    "eagle,usa": (-116.354010, 43.695440),
    "gaoqiao,china": (108.242150, 31.368760),
    "norland,usa": (-80.212270, 25.948980),
    "scotch plains,usa": (-74.389870, 40.655380),
    "alamaiti,china": (77.476220, 38.582030),
    "evesham,uk": (-1.948870, 52.092370),
    "hanworth,uk": (-0.383330, 51.433330),
    "el cerrito,usa": (-122.311640, 37.915760),
    "whitefield,uk": (-2.300000, 53.550000),
    "kax,china": (81.870000, 43.641110),
    "xinlin,china": (124.400000, 51.666670),
    "wu kai sha,china": (114.242120, 22.430160),
    "derby,usa": (-97.268930, 37.545570),
    "frankford,usa": (-75.078590, 40.013840),
    "graham,usa": (-122.294280, 47.052880),
    "ilchester,usa": (-76.764690, 39.250940),
    "bayonet point,usa": (-82.683430, 28.326670),
    "lofthouse,uk": (-1.496970, 53.729470),
    "loves park,usa": (-89.058160, 42.320020),
    "jiaoshi,china": (107.597600, 29.716070),
    "avon lake,usa": (-82.028200, 41.505320),
    "sanzhi,taiwan": (121.501820, 25.257820),
    "san lorenzo,usa": (-122.124410, 37.681040),
    "baishi zhen,china": (107.882470, 30.316660),
    "morton grove,usa": (-87.782560, 42.040590),
    "penarth,uk": (-3.173420, 51.438600),
    "kingston,usa": (-73.997360, 41.927040),
    "bishopbriggs,uk": (-4.218690, 55.906690),
    "belper,uk": (-1.481190, 53.023300),
    "mcdonough,usa": (-84.146860, 33.447340),
    "romulus,usa": (-83.396600, 42.222260),
    "wangpu,china": (105.435850, 35.057120),
    "rosemount,usa": (-93.125770, 44.739410),
    "manglai,china": (79.678070, 37.275160),
    "xiaying,china": (119.476540, 37.042480),
    "northwest one,usa": (-77.011960, 38.904280),
    "eloise,usa": (-81.738130, 27.994740),
    "laguna beach,usa": (-117.783110, 33.542250),
    "bellview,usa": (-87.314970, 30.461590),
    "manoa,usa": (-157.804230, 21.316080),
    "formby,uk": (-3.069990, 53.558380),
    "burnham-on-sea,uk": (-2.997800, 51.238620),
    "terrytown,usa": (-90.032570, 29.910210),
    "broadstairs,uk": (1.441850, 51.358450),
    "crestview,usa": (-86.570510, 30.762130),
    "keene,usa": (-72.278140, 42.933690),
    "lihe,china": (108.262160, 30.816090),
    "gallup,usa": (-108.742580, 35.528080),
    "south old bridge,usa": (-74.354320, 40.408160),
    "duncan,usa": (-97.957810, 34.502300),
    "dupont circle,usa": (-77.044140, 38.908440),
    "griffin,usa": (-84.264090, 33.246780),
    "dolton,usa": (-87.607270, 41.638920),
    "oadby,uk": (-1.083540, 52.606210),
    "webster groves,usa": (-90.357340, 38.592550),
    "belton,usa": (-94.531900, 38.811950),
    "mu'er,china": (106.644390, 29.806010),
    "denison,usa": (-96.536660, 33.755660),
    "east elmhurst,usa": (-73.865140, 40.761210),
    "kerrville,usa": (-99.140320, 30.047430),
    "pooler,usa": (-81.247060, 32.115480),
    "mequon,usa": (-88.030010, 43.215550),
    "vicksburg,usa": (-90.877880, 32.352650),
    "wright,usa": (-86.638290, 30.455750),
    "morrisania,usa": (-73.906530, 40.829270),
    "heanor,uk": (-1.353830, 53.013720),
    "pacific palisades,usa": (-118.526470, 34.048060),
    "palm city,usa": (-80.266160, 27.167830),
    "middleborough,usa": (-70.911150, 41.893160),
    "arnold,usa": (-76.502740, 39.032060),
    "gongmen,china": (106.296390, 34.941390),
    "guanlong,china": (113.943980, 22.587770),
    "isla vista,usa": (-119.860970, 34.413330),
    "vero beach south,usa": (-80.413080, 27.616380),
    "van buren,usa": (-94.348270, 35.436760),
    "east peoria,usa": (-89.580100, 40.666150),
    "landover,usa": (-76.896640, 38.934000),
    "windham,usa": (-72.157020, 41.699820),
    "jacksonville beach,usa": (-81.393140, 30.294690),
    "calabasas,usa": (-118.638420, 34.157780),
    "chapeltown,uk": (-1.472170, 53.465060),
    "solon,usa": (-81.441230, 41.389780),
    "truro,uk": (-5.054360, 50.265260),
    "chantilly,usa": (-77.431100, 38.894280),
    "lintan chengguanzhen,china": (103.352420, 34.688850),
    "candler-mcafee,usa": (-84.272460, 33.726720),
    "huimin,china": (106.704720, 29.461940),
    "cizhu,china": (106.739820, 29.985400),
    "roselle,usa": (-88.079790, 41.984750),
    "copiague,usa": (-73.399840, 40.681490),
    "westpark,usa": (-117.813710, 33.685270),
    "munster,usa": (-87.512540, 41.564480),
    "ladera ranch,usa": (-117.635610, 33.570860),
    "litherland,uk": (-2.998090, 53.469930),
    "labuleng,china": (102.521170, 35.201250),
    "lisle,usa": (-88.074790, 41.801140),
    "anak bukit,singapore": (103.773010, 1.340670),
    "picnic point-north lynnwood,usa": (-122.294970, 47.862780),
    "east naples,usa": (-81.766480, 26.138420),
    "crystal,usa": (-93.360230, 45.032740),
    "cloverleaf,usa": (-95.171880, 29.778280),
    "dixiana,usa": (-86.649380, 33.740210),
    "machesney park,usa": (-89.039000, 42.347240),
    "morgan park,usa": (-87.666720, 41.690310),
    "market harborough,uk": (-0.920530, 52.477600),
    "noe valley,usa": (-122.433690, 37.750180),
    "east tremont,usa": (-73.890970, 40.845380),
    "pelham,usa": (-86.809990, 33.285670),
    "tremont,usa": (-73.905690, 40.849540),
    "lincolnia,usa": (-77.143310, 38.818450),
    "royton,uk": (-2.122670, 53.565070),
    "walton-on-thames,uk": (-0.413190, 51.386780),
    "valinda,usa": (-117.943670, 34.045290),
    "wellington,uk": (-2.516670, 52.700000),
    "haines city,usa": (-81.620090, 28.114500),
    "woodford green,uk": (0.023290, 51.609380),
    "millbrae,usa": (-122.387190, 37.598550),
    "newberg,usa": (-122.973160, 45.300120),
    "the crossings,usa": (-80.401170, 25.670660),
    "valley station,usa": (-85.870240, 38.111180),
    "lennox,usa": (-118.352580, 33.938070),
    "east lake-orient park,usa": (-82.378780, 27.982690),
    "stalybridge,uk": (-2.059080, 53.484140),
    "wilsonville,usa": (-122.773710, 45.299840),
    "banqiao,china": (105.953410, 29.513020),
    "hutto,usa": (-97.546670, 30.542700),
    "pulue,china": (106.159270, 29.817960),
    "laguna city,china": (114.228610, 22.305540),
    "bloomingdale,usa": (-82.240370, 27.893640),
    "west odessa,usa": (-102.498760, 31.842350),
    "inglewood-finn hill,usa": (-122.231670, 47.720490),
    "oak harbor,usa": (-122.643220, 48.293160),
    "'ewa gentry,usa": (-158.030390, 21.339990),
    "godalming,uk": (-0.614890, 51.185800),
    "mingda,china": (107.657260, 30.726300),
    "tongyangdao,china": (109.969870, 41.770310),
    "rosemont,usa": (-121.364670, 38.551850),
    "auburn hills,usa": (-83.234100, 42.687530),
    "pottstown,usa": (-75.649630, 40.245370),
    "potters bar,uk": (-0.178350, 51.693530),
    "west puente valley,usa": (-117.968400, 34.051680),
    "maple heights,usa": (-81.565960, 41.415330),
    "willoughby,usa": (-81.406500, 41.639770),
    "benbrook,usa": (-97.460580, 32.673190),
    "cranford,usa": (-74.299590, 40.658440),
    "shibao,china": (105.315850, 34.107860),
    "seaford,uk": (0.102680, 50.771410),
    "alfreton,uk": (-1.383760, 53.097660),
    "avon,usa": (-82.035420, 41.451710),
    "visitacion valley,usa": (-122.404330, 37.717150),
    "north augusta,usa": (-81.965120, 33.501800),
    "camborne,uk": (-5.297310, 50.213060),
    "guilford,usa": (-72.681760, 41.288990),
    "cottage lake,usa": (-122.077350, 47.744270),
    "dawan,china": (106.820230, 30.019630),
    "corcoran,usa": (-119.560400, 36.098010),
    "east patchogue,usa": (-72.996220, 40.767040),
    "shuen wan,china": (114.208120, 22.467670),
    "hudson,usa": (-81.440670, 41.240060),
    "yongle,china": (109.504790, 31.010480),
    "port hueneme,usa": (-119.195110, 34.147780),
    "kenilworth,uk": (-1.582760, 52.349580),
    "holiday,usa": (-82.739550, 28.187790),
    "near south side,usa": (-87.624770, 41.856700),
    "radcliff,usa": (-85.949130, 37.840350),
    "hopewell,usa": (-77.287200, 37.304320),
    "yongjia,china": (106.001340, 29.571900),
    "new castle,usa": (-80.347010, 41.003670),
    "seaham,uk": (-1.345750, 54.839030),
    "grand boulevard,usa": (-87.617270, 41.813920),
    "south elgin,usa": (-88.292300, 41.994190),
    "thornaby-on-tees,uk": (-1.300000, 54.533330),
    "prichard,usa": (-88.078890, 30.738800),
    "new brighton,usa": (-93.201890, 45.065520),
    "anniston,usa": (-85.831630, 33.659830),
    "ruston,usa": (-92.637930, 32.523210),
    "gulu,china": (109.439910, 31.330100),
    "midlothian,usa": (-96.994450, 32.482360),
    "oxford,usa": (-89.519250, 34.366500),
    "panghai,china": (108.063610, 26.726940),
    "wanshun,china": (106.971590, 30.040060),
    "darien,usa": (-87.973950, 41.751980),
    "gulebage,china": (77.230280, 38.412690),
    "northwood,usa": (-117.760910, 33.713720),
    "sudbury,uk": (0.731170, 52.038900),
    "ludlow,usa": (-72.475920, 42.160090),
    "south bradenton,usa": (-82.581760, 27.463100),
    "foggy bottom,usa": (-77.062200, 38.901500),
    "north plainfield,usa": (-74.427370, 40.630100),
    "wangyin,china": (105.761670, 34.833890),
    "acworth,usa": (-84.678370, 34.066350),
    "zhongchao,china": (109.220000, 26.137500),
    "fo tan,china": (114.192930, 22.398460),
    "shigang,china": (109.364320, 31.136110),
    "pascagoula,usa": (-88.556130, 30.365760),
    "lai chi van,china": (113.551110, 22.119720),
    "sunny isles beach,usa": (-80.122820, 25.950650),
    "rawtenstall,uk": (-2.284420, 53.700760),
    "roseburg,usa": (-123.341740, 43.216500),
    "chapchal,china": (81.147580, 43.835550),
    "merrick,usa": (-73.551520, 40.662880),
    "somerset,usa": (-74.488490, 40.497600),
    "moses lake,usa": (-119.278080, 47.130140),
    "greater northdale,usa": (-82.525940, 28.105450),
    "northdale,usa": (-82.505610, 28.093900),
    "summit,usa": (-74.364680, 40.715620),
    "xiejiawan,china": (105.171480, 34.812130),
    "alliance,usa": (-81.105930, 40.915340),
    "kalispell,usa": (-114.312910, 48.195790),
    "south holland,usa": (-87.606990, 41.600870),
    "dongta,china": (106.344440, 38.081400),
    "maguan,china": (106.033240, 35.066150),
    "kenmore,usa": (-122.244010, 47.757320),
    "retford,uk": (-0.943150, 53.322130),
    "del city,usa": (-97.440870, 35.442010),
    "derry,usa": (-71.327290, 42.880640),
    "renfrew,uk": (-4.392530, 55.871970),
    "hamtramck,usa": (-83.049640, 42.392820),
    "hoxtolgay,china": (86.002140, 46.518720),
    "zhouzhuang,china": (120.844270, 31.117880),
    "portadown,uk": (-6.444340, 54.423020),
    "heavitree,uk": (-3.496460, 50.720440),
    "marsiling,singapore": (103.774070, 1.432540),
    "great kills,usa": (-74.151530, 40.554270),
    "wekiwa springs,usa": (-81.425630, 28.698610),
    "berkhamsted,uk": (-0.565280, 51.760400),
    "duarte,usa": (-117.977290, 34.139450),
    "converse,usa": (-98.316120, 29.518010),
    "villa park,usa": (-87.988950, 41.889750),
    "zhouqu chengguanzhen,china": (104.362780, 33.784170),
    "park forest,usa": (-87.674490, 41.491420),
    "christiansburg,usa": (-80.408940, 37.129850),
    "pushun,china": (107.603260, 30.472410),
    "stanley,uk": (-1.698460, 54.867960),
    "jurupa valley,usa": (-117.516440, 33.992510),
    "ashland,usa": (-122.113850, 37.694650),
    "west and east lealman,usa": (-82.689440, 27.819930),
    "farragut,usa": (-84.153530, 35.884520),
    "paosha,china": (105.675720, 33.723530),
    "mount vernon triangle,usa": (-77.016850, 38.902320),
    "prairie village,usa": (-94.633570, 38.991670),
    "kam tin,china": (114.060190, 22.441230),
    "smithfield,usa": (-71.549510, 41.922040),
    "siyeke,china": (81.522980, 36.885270),
    "wadsworth,usa": (-81.729850, 41.025610),
    "dayang,china": (106.072050, 34.989750),
    "camas,usa": (-122.399540, 45.587060),
    "tsz ching estate,china": (114.200560, 22.350990),
    "swanley,uk": (0.173210, 51.397170),
    "fubang,china": (99.802860, 22.904180),
    "tongjiaxi,china": (106.444420, 29.684970),
    "fort walton beach,usa": (-86.617070, 30.420590),
    "fengjia,china": (108.784590, 29.393130),
    "tanglin,singapore": (103.816670, 1.316670),
    "geneva,usa": (-88.305350, 41.887530),
    "brent,usa": (-87.236080, 30.468810),
    "south euclid,usa": (-81.518460, 41.523110),
    "dashu,china": (109.321540, 31.210930),
    "newton-le-willows,uk": (-2.600000, 53.450000),
    "brushy creek,usa": (-97.739730, 30.513530),
    "rottingdean,uk": (-0.059390, 50.809840),
    "westchase,usa": (-82.609820, 28.055020),
    "sugar hill,usa": (-84.033520, 34.106490),
    "amersham,uk": (-0.616670, 51.666670),
    "chillicothe,usa": (-82.982400, 39.333120),
    "south lake tahoe,usa": (-119.984350, 38.933240),
    "anthem,usa": (-112.146820, 33.867260),
    "west carson,usa": (-118.292570, 33.821680),
    "massapequa,usa": (-73.474290, 40.680660),
    "lumberton,usa": (-79.010450, 34.618340),
    "jinlong,china": (106.060620, 29.513600),
    "hadley wood,uk": (-0.169810, 51.666690),
    "honglu,china": (105.726800, 29.351980),
    "taylors,usa": (-82.296230, 34.920390),
    "ossett,uk": (-1.580060, 53.679780),
    "yucca valley,usa": (-116.432240, 34.114170),
    "westford,usa": (-71.437840, 42.579260),
    "rittenhouse,usa": (-75.172120, 39.948450),
    "allison park,usa": (-79.958670, 40.559510),
    "shawan,china": (104.563700, 33.627360),
    "bay point,usa": (-121.961630, 38.029090),
    "sedalia,usa": (-93.228260, 38.704460),
    "naples,usa": (-81.795960, 26.142340),
    "jiangnan,china": (107.037150, 29.793130),
    "renxian,china": (107.678950, 30.660920),
    "patterson,usa": (-121.129660, 37.471600),
    "waynesboro,usa": (-78.889470, 38.068470),
    "h street ne,usa": (-76.995870, 38.900150),
    "richmond,uk": (-0.306330, 51.461710),
    "maldon,uk": (0.674630, 51.731100),
    "albertville,usa": (-86.208780, 34.267830),
    "old trafford,uk": (-2.288180, 53.457560),
    "wissinoming,usa": (-75.063230, 40.022330),
    "stoneham,usa": (-71.099500, 42.480100),
    "tustin legacy,usa": (-117.825880, 33.700060),
    "shangchong,china": (108.657850, 26.253180),
    "basking ridge,usa": (-74.549320, 40.706210),
    "perrysburg,usa": (-83.627160, 41.557000),
    "baoluan,china": (107.678340, 29.764160),
    "liuping,china": (105.719170, 34.891390),
    "speke,uk": (-2.841000, 53.340710),
    "garston,uk": (-2.900000, 53.333330),
    "bayi,china": (94.358920, 29.658120),
    "klamath falls,usa": (-121.781670, 42.224870),
    "green valley,usa": (-110.993700, 31.854250),
    "mandan,usa": (-100.889580, 46.826660),
    "okemos,usa": (-84.427470, 42.722260),
    "judian,china": (99.649100, 27.306120),
    "east moline,usa": (-90.444300, 41.500870),
    "west pensacola,usa": (-87.279690, 30.426590),
    "kinston,usa": (-77.581640, 35.262660),
    "guocun,china": (108.169330, 30.566180),
    "shelbyville,usa": (-86.460270, 35.483410),
    "buxton,uk": (-1.909820, 53.257410),
    "marquette,usa": (-87.395420, 46.543540),
    "hongzhou,china": (109.408890, 26.125830),
    "fairfield heights,usa": (-86.382240, 39.828610),
    "biddeford,usa": (-70.453380, 43.492580),
    "haidong zhen,china": (100.260610, 25.709790),
    "golden valley,usa": (-93.349120, 45.009690),
    "canyon lake,usa": (-98.262510, 29.875220),
    "conda,usa": (-111.532450, 42.728250),
    "south milwaukee,usa": (-87.860640, 42.910570),
    "horley,uk": (-0.159190, 51.174230),
    "marina,usa": (-121.802170, 36.684400),
    "cowes,uk": (-1.297810, 50.762520),
    "mukilteo,usa": (-122.304580, 47.944540),
    "barnes,uk": (-0.248390, 51.473520),
    "rancho san diego,usa": (-116.935300, 32.747270),
    "qitang,china": (106.285120, 29.778510),
    "pleasant plains,usa": (-77.030250, 38.930670),
    "qingping,china": (106.520570, 29.976960),
    "carrboro,usa": (-79.075290, 35.910140),
    "crest hill,usa": (-88.098670, 41.554750),
    "saint andrews,usa": (-81.101000, 34.043000),
    "dronfield,uk": (-1.475070, 53.302210),
    "ripley,uk": (-1.400000, 53.033330),
    "hays,usa": (-99.326770, 38.879180),
    "bathgate,uk": (-3.643980, 55.902040),
    "ha tsuen,china": (113.991600, 22.447240),
    "ferguson,usa": (-90.305390, 38.744220),
    "omagh,uk": (-7.300000, 54.600000),
    "laurelton,usa": (-73.746590, 40.670190),
    "march,uk": (0.088280, 52.551310),
    "lino lakes,usa": (-93.088830, 45.160240),
    "zhuantang,china": (106.668350, 28.896300),
    "west lake stevens,usa": (-122.101800, 47.993430),
    "new hope,usa": (-93.386620, 45.038020),
    "caohui,china": (107.469530, 30.397330),
    "stowmarket,uk": (0.997740, 52.188930),
    "palm river-clair mel,usa": (-82.379390, 27.923860),
    "trussville,usa": (-86.608880, 33.619830),
    "bangkit,singapore": (103.772510, 1.379820),
    "shuren,china": (107.739230, 29.986610),
    "xinyingpan,china": (100.920050, 27.167570),
    "shigu,china": (99.956280, 26.868520),
    "woodrow,usa": (-74.191060, 40.541500),
    "clevedon,uk": (-2.857860, 51.442270),
    "maesteg,uk": (-3.658230, 51.609260),
    "anju,china": (106.031860, 29.990660),
    "sanjianzai,china": (113.775760, 22.729110),
    "notting hill,uk": (-0.205870, 51.511500),
    "guiseley,uk": (-1.712320, 53.875610),
    "corinth,usa": (-97.064730, 33.154010),
    "mountlake terrace,usa": (-122.308740, 47.788150),
    "nixa,usa": (-93.294350, 37.043390),
    "east ridge,usa": (-85.251900, 35.014240),
    "bordon,uk": (-0.862450, 51.113570),
    "caterham,uk": (-0.078890, 51.282300),
    "grayslake,usa": (-88.041750, 42.344470),
    "agoura hills,usa": (-118.774530, 34.136390),
    "acton,usa": (-71.432840, 42.485090),
    "silver firs,usa": (-122.155100, 47.866020),
    "hauppauge,usa": (-73.202610, 40.825650),
    "kihei,usa": (-156.445780, 20.764620),
    "south el monte,usa": (-118.046730, 34.051950),
    "kaimuki,usa": (-157.801350, 21.279140),
    "arvin,usa": (-118.828430, 35.209130),
    "hongbao,china": (106.060260, 34.751910),
    "gardner,usa": (-94.927190, 38.810840),
    "lathrop,usa": (-121.276610, 37.822700),
    "sidney,usa": (-84.155500, 40.284220),
    "wallington,uk": (-0.153680, 51.364040),
    "tai wo hau,china": (114.123470, 22.367180),
    "gainsborough,uk": (-0.766670, 53.383330),
    "sweetwater,usa": (-80.373110, 25.763430),
    "milwaukie,usa": (-122.639260, 45.446230),
    "east millcreek,usa": (-111.810490, 40.699950),
    "goole,uk": (-0.877320, 53.703240),
    "sandhurst,uk": (-0.786550, 51.346750),
    "piqua,usa": (-84.242440, 40.144770),
    "lomita,usa": (-118.315070, 33.792240),
    "wanqiao zhen,china": (100.122790, 25.789240),
    "cockeysville,usa": (-76.643860, 39.481220),
    "easley,usa": (-82.601520, 34.829840),
    "new springville,usa": (-74.163200, 40.593440),
    "pleasantville,usa": (-74.524040, 39.389840),
    "gaofeng,china": (107.407880, 30.219680),
    "liberal,usa": (-100.921000, 37.043080),
    "palisades park,usa": (-73.997640, 40.848160),
    "jenks,usa": (-95.968330, 36.022870),
    "simpsonville,usa": (-82.254280, 34.737060),
    "latham,usa": (-73.759010, 42.747020),
    "heqing,china": (109.632790, 19.528310),
    "pleasant prairie,usa": (-87.933410, 42.553080),
    "harwich,uk": (1.284370, 51.941940),
    "pimlico,uk": (-0.136990, 51.488970),
    "noma,usa": (-77.005980, 38.903720),
    "mountain brook,usa": (-86.752210, 33.500940),
    "chambersburg,usa": (-77.661100, 39.937590),
    "adrian,usa": (-84.037170, 41.897550),
    "shek o,china": (114.251210, 22.233440),
    "chek chue,china": (114.212410, 22.218490),
    "west melbourne,usa": (-80.653390, 28.071680),
    "wuqiao,china": (108.455060, 30.779670),
    "east garfield park,usa": (-87.702830, 41.880870),
    "shanghe,china": (105.934030, 30.160360),
    "rotterdam,usa": (-73.970960, 42.787020),
    "east dereham,uk": (0.933330, 52.683330),
    "bellshill,uk": (-4.016670, 55.816670),
    "chesham,uk": (-0.600000, 51.700000),
    "kalihi valley,usa": (-157.842940, 21.363730),
    "bethany,usa": (-122.867600, 45.557890),
    "lake worth corridor,usa": (-80.101020, 26.616490),
    "gerrards cross,uk": (-0.555430, 51.586100),
    "heqian,china": (108.469730, 31.414970),
    "winter gardens,usa": (-116.933360, 32.831160),
    "wade hampton,usa": (-82.333170, 34.903730),
    "murphy,usa": (-96.613050, 33.015120),
    "coralville,usa": (-91.580450, 41.676400),
    "crowborough,uk": (0.163420, 51.060980),
    "ensley,usa": (-87.272750, 30.518810),
    "stamford,uk": (-0.483330, 52.650000),
    "stourport-on-severn,uk": (-2.280340, 52.339760),
    "gorseinon,uk": (-4.041630, 51.669310),
    "sapulpa,usa": (-96.114170, 35.998700),
    "failsworth,uk": (-2.165680, 53.504840),
    "american canyon,usa": (-122.260800, 38.174920),
    "south san jose hills,usa": (-117.904780, 34.012790),
    "nailsea,uk": (-2.758470, 51.432390),
    "wenheng,china": (116.754290, 25.667420),
    "daguan,china": (106.976940, 29.255000),
    "agoura,usa": (-118.737870, 34.143060),
    "sheung shui,china": (114.116670, 22.516670),
    "bayville,usa": (-74.154860, 39.909290),
    "wutongshu,china": (106.283330, 38.183330),
    "isleworth,uk": (-0.342460, 51.475180),
    "baijiawan,china": (105.288890, 34.695830),
    "arbutus,usa": (-76.699970, 39.254550),
    "chengjiao,china": (104.919630, 33.385200),
    "rongxi,china": (108.880380, 28.524850),
    "risca,uk": (-3.100810, 51.607990),
    "libertyville,usa": (-87.953130, 42.283080),
    "halewood,uk": (-2.831480, 53.359600),
    "beitun,china": (87.820530, 47.352490),
    "granite bay,usa": (-121.163840, 38.763230),
    "charlestown,usa": (-71.062000, 42.377870),
    "zishui,china": (108.314650, 31.412810),
    "alloa,uk": (-3.789970, 56.115860),
    "hong lok yuen,china": (114.155200, 22.463150),
    "zhuoshui,china": (108.770200, 29.303090),
    "newmarket,uk": (0.404180, 52.244670),
    "northfield,usa": (-93.161600, 44.458300),
    "rocky river,usa": (-81.839300, 41.475600),
    "raymore,usa": (-94.452730, 38.801950),
    "havelock,usa": (-76.901330, 34.879050),
    "golden,usa": (-105.221100, 39.755540),
    "bingley,uk": (-1.838570, 53.848610),
    "douglas,usa": (-87.618110, 41.834760),
    "cartersville,usa": (-84.802310, 34.165330),
    "oakleaf plantation,usa": (-81.835490, 30.170830),
    "brownhills,uk": (-1.933330, 52.633330),
    "affton,usa": (-90.333170, 38.550610),
    "ramona,usa": (-116.868080, 33.041710),
    "cambria heights,usa": (-73.738470, 40.694550),
    "elko,usa": (-115.763120, 40.832420),
    "hollis,usa": (-73.767080, 40.713440),
    "fairview park,china": (114.047660, 22.467380),
    "brooklyn heights,usa": (-73.993750, 40.695380),
    "nogales,usa": (-110.934250, 31.340380),
    "parma heights,usa": (-81.759580, 41.390050),
    "la canada flintridge,usa": (-118.187850, 34.199170),
    "mustang,usa": (-97.724490, 35.384230),
    "rose hill,usa": (-77.112760, 38.788720),
    "fulu,china": (107.968320, 30.654220),
    "east northport,usa": (-73.324560, 40.876760),
    "yateley,uk": (-0.829850, 51.343050),
    "burqin,china": (86.863750, 47.702830),
    "hythe,uk": (-1.401620, 50.860040),
    "glen avon,usa": (-117.484770, 34.011680),
    "newquay,uk": (-5.073190, 50.415570),
    "sulphur,usa": (-93.377380, 30.236590),
    "ma tau wai,china": (114.187430, 22.320740),
    "montville center,usa": (-72.151190, 41.478990),
    "ferndale,usa": (-83.134650, 42.460590),
    "south saint paul,usa": (-93.034940, 44.892740),
    "lynn haven,usa": (-85.648260, 30.245480),
    "lents,usa": (-122.567310, 45.479840),
    "sandown,uk": (-1.161030, 50.651580),
    "lake ronkonkoma,usa": (-73.131220, 40.835100),
    "atherton,uk": (-2.493540, 53.523710),
    "millburn,usa": (-74.304040, 40.724820),
    "murrysville,usa": (-79.697550, 40.428400),
    "stephenville,usa": (-98.202260, 32.220700),
    "colne,uk": (-2.168510, 53.857130),
    "oregon,usa": (-83.486880, 41.643660),
    "eastmont,usa": (-122.181540, 47.897400),
    "coconut grove,usa": (-80.256990, 25.712600),
    "west mifflin,usa": (-79.866440, 40.363400),
    "shilongba,china": (101.363250, 26.579270),
    "haddington,usa": (-75.237640, 39.965780),
    "chalfont saint peter,uk": (-0.556180, 51.608850),
    "tuqiang,china": (122.766670, 52.900000),
    "rensha,china": (107.594090, 30.053050),
    "mill creek,usa": (-122.204300, 47.860100),
    "pace,usa": (-87.161080, 30.599360),
    "hebian,china": (106.196730, 29.656630),
    "miamisburg,usa": (-84.286610, 39.642840),
    "ampthill,uk": (-0.495670, 52.026940),
    "palm valley,usa": (-81.387580, 30.177460),
    "rolla,usa": (-91.771270, 37.951430),
    "tukwila,usa": (-122.260960, 47.473990),
    "swinton,uk": (-2.350000, 53.500000),
    "portslade,uk": (-0.216080, 50.842860),
    "kingswinford,uk": (-2.168890, 52.497550),
    "chislehurst,uk": (0.068580, 51.417090),
    "bowthorpe,uk": (1.218850, 52.638840),
    "kempston hardwick,uk": (-0.499080, 52.089560),
    "sungai simpang,singapore": (103.826670, 1.438060),
    "new caney,usa": (-95.211320, 30.155220),
    "debary,usa": (-81.308680, 28.883050),
    "lyndhurst,usa": (-74.124310, 40.812040),
    "lake zurich,usa": (-88.093410, 42.196970),
    "arewusitang,china": (81.524350, 43.797730),
    "bryant,usa": (-92.489050, 34.595930),
    "eustis,usa": (-81.685350, 28.852770),
    "hailsham,uk": (0.257750, 50.862200),
    "newburg,usa": (-85.659680, 38.160070),
    "johnstown,usa": (-78.921970, 40.326740),
    "socastee,usa": (-78.998370, 33.683500),
    "dumbarton,uk": (-4.570610, 55.944330),
    "ypsilanti,usa": (-83.612990, 42.241150),
    "north bellmore,usa": (-73.533460, 40.691490),
    "king of prussia,usa": (-75.396020, 40.089270),
    "hayesville,usa": (-122.982870, 44.985950),
    "cortlandt manor,usa": (-73.871640, 41.280000),
    "warrensburg,usa": (-93.736050, 38.762790),
    "tai wai,china": (114.178970, 22.372860),
    "mokena,usa": (-87.889220, 41.526140),
    "poulton-le-fylde,uk": (-2.983330, 53.833330),
    "mariners harbor,usa": (-74.158750, 40.636770),
    "brough,uk": (-0.572150, 53.728610),
    "leek,uk": (-2.022070, 53.104340),
    "bonney lake,usa": (-122.186510, 47.177050),
    "lealman,usa": (-82.679270, 27.821140),
    "kempston,uk": (-0.500440, 52.115990),
    "penzance,uk": (-5.537150, 50.118610),
    "waikiki,usa": (-157.835940, 21.285500),
    "wujian,china": (105.834360, 29.182090),
    "dinnington,uk": (-1.200000, 53.366670),
    "hermosa beach,usa": (-118.399520, 33.862240),
    "fengle,china": (108.414610, 31.189750),
    "selden,usa": (-73.035660, 40.866490),
    "clemmons,usa": (-80.382000, 36.021530),
    "west chester,usa": (-75.608040, 39.960970),
    "evergreen park,usa": (-87.701720, 41.720590),
    "southbury,usa": (-73.213170, 41.481480),
    "ho man tin,china": (114.181810, 22.315840),
    "faversham,uk": (0.888560, 51.314800),
    "yisilamu'awati,china": (80.184010, 37.584910),
    "brickworks estate,singapore": (103.808330, 1.287220),
    "paikeqi,china": (77.208250, 38.550110),
    "marblehead,usa": (-70.857830, 42.500100),
    "norton,usa": (-71.186990, 41.966770),
    "plattsburgh,usa": (-73.452910, 44.699490),
    "lirang,china": (107.631450, 30.684940),
    "xambabazar,china": (81.509720, 36.886390),
    "north salt lake,usa": (-111.906880, 40.848560),
    "sand springs,usa": (-96.108890, 36.139810),
    "tewkesbury,uk": (-2.160100, 51.992440),
    "painesville,usa": (-81.245660, 41.724490),
    "fuyun,china": (89.521150, 46.991900),
    "cheung chau,china": (114.027870, 22.210850),
    "diamond head / kapahulu / saint louis heights,usa": (-157.811270, 21.276970),
    "hartranft,usa": (-75.147120, 39.984830),
    "pickerington,usa": (-82.753500, 39.884230),
    "new canaan,usa": (-73.494840, 41.146760),
    "snellville,usa": (-84.019910, 33.857330),
    "fox chase,usa": (-75.080170, 40.081220),
    "sparta,usa": (-74.638490, 41.033430),
    "shui chuen o,china": (114.197780, 22.371610),
    "holtsville,usa": (-73.045110, 40.815380),
    "lichuan zhen,china": (104.319470, 34.248450),
    "salmon creek,usa": (-122.648990, 45.710670),
    "kingsessing,usa": (-75.229630, 39.936780),
    "antrim,uk": (-6.211000, 54.717500),
    "la crescenta-montrose,usa": (-118.235290, 34.232160),
    "spanish lake,usa": (-90.215940, 38.787830),
    "zhongzhai,china": (104.420090, 33.191330),
    "willmar,usa": (-95.043340, 45.121910),
    "yajiang,china": (107.373690, 29.454770),
    "soho,uk": (-0.135350, 51.514400),
    "kirkintilloch,uk": (-4.152620, 55.939330),
    "qingfeng,china": (105.826760, 29.339380),
    "tysons,usa": (-77.231090, 38.918720),
    "samuyuzi,china": (81.863980, 43.719470),
    "forest lake,usa": (-92.985220, 45.278860),
    "san tin,china": (114.069320, 22.501660),
    "norris green,uk": (-2.920730, 53.445130),
    "heyan,china": (108.670450, 31.356390),
    "earl shilton,uk": (-1.315360, 52.576820),
    "lynbrook,usa": (-73.671800, 40.654830),
    "orchards,usa": (-122.560930, 45.666510),
    "eastchester,usa": (-73.808610, 40.958330),
    "payson,usa": (-111.732150, 40.044400),
    "tiverton,uk": (-3.492320, 50.902410),
    "dingshi,china": (108.546460, 28.775490),
    "west saint paul,usa": (-93.101610, 44.916080),
    "madisonville,usa": (-87.498890, 37.328100),
    "ives estates,usa": (-80.176710, 25.962310),
    "langgar,china": (81.500000, 36.700000),
    "papillion,usa": (-96.042240, 41.154440),
    "badger,usa": (-147.533330, 64.800000),
    "adwick le street,uk": (-1.184540, 53.570770),
    "seymour,usa": (-85.890250, 38.959220),
    "lake shore,usa": (-76.484960, 39.107050),
    "baolong,china": (110.005880, 30.942290),
    "weybridge,uk": (-0.459750, 51.371780),
    "blackwall,uk": (-0.001600, 51.509710),
    "south ockendon,uk": (0.283330, 51.507990),
    "mckeesport,usa": (-79.864220, 40.347850),
    "pinecrest,usa": (-80.308110, 25.667050),
    "weirton heights,usa": (-80.539240, 40.408400),
    "port angeles,usa": (-123.430740, 48.118150),
    "gulou,china": (106.171680, 30.175990),
    "irlam,uk": (-2.423230, 53.442530),
    "longkong,china": (107.914900, 30.044770),
    "hazel dell,usa": (-122.662880, 45.671510),
    "chessington,uk": (-0.304270, 51.362400),
    "angleton,usa": (-95.431880, 29.169410),
    "fernley,usa": (-119.251830, 39.607970),
    "alice,usa": (-98.069720, 27.752250),
    "battle ground,usa": (-122.533430, 45.780950),
    "tuen mun san hui,china": (113.975960, 22.398770),
    "waina,china": (105.049720, 33.206390),
    "dixon,usa": (-121.823300, 38.445460),
    "forest park,usa": (-84.369090, 33.622050),
    "longmen,china": (107.687120, 30.798190),
    "shitan,china": (106.502910, 30.068960),
    "mamaroneck,usa": (-73.732630, 40.948710),
    "olympic,china": (114.157360, 22.319390),
    "bear,usa": (-75.658260, 39.629280),
    "melksham,uk": (-2.140020, 51.372810),
    "bayou cane,usa": (-90.751200, 29.624100),
    "horsforth,uk": (-1.637540, 53.842600),
    "alsip,usa": (-87.738660, 41.668920),
    "lutz,usa": (-82.461480, 28.151120),
    "discovery bay,china": (114.016670, 22.300000),
    "green haven,usa": (-76.547740, 39.139550),
    "telok blangah,singapore": (103.811670, 1.274720),
    "bellwood,usa": (-87.883120, 41.881420),
    "clydach,uk": (-3.900000, 51.683330),
    "dukinfield,uk": (-2.088090, 53.474970),
    "sansheng,china": (106.626500, 29.892560),
    "clayton,usa": (-78.456390, 35.650710),
    "central falls,usa": (-71.392280, 41.890660),
    "sun valley,usa": (-119.776020, 39.596300),
    "horizon city,usa": (-106.207480, 31.692610),
    "orinda,usa": (-122.179690, 37.877150),
    "pinole,usa": (-122.298860, 38.004370),
    "helin,china": (107.680640, 30.581230),
    "budai,taiwan": (120.161540, 23.377950),
    "sun city center,usa": (-82.351760, 27.718090),
    "altamont,usa": (-121.737220, 42.206810),
    "howard,usa": (-88.088160, 44.543600),
    "niu valley,usa": (-157.737060, 21.284300),
    "alamo,usa": (-98.123060, 26.183690),
    "broadview heights,usa": (-81.685130, 41.313940),
    "upper saint clair,usa": (-80.083390, 40.335900),
    "haslett,usa": (-84.401080, 42.746980),
    "west elsdon,usa": (-87.724500, 41.793920),
    "baytokay,china": (81.788890, 43.681670),
    "glassboro,usa": (-75.111840, 39.702890),
    "altus,usa": (-99.333980, 34.638130),
    "blythe,usa": (-114.596350, 33.610300),
    "jiangluo,china": (105.821940, 33.901390),
    "silverdale,usa": (-122.694870, 47.644540),
    "the peak,china": (114.156490, 22.262020),
    "matteson,usa": (-87.713100, 41.503920),
    "great wyrley,uk": (-2.011110, 52.662770),
    "tumwater,usa": (-122.909310, 47.007320),
    "yarm,uk": (-1.357930, 54.503640),
    "old jamestown,usa": (-90.285110, 38.834940),
    "tonggu,china": (108.682580, 28.781690),
    "shoreham-by-sea,uk": (-0.274310, 50.834130),
    "weirton,usa": (-80.589520, 40.418960),
    "shaoyun,china": (105.984210, 29.984580),
    "white oak,usa": (-84.599390, 39.213110),
    "boon lay,singapore": (103.694000, 1.311000),
    "pinner,uk": (-0.382160, 51.593840),
    "carlisle,usa": (-77.188870, 40.201480),
    "mineola,usa": (-73.640680, 40.749270),
    "baijia,china": (107.325760, 30.017040),
    "tullahoma,usa": (-86.209430, 35.362020),
    "ozark,usa": (-93.206020, 37.020890),
    "secaucus,usa": (-74.056530, 40.789550),
    "fairwood,usa": (-122.157340, 47.448430),
    "camp springs,usa": (-76.906640, 38.804000),
    "ely,uk": (0.261960, 52.399640),
    "jiaogong,china": (104.646370, 33.565470),
    "ronkonkoma,usa": (-73.143000, 40.821000),
    "sung wong toi,china": (114.191490, 22.324660),
    "saco,usa": (-70.442830, 43.500920),
    "maple shade,usa": (-74.992390, 39.952610),
    "gangjia,china": (107.504030, 30.220550),
    "east massapequa,usa": (-73.436510, 40.673430),
    "amherst center,usa": (-72.519250, 42.375370),
    "montrose,usa": (-107.876170, 38.478320),
    "marion oaks,usa": (-82.183150, 29.008590),
    "brownwood,usa": (-98.991160, 31.709320),
    "southbridge,usa": (-72.033410, 42.075100),
    "deerfield,usa": (-87.844510, 42.171140),
    "castaic,usa": (-118.622870, 34.488880),
    "ennis,usa": (-96.625270, 32.329310),
    "ellensburg,usa": (-120.547850, 46.996510),
    "columbia city,usa": (-122.275400, 47.563990),
    "claremore,usa": (-95.616090, 36.312600),
    "waukee,usa": (-93.885230, 41.611660),
    "jasmine estates,usa": (-82.690100, 28.293060),
    "melville,usa": (-73.415120, 40.793430),
    "petworth,usa": (-77.024980, 38.945940),
    "kew gardens,usa": (-73.830970, 40.714270),
    "middleton,usa": (-89.504290, 43.097220),
    "hook,uk": (-0.306500, 51.368030),
    "bartow,usa": (-81.843140, 27.896410),
    "sylvania,usa": (-83.712990, 41.718940),
    "baoxing,china": (105.692650, 29.621730),
    "mengman,china": (100.887850, 22.321570),
    "rio rico,usa": (-110.976480, 31.471480),
    "sanxi,china": (110.094030, 31.132020),
    "ala moana - kakaako,usa": (-157.856710, 21.296490),
    "so uk,china": (114.156790, 22.341310),
    "north druid hills,usa": (-84.313260, 33.816770),
    "north bay shore,usa": (-73.260200, 40.753000),
    "stonegate,usa": (-117.740090, 33.705340),
    "milledgeville,usa": (-83.232100, 33.080140),
    "cortland,usa": (-76.180480, 42.601180),
    "suhe,china": (105.222100, 34.062500),
    "qiemo,china": (85.529920, 38.133870),
    "nether edge,uk": (-1.487590, 53.359340),
    "jiaping,china": (106.348420, 28.991650),
    "berea,usa": (-81.854300, 41.366160),
    "capitol riverfront,usa": (-77.003140, 38.877960),
    "twinsburg,usa": (-81.440110, 41.312560),
    "wantagh,usa": (-73.510130, 40.683710),
    "west hempstead,usa": (-73.650130, 40.704820),
    "mangnai zhen,china": (90.155530, 38.385540),
    "humberstone,uk": (-1.086470, 52.647380),
    "ansonia,usa": (-73.079000, 41.346210),
    "kowloon tong,china": (114.179690, 22.333120),
    "maliuzui,china": (106.943990, 29.692860),
    "dashun,china": (107.045420, 29.570070),
    "mayfield heights,usa": (-81.457900, 41.519220),
    "south elmsall,uk": (-1.280340, 53.597090),
    "syosset,usa": (-73.502070, 40.826210),
    "zhendong,china": (108.395440, 31.185170),
    "golders green,uk": (-0.200330, 51.576310),
    "brook park,usa": (-81.804580, 41.398380),
    "hebburn,uk": (-1.515460, 54.973020),
    "union hill-novelty hill,usa": (-122.028330, 47.678870),
    "siu sai wan estate,china": (114.248810, 22.261550),
    "tuohula,china": (79.692830, 37.242270),
    "mirfield,uk": (-1.696360, 53.673430),
    "erlanger,usa": (-84.600780, 39.016730),
    "park view,usa": (-77.023590, 38.932060),
    "rossville,usa": (-74.210190, 40.549290),
    "south burlington,usa": (-73.170960, 44.466990),
    "mount greenwood,usa": (-87.708660, 41.698090),
    "emsworth,uk": (-0.936970, 50.847790),
    "sai wan ho,china": (114.223200, 22.284490),
    "casa de oro-mount helix,usa": (-116.968770, 32.763970),
    "langley park,usa": (-76.981360, 38.988720),
    "brigham city,usa": (-112.015500, 41.510210),
    "kaqun,china": (76.867220, 37.978060),
    "aberystwyth,uk": (-4.082920, 52.415480),
    "so uk estate,china": (114.156530, 22.341530),
    "oswestry,uk": (-3.054970, 52.861950),
    "fairmont,usa": (-80.142580, 39.485080),
    "shekou,china": (113.915600, 22.493590),
    "fairhope,usa": (-87.903330, 30.522970),
    "dongjia,china": (107.705740, 30.223520),
    "mission hill,usa": (-71.108450, 42.334370),
    "tak long estate,china": (114.203380, 22.330200),
    "greater upper marlboro,usa": (-76.748270, 38.831420),
    "frederickson,usa": (-122.358730, 47.096210),
    "keng hau,china": (114.174720, 22.365070),
    "prestatyn,uk": (-3.407760, 53.337480),
    "horwich,uk": (-2.549750, 53.601260),
    "iselin,usa": (-74.322370, 40.575380),
    "suwanee,usa": (-84.071300, 34.051490),
    "whitehall,usa": (-82.885460, 39.966730),
    "lancing,uk": (-0.322470, 50.828820),
    "rutherford,usa": (-74.106810, 40.826490),
    "islip,usa": (-73.210390, 40.729820),
    "un chau estate,china": (114.156160, 22.336330),
    "weiwu'eryuqiwen,china": (81.860630, 43.755980),
    "lam tin,china": (114.236340, 22.309330),
    "tongle,china": (107.197030, 29.461210),
    "kirkdale,uk": (-2.976570, 53.433420),
    "cuiyun,china": (106.588520, 29.688170),
    "marshfield,usa": (-90.171800, 44.668850),
    "rawmarsh,uk": (-1.344370, 53.460620),
    "eastwood,uk": (-1.300000, 53.000000),
    "lorton,usa": (-77.227760, 38.704280),
    "apengjiang,china": (108.742890, 29.151960),
    "kokyar,china": (81.633340, 36.818990),
    "peacehaven,uk": (-0.006520, 50.792700),
    "lei tung estate,china": (114.155230, 22.241150),
    "yinping,china": (107.575180, 30.541970),
    "gautier,usa": (-88.611690, 30.385750),
    "bourbonnais,usa": (-87.887540, 41.153760),
    "goodings grove,usa": (-87.930890, 41.629200),
    "west molesey,uk": (-0.379970, 51.399850),
    "east molesey,uk": (-0.349160, 51.398720),
    "longchang,china": (107.916670, 26.666670),
    "ciyun,china": (106.205600, 29.075410),
    "macomb,usa": (-90.671800, 40.459210),
    "hudiyuzi,china": (81.412120, 43.925510),
    "nuofu,china": (99.699570, 22.220010),
    "point pleasant,usa": (-74.068190, 40.083170),
    "bellaire,usa": (-95.458830, 29.705790),
    "el reno,usa": (-97.955050, 35.532270),
    "east mount airy,usa": (-75.187500, 40.064500),
    "southsea,uk": (-1.090710, 50.783510),
    "chowchilla,usa": (-120.260180, 37.123000),
    "mead valley,usa": (-117.296150, 33.833350),
    "wantage,uk": (-1.425650, 51.588460),
    "qianhu,china": (105.577780, 34.804720),
    "hyattsville,usa": (-76.945530, 38.955940),
    "isle of lewis,uk": (-6.388030, 58.219010),
    "wealdstone,uk": (-0.337110, 51.599830),
    "happy valley,usa": (-122.530370, 45.446790),
    "onalaska,usa": (-91.235140, 43.884410),
    "round lake,usa": (-88.093410, 42.353360),
    "stafford,usa": (-95.557720, 29.616070),
    "uckfield,uk": (0.095890, 50.969480),
    "yorkville,usa": (-88.447290, 41.641140),
    "peterhead,uk": (-1.784350, 57.505170),
    "north ogden,usa": (-111.960220, 41.307160),
    "bensenville,usa": (-87.940070, 41.955030),
    "larne,uk": (-5.816670, 54.850000),
    "forney,usa": (-96.471930, 32.748180),
    "monsey,usa": (-74.068480, 41.111210),
    "fern creek,usa": (-85.587740, 38.159790),
    "wushipai,china": (113.909690, 22.523830),
    "shenandoah,usa": (-91.000940, 30.401300),
    "kaitang,china": (108.129720, 26.720280),
    "el dorado,usa": (-92.666270, 33.207630),
    "ashtabula,usa": (-80.789810, 41.865050),
    "natchitoches,usa": (-93.086270, 31.760720),
    "ottawa,usa": (-88.842580, 41.345590),
    "outram park,singapore": (103.838060, 1.282500),
    "lingquan,china": (117.677000, 49.405200),
    "shafter,usa": (-119.271780, 35.500510),
    "mansfield woodhouse,uk": (-1.193840, 53.164950),
    "shaoyu,china": (105.365100, 34.064080),
    "guchang,china": (105.588630, 29.486840),
    "danzi,china": (108.005920, 30.857000),
    "jiuchao,china": (108.765280, 26.090830),
    "amesbury,usa": (-70.930050, 42.858420),
    "grove,uk": (-1.421870, 51.609540),
    "franklin park,usa": (-87.865620, 41.935310),
    "meadowbrook,usa": (-77.473530, 37.448820),
    "mcalester,usa": (-95.769710, 34.933430),
    "quankou,china": (101.739300, 37.352220),
    "punta gorda isles,usa": (-82.078420, 26.917560),
    "hadleigh,uk": (0.609830, 51.552690),
    "north watford,uk": (-0.394460, 51.680720),
    "dianshui,china": (108.089000, 29.283390),
    "palestine,usa": (-95.630790, 31.762120),
    "sherrelwood,usa": (-105.001370, 39.837760),
    "yongping,china": (105.272250, 34.289940),
    "creve coeur,usa": (-90.422620, 38.660890),
    "ballenger creek,usa": (-77.435260, 39.372600),
    "cinco ranch,usa": (-95.758000, 29.738840),
    "oytograk,china": (81.933330, 36.833330),
    "marlow,uk": (-0.774150, 51.569330),
    "palmer,usa": (-72.328690, 42.158430),
    "erong,china": (109.288370, 28.571280),
    "belle glade,usa": (-80.667560, 26.684510),
    "makakilo,usa": (-158.086550, 21.352370),
    "franconia,usa": (-77.146370, 38.782060),
    "marple,uk": (-2.062920, 53.394520),
    "hong'an,china": (109.266610, 28.502280),
    "fulwood,uk": (-1.550000, 53.350000),
    "eastlake,usa": (-81.450390, 41.653940),
    "cameron park,usa": (-120.987160, 38.668790),
    "steubenville,usa": (-80.633960, 40.369790),
    "springboro,usa": (-84.233270, 39.552280),
    "wallingford center,usa": (-72.818920, 41.449870),
    "chapel allerton,uk": (-1.538340, 53.829010),
    "san po kong,china": (114.196690, 22.335460),
    "lanham-seabrook,usa": (-76.851080, 38.968350),
    "clark-fulton,usa": (-81.709790, 41.464020),
    "pampa,usa": (-100.959870, 35.536160),
    "gaolou,china": (104.676680, 34.760840),
    "florida ridge,usa": (-80.386720, 27.580310),
    "five corners,usa": (-122.575100, 45.684560),
    "boone,usa": (-81.674550, 36.216790),
    "seminole,usa": (-82.791210, 27.839750),
    "jianlong,china": (106.185220, 29.358600),
    "punta gorda,usa": (-82.045370, 26.929780),
    "rosamond,usa": (-118.163410, 34.864140),
    "longlin,china": (105.067390, 33.942780),
    "puzi,china": (108.328250, 29.632920),
    "baiguan,china": (104.914440, 33.966170),
    "lop,china": (80.181820, 37.078910),
    "bibo,china": (107.631390, 26.530830),
    "cutler,usa": (-80.310610, 25.615100),
    "mattoon,usa": (-88.372830, 39.483090),
    "baohe,china": (107.701720, 30.060840),
    "brymbo,uk": (-3.066670, 53.066670),
    "arroyo grande,usa": (-120.590730, 35.118590),
    "anacortes,usa": (-122.612670, 48.512600),
    "east barnet,uk": (-0.161030, 51.646740),
    "xiaochuan,china": (105.561560, 33.680600),
    "hok yuen,china": (114.188160, 22.310270),
    "laguna verde,china": (114.190710, 22.307190),
    "rancho mirage,usa": (-116.412790, 33.739740),
    "shek kip mei,china": (114.167990, 22.331460),
    "limerick,usa": (-75.522120, 40.230930),
    "mililani mauka / launani valley,usa": (-157.987990, 21.478850),
    "waltham abbey,uk": (-0.004210, 51.687000),
    "devizes,uk": (-1.994210, 51.350840),
    "wilton,usa": (-73.437900, 41.195370),
    "ojus,usa": (-80.150600, 25.948430),
    "santa fe springs,usa": (-118.085350, 33.947240),
    "vincennes,usa": (-87.528630, 38.677270),
    "amsterdam,usa": (-74.188190, 42.938690),
    "durango,usa": (-107.880070, 37.275280),
    "guangpu,china": (106.145210, 29.335670),
    "dumont,usa": (-73.996810, 40.940650),
    "hampton,uk": (-0.367010, 51.413340),
    "hanahan,usa": (-80.022030, 32.918510),
    "central point,usa": (-122.916430, 42.375960),
    "elizabeth city,usa": (-76.251050, 36.294600),
    "dalserf,uk": (-3.916670, 55.733330),
    "dongchuan,china": (101.835650, 37.367970),
    "newburyport,usa": (-70.877280, 42.812590),
    "rockland,usa": (-70.916160, 42.130660),
    "hedge end,uk": (-1.300760, 50.912340),
    "westbrook,usa": (-70.371160, 43.677030),
    "sandbach,uk": (-2.362510, 53.145150),
    "new mills,uk": (-1.999860, 53.365920),
    "st. marys,usa": (-81.546490, 30.730510),
    "lackawanna,usa": (-78.823370, 42.825610),
    "heng fa chuen,china": (114.240770, 22.276680),
    "arix,china": (81.607650, 36.755410),
    "arele,china": (81.666870, 36.812950),
    "westerly,usa": (-71.827290, 41.377600),
    "maumelle,usa": (-92.404320, 34.866760),
    "wangyao,china": (105.541670, 34.885000),
    "aldrich bay,china": (114.224740, 22.282030),
    "leland,usa": (-78.044710, 34.256280),
    "changtan,china": (108.599760, 30.739160),
    "ascot,uk": (-0.674800, 51.410820),
    "wisconsin rapids,usa": (-89.817350, 44.383580),
    "lenoir,usa": (-81.538980, 35.914020),
    "north massapequa,usa": (-73.462070, 40.700930),
    "scarsdale,usa": (-73.784580, 41.005100),
    "nanuet,usa": (-74.013470, 41.088710),
    "gretna,usa": (-90.053960, 29.914650),
    "sheridan,usa": (-106.956180, 44.797190),
    "north amityville,usa": (-73.425120, 40.697600),
    "manchester city centre,uk": (-2.245550, 53.480970),
    "tacony,usa": (-75.044340, 40.031220),
    "arcata,usa": (-124.082840, 40.866520),
    "hannibal,usa": (-91.358480, 39.708380),
    "wahiawa,usa": (-158.024640, 21.502790),
    "nima,china": (102.071270, 34.000650),
    "colonial heights,usa": (-77.407260, 37.268040),
    "choi hung estate,china": (114.205810, 22.336360),
    "colonia,usa": (-74.302090, 40.574550),
    "logansport,usa": (-86.356670, 40.754480),
    "linda,usa": (-121.550800, 39.127670),
    "tinton falls,usa": (-74.100420, 40.304280),
    "abergele,uk": (-3.582200, 53.284360),
    "spennymoor,uk": (-1.602290, 54.698800),
    "youchou,china": (109.141470, 28.963460),
    "godfrey,usa": (-90.186780, 38.955600),
    "times square,usa": (-73.986440, 40.756360),
    "dorking,uk": (-0.333800, 51.232280),
    "lugu,taiwan": (120.752500, 23.746390),
    "west garfield park,usa": (-87.729220, 41.880590),
    "ramsbottom,uk": (-2.316830, 53.647890),
    "willimantic,usa": (-72.208130, 41.710650),
    "liulin,china": (103.504170, 34.589720),
    "calverton,usa": (-76.935810, 39.057610),
    "oxon hill,usa": (-76.989700, 38.803450),
    "amersham on the hill,uk": (-0.607420, 51.674680),
    "takoma park,usa": (-77.007480, 38.977890),
    "wallingford,usa": (-72.823160, 41.457040),
    "sycamore,usa": (-88.686750, 41.988920),
    "cocoa,usa": (-80.742000, 28.386120),
    "jiuchi,china": (108.370890, 30.798340),
    "martinsburg,usa": (-77.963890, 39.456210),
    "marco island,usa": (-81.718420, 25.941210),
    "tiffin,usa": (-83.177970, 41.114500),
    "hunting park,usa": (-75.143790, 40.016500),
    "albert lea,usa": (-93.368270, 43.648010),
    "golden triangle,usa": (-77.043620, 38.905240),
    "moreton,uk": (-3.116670, 53.400000),
    "biddulph,uk": (-2.175840, 53.117240),
    "bishopstoke,uk": (-1.328320, 50.966430),
    "south hadley,usa": (-72.574530, 42.258420),
    "ferndown,uk": (-1.899750, 50.807430),
    "tai shui hang,china": (114.223850, 22.406310),
    "juniata park,usa": (-75.108790, 40.008450),
    "shaw,usa": (-77.021370, 38.912060),
    "ocean springs,usa": (-88.827810, 30.411310),
    "yongcheng,china": (106.820120, 29.021330),
    "hinsdale,usa": (-87.937010, 41.800860),
    "yangjiaying,china": (111.693010, 39.480550),
    "brightwood,usa": (-77.027480, 38.961220),
    "barrhead,uk": (-4.392850, 55.799160),
    "winthrop,usa": (-70.982830, 42.375100),
    "lindenwold,usa": (-74.997670, 39.824280),
    "jiayi,china": (81.635450, 36.854810),
    "kenwood,usa": (-87.597550, 41.809200),
    "hopkins,usa": (-93.462730, 44.924960),
    "bethnal green,uk": (-0.061090, 51.527180),
    "dunbage,china": (77.504740, 38.857390),
    "allendale,usa": (-85.953650, 42.972250),
    "paipu,china": (109.158610, 19.639810),
    "back bay,usa": (-71.087000, 42.350100),
    "ware,uk": (-0.028750, 51.810580),
    "wo che,china": (114.192170, 22.390160),
    "menasha,usa": (-88.446500, 44.202210),
    "palos hills,usa": (-87.817000, 41.696700),
    "prunedale,usa": (-121.669670, 36.775790),
    "culpeper,usa": (-77.996660, 38.473180),
    "stevenson ranch,usa": (-118.573720, 34.390480),
    "tai mei tuk,china": (114.234580, 22.474470),
    "south houston,usa": (-95.235490, 29.663010),
    "kirksville,usa": (-92.583250, 40.194750),
    "maltby,uk": (-1.200000, 53.416670),
    "tallmadge,usa": (-81.441780, 41.101450),
    "north babylon,usa": (-73.321790, 40.716490),
    "liuyin,china": (106.609960, 29.962070),
    "bayswater,uk": (-0.184260, 51.511160),
    "warminster,uk": (-2.178730, 51.204340),
    "xiaba,china": (106.510060, 29.116840),
    "tuantian,china": (98.653200, 24.711300),
    "new philadelphia,usa": (-81.445670, 40.489790),
    "saint matthews,usa": (-85.655790, 38.252850),
    "teignmouth,uk": (-3.496710, 50.545810),
    "maitland,usa": (-81.363120, 28.627780),
    "walton-on-the-naze,uk": (1.267380, 51.848190),
    "north aurora,usa": (-88.327300, 41.806140),
    "safety harbor,usa": (-82.693160, 27.990850),
    "maliu,china": (108.244630, 31.434210),
    "north canton,usa": (-81.402340, 40.875890),
    "tynemouth,uk": (-1.425590, 55.017880),
    "kadoorie,china": (114.175560, 22.322470),
    "east hemet,usa": (-116.938910, 33.740020),
    "hongguang qidui,china": (106.287210, 38.733220),
    "oi man estate,china": (114.178530, 22.311970),
    "radford,usa": (-80.576450, 37.131790),
    "tillmans corner,usa": (-88.170840, 30.590190),
    "nicetown-tioga,usa": (-75.163870, 40.009890),
    "detroit-shoreway,usa": (-81.729910, 41.477720),
    "bushey,uk": (-0.360530, 51.643160),
    "gelligaer,uk": (-3.256110, 51.664440),
    "sleaford,uk": (-0.409410, 52.998260),
    "houba,china": (108.506280, 31.205090),
    "huoshilafu,china": (76.695790, 37.866420),
    "anoka,usa": (-93.387180, 45.197740),
    "east cleveland,usa": (-81.579010, 41.533110),
    "sudbury,usa": (-71.416170, 42.383430),
    "jianshan,china": (108.895330, 31.433960),
    "haydock,uk": (-2.681660, 53.467230),
    "plainville,usa": (-72.858160, 41.674540),
    "discovery park,china": (114.111410, 22.376210),
    "eman,china": (109.262710, 19.857230),
    "ada,usa": (-96.678340, 34.774530),
    "mountsorrel,uk": (-1.150000, 52.716670),
    "lewes,uk": (0.008800, 50.873980),
    "erlang,china": (105.992130, 30.362640),
    "thorne,uk": (-0.963080, 53.611220),
    "glassmanor,usa": (-76.998590, 38.819000),
    "south orange,usa": (-74.261260, 40.748990),
    "fuyong,china": (113.815190, 22.672140),
    "idylwood,usa": (-77.211650, 38.895110),
    "seabrook,usa": (-76.849000, 38.974000),
    "durant,usa": (-96.370820, 33.993990),
    "killingly center,usa": (-71.869240, 41.838710),
    "kings park,usa": (-73.257340, 40.886210),
    "grangemouth,uk": (-3.721830, 56.011410),
    "calne,uk": (-2.005710, 51.438790),
    "canby,usa": (-122.692590, 45.262900),
    "poplar bluff,usa": (-90.392890, 36.757000),
    "moraga,usa": (-122.129690, 37.834930),
    "friern barnet,uk": (-0.158530, 51.613280),
    "gongtan,china": (108.348560, 28.907720),
    "redland,usa": (-77.144150, 39.145390),
    "massapequa park,usa": (-73.455120, 40.680380),
    "nantwich,uk": (-2.520510, 53.068780),
    "kuna,usa": (-116.420120, 43.491830),
    "tuchang,china": (106.490700, 29.925300),
    "foley,usa": (-87.683600, 30.406590),
    "ruskin,usa": (-82.433150, 27.720860),
    "hermiston,usa": (-119.289460, 45.840410),
    "siwei,china": (114.153280, 38.016570),
    "nederland,usa": (-93.992400, 29.974380),
    "wudong,china": (107.341270, 30.209900),
    "heishui,china": (108.796360, 29.055510),
    "ashwaubenon,usa": (-88.070100, 44.482210),
    "longshe,china": (108.211260, 29.530860),
    "harlesden,uk": (-0.250200, 51.538110),
    "wath upon dearne,uk": (-1.345800, 53.502910),
    "romsey,uk": (-1.499890, 50.989060),
    "primrose place,uk": (-0.108870, 52.560610),
    "live oak,usa": (-121.980520, 36.983560),
    "brockley,uk": (-0.036520, 51.463690),
    "cirencester,uk": (-1.971450, 51.719270),
    "wanshui,china": (107.987220, 26.735280),
    "okolona,usa": (-85.687740, 38.141180),
    "wyckoff,usa": (-74.172920, 41.009540),
    "woodmere,usa": (-73.712630, 40.632050),
    "hexing,china": (107.819770, 30.744850),
    "imperial,usa": (-115.569440, 32.847550),
    "shajing residential district,china": (113.811850, 22.731770),
    "blantyre,uk": (-4.094850, 55.796340),
    "white settlement,usa": (-97.458350, 32.759570),
    "xiulin,taiwan": (121.626300, 24.120190),
    "tangfang,china": (109.309180, 31.392920),
    "eloy,usa": (-111.554840, 32.755900),
    "beckley,usa": (-81.188160, 37.778170),
    "conglin,china": (106.970280, 29.030280),
    "broad ripple,usa": (-86.141650, 39.866710),
    "el segundo,usa": (-118.416470, 33.919180),
    "heysham,uk": (-2.893220, 54.043670),
    "holden,usa": (-71.863410, 42.351760),
    "taxkowruek,china": (81.306040, 43.892570),
    "avenel,usa": (-74.285150, 40.580380),
    "ting kau,china": (114.079070, 22.369560),
    "east setauket,usa": (-73.105940, 40.941490),
    "glen parva,uk": (-1.170620, 52.585270),
    "goodlettsville,usa": (-86.713330, 36.323110),
    "westbury,uk": (-2.187500, 51.260000),
    "chuk yuen north estate,china": (114.191970, 22.345920),
    "elmwood,usa": (-75.227960, 39.917890),
    "colchester,usa": (-73.147910, 44.543940),
    "terrell,usa": (-96.275260, 32.735960),
    "guisborough,uk": (-1.056060, 54.534780),
    "point breeze,usa": (-75.177960, 39.933450),
    "bedlington,uk": (-1.593190, 55.130610),
    "artesia,usa": (-118.083120, 33.865850),
    "south ogden,usa": (-111.971330, 41.191890),
    "huwei,china": (107.638530, 29.905650),
    "bage'awati,china": (77.540220, 38.489080),
    "frinton-on-sea,uk": (1.244240, 51.830610),
    "wang tau hom,china": (114.187320, 22.340100),
    "long'e,china": (109.212500, 25.807220),
    "dalain hob,china": (101.063890, 41.965280),
    "shenzhenwan,china": (113.939620, 22.487070),
    "la vista,usa": (-96.031130, 41.183890),
    "paya lebar,singapore": (103.890560, 1.353890),
    "tanque verde,usa": (-110.737310, 32.251740),
    "glenvar heights,usa": (-80.325610, 25.707600),
    "xiangshui,china": (108.193000, 30.655000),
    "hayling island,uk": (-0.968690, 50.783800),
    "pendleton,usa": (-118.788600, 45.672070),
    "dorchester,uk": (-2.433330, 50.716670),
    "parkside,usa": (-122.486300, 37.741970),
    "zhouxi,china": (107.916670, 26.483330),
    "linnei,taiwan": (120.618850, 23.761500),
    "sayville,usa": (-73.082060, 40.735930),
    "braunstone,uk": (-1.179040, 52.618350),
    "clarksdale,usa": (-90.570930, 34.200110),
    "pak tin estate,china": (114.166730, 22.337130),
    "northallerton,uk": (-1.432430, 54.339010),
    "fairview heights,usa": (-89.990380, 38.588940),
    "san carlos park,usa": (-81.801470, 26.467300),
    "dongjiang,china": (104.950660, 33.379230),
    "saint ives,uk": (-0.076560, 52.332510),
    "tin wan,china": (114.147260, 22.251130),
    "longfield,uk": (0.302120, 51.396900),
    "new milford,usa": (-74.019030, 40.935100),
    "zhuzilin,china": (114.015040, 22.538110),
    "saint andrews,uk": (-2.799020, 56.338710),
    "south ruislip,uk": (-0.408670, 51.555180),
    "ehen hudag,china": (101.668980, 39.210740),
    "north attleborough center,usa": (-71.324740, 41.972630),
    "country club hills,usa": (-87.720330, 41.568090),
    "wang tau hom estate,china": (114.186730, 22.340090),
    "baitu,china": (108.811400, 30.597220),
    "lemont,usa": (-88.001730, 41.673640),
    "sartell,usa": (-94.206940, 45.621630),
    "parkwood manor,usa": (-74.967950, 40.093440),
    "dyersburg,usa": (-89.385630, 36.034520),
    "defiance,usa": (-84.355780, 41.284490),
    "beltsville,usa": (-76.907470, 39.034830),
    "kwun tong,china": (114.221760, 22.311840),
    "fudong,china": (100.000140, 23.123190),
    "lixin,china": (105.080560, 34.912220),
    "centralia,usa": (-122.954300, 46.716210),
    "chalmette,usa": (-89.965370, 29.942960),
    "shorewood,usa": (-88.201730, 41.520030),
    "rochford,uk": (0.706730, 51.581980),
    "high blantyre,uk": (-4.100070, 55.784380),
    "zhaoxing,china": (109.176390, 25.910830),
    "plumstead,uk": (0.083330, 51.483330),
    "bluffton,usa": (-80.860390, 32.237150),
    "tifton,usa": (-83.508500, 31.450460),
    "cobham,uk": (-0.411300, 51.329970),
    "linhe,china": (106.368000, 38.321400),
    "nipomo,usa": (-120.476000, 35.042750),
    "north decatur,usa": (-84.306030, 33.790380),
    "brixham,uk": (-3.515850, 50.394310),
    "morganton,usa": (-81.684820, 35.745410),
    "kam ying,china": (114.236640, 22.422850),
    "denville,usa": (-74.477380, 40.892320),
    "barrington,usa": (-71.308660, 41.740660),
    "phoenixville,usa": (-75.514910, 40.130380),
    "mercedes,usa": (-97.913610, 26.149800),
    "center point,usa": (-86.683600, 33.645660),
    "lemay,usa": (-90.279280, 38.533390),
    "wolcott,usa": (-72.986770, 41.602320),
    "norcross,usa": (-84.213530, 33.941210),
    "troutdale,usa": (-122.387310, 45.539290),
    "oak grove,usa": (-122.640090, 45.416790),
    "sun tin wai,china": (114.186960, 22.370580),
    "north valley stream,usa": (-73.701800, 40.685100),
    "whickham,uk": (-1.676350, 54.945610),
    "easthampton,usa": (-72.668980, 42.266760),
    "bothell west,usa": (-122.240640, 47.805270),
    "changlong,china": (107.412960, 30.306180),
    "tahlequah,usa": (-94.969960, 35.915370),
    "yujing,taiwan": (120.461380, 23.124930),
    "hazel park,usa": (-83.104090, 42.462540),
    "muhe,china": (106.134880, 35.023370),
    "opelousas,usa": (-92.081510, 30.533530),
    "alton,uk": (-0.974690, 51.149310),
    "grafton,usa": (-71.685620, 42.207040),
    "sandalfoot cove,usa": (-80.186900, 26.338630),
    "brenham,usa": (-96.397740, 30.166880),
    "opa-locka,usa": (-80.250330, 25.902320),
    "beaver dam,usa": (-88.837330, 43.457770),
    "coalinga,usa": (-120.360150, 36.139680),
    "biggleswade,uk": (-0.264930, 52.086520),
    "xigaoshan,china": (105.388170, 33.734750),
    "jenison,usa": (-85.791980, 42.907250),
    "cohoes,usa": (-73.700120, 42.774240),
    "zhongling,china": (108.958410, 28.296750),
    "swansea,usa": (-71.189770, 41.748160),
    "donna,usa": (-98.051950, 26.170350),
    "kensington,uk": (-2.952830, 53.408610),
    "vienna,usa": (-77.265260, 38.901220),
    "pinewood,usa": (-80.216990, 25.868980),
    "jiangjia,china": (106.819170, 29.393060),
    "south norwood,uk": (-0.074690, 51.399440),
    "lansdale,usa": (-75.283790, 40.241500),
    "langru,china": (79.621390, 36.893330),
    "cowley,uk": (-1.206310, 51.732130),
    "harringay,uk": (-0.099560, 51.582400),
    "sevierville,usa": (-83.561840, 35.868150),
    "chickasha,usa": (-97.936430, 35.052570),
    "kingsland,usa": (-81.689830, 30.799960),
    "lower moyamensing,usa": (-75.164750, 39.919560),
    "norbury,uk": (-0.116670, 51.416670),
    "uvalde,usa": (-99.786170, 29.209680),
    "enfield lock,uk": (-0.027480, 51.670860),
    "hillcrest heights,usa": (-76.959420, 38.832890),
    "stuart,usa": (-80.252830, 27.197550),
    "ersheng,china": (106.770830, 29.465830),
    "fairhaven,usa": (-70.903650, 41.637600),
    "zachary,usa": (-91.156500, 30.648520),
    "lymington,uk": (-1.538280, 50.759160),
    "red wing,usa": (-92.533800, 44.562470),
    "sikeston,usa": (-89.587860, 36.876720),
    "bethpage,usa": (-73.482070, 40.744270),
    "erenhot,china": (111.976670, 43.647500),
    "sam shing,china": (113.978720, 22.381280),
    "kilwinning,uk": (-4.706660, 55.653330),
    "louth,uk": (-0.004380, 53.366640),
    "flowing wells,usa": (-111.009820, 32.293960),
    "'ewa beach,usa": (-158.007220, 21.315560),
    "kuoshi'airike,china": (77.279480, 38.622750),
    "bridgeview,usa": (-87.804220, 41.750030),
    "fairview park,usa": (-81.864300, 41.441440),
    "laguna woods,usa": (-117.725330, 33.610300),
    "wu'erqi,china": (79.559260, 37.320190),
    "mount clemens,usa": (-82.877980, 42.597260),
    "canon city,usa": (-105.242450, 38.440980),
    "saint michael,usa": (-93.664960, 45.209960),
    "south river,usa": (-74.385980, 40.446490),
    "fort thomas,usa": (-84.447160, 39.075060),
    "jutou,china": (105.033890, 34.820830),
    "johnstone,uk": (-4.516050, 55.829060),
    "sunset,usa": (-80.352280, 25.705940),
    "prospect heights,usa": (-87.937570, 42.095300),
    "griffith,usa": (-87.423650, 41.528370),
    "estelle,usa": (-90.106740, 29.845760),
    "fazakerley,uk": (-2.928630, 53.461400),
    "schofield barracks,usa": (-158.065150, 21.498370),
    "tianjia,china": (105.856650, 30.089630),
    "bon air,usa": (-77.557770, 37.524870),
    "carterton,uk": (-1.594350, 51.759050),
    "xiaojia,china": (106.470310, 30.288380),
    "ripon,uk": (-1.528260, 54.135790),
    "bonnyrigg,uk": (-3.105100, 55.873290),
    "oconomowoc,usa": (-88.499270, 43.111670),
    "hough,usa": (-81.636520, 41.512000),
    "vero beach,usa": (-80.397270, 27.638640),
    "xinhua,china": (98.482960, 24.752520),
    "zhushan,china": (108.274190, 30.732940),
    "bayshore gardens,usa": (-82.590380, 27.425320),
    "wong chuk hang,china": (114.170010, 22.239810),
    "streetsboro,usa": (-81.345940, 41.239220),
    "calhoun,usa": (-84.951050, 34.502590),
    "fishtown,usa": (-75.135450, 39.965110),
    "morton,usa": (-89.459260, 40.612820),
    "menomonie,usa": (-91.919340, 44.875520),
    "longxi,china": (109.635520, 31.302230),
    "hartley,uk": (0.303670, 51.386730),
    "truckee,usa": (-120.183250, 39.327960),
    "buckhall,usa": (-77.431100, 38.731780),
    "baychester,usa": (-73.836450, 40.869280),
    "jifeng,china": (105.657860, 33.655260),
    "puchi,china": (104.814180, 33.534660),
    "hopatcong hills,usa": (-74.670720, 40.943990),
    "waterville,usa": (-69.631710, 44.552010),
    "oroville,usa": (-121.557760, 39.513940),
    "roosevelt,usa": (-73.589020, 40.678710),
    "bikou,china": (105.241390, 32.745830),
    "tooting,uk": (-0.163940, 51.425240),
    "stepney,uk": (-0.042920, 51.517500),
    "yeung uk tsuen,china": (114.016670, 22.450000),
    "laconia,usa": (-71.470350, 43.527850),
    "bellmore,usa": (-73.527070, 40.668710),
    "nuuanu - punchbowl,usa": (-157.828520, 21.342150),
    "hibbing,usa": (-92.937690, 47.427150),
    "sudley,usa": (-77.497490, 38.792890),
    "kuliouou - kalani iki,usa": (-157.745000, 21.297130),
    "coos bay,usa": (-124.217890, 43.366500),
    "mujia,china": (99.634530, 22.991000),
    "banbridge,uk": (-6.283330, 54.350000),
    "braemar hill,china": (114.200340, 22.282820),
    "chepstow,uk": (-2.676830, 51.640870),
    "hope mills,usa": (-78.945310, 34.970440),
    "cimarron hills,usa": (-104.698860, 38.858610),
    "zhongba,china": (105.032860, 34.035110),
    "katy,usa": (-95.824400, 29.785790),
    "dazhuang,china": (105.336110, 34.958890),
    "clarksburg,usa": (-80.344530, 39.280650),
    "jollyville,usa": (-97.775010, 30.442700),
    "highland village,usa": (-97.046680, 33.091790),
    "ocean acres,usa": (-74.280980, 39.743450),
    "roehampton,uk": (-0.243930, 51.451650),
    "wolf trap,usa": (-77.286090, 38.939830),
    "maying,china": (104.846170, 33.596450),
    "midway,usa": (-87.005530, 30.406480),
    "penicuik,uk": (-3.226080, 55.831160),
    "hualin,china": (104.751980, 34.825590),
    "sulphur springs,usa": (-95.601070, 33.138450),
    "ryton,uk": (-2.350000, 52.616670),
    "maryland city,usa": (-76.817750, 39.092050),
    "upper norwood,uk": (-0.092700, 51.415050),
    "siloam springs,usa": (-94.540500, 36.188140),
    "yulong,china": (105.810440, 29.546150),
    "xiaochangshan,china": (122.723610, 39.235830),
    "hoi lai estate,china": (114.146670, 22.331820),
    "ham lake,usa": (-93.249950, 45.250240),
    "west columbia,usa": (-81.073980, 33.993490),
    "dyer,usa": (-87.521710, 41.494200),
    "rye,usa": (-73.683740, 40.980650),
    "fort hunt,usa": (-77.058030, 38.732890),
    "worcester park,uk": (-0.244450, 51.379920),
    "mount davis,china": (114.117770, 22.278620),
    "americus,usa": (-84.232690, 32.072390),
    "crawfordsville,usa": (-86.874450, 40.041150),
    "lake mary,usa": (-81.317840, 28.758880),
    "viewpark,uk": (-4.057300, 55.827370),
    "aldridge,uk": (-1.917150, 52.605490),
    "longsight,uk": (-2.201040, 53.458010),
    "republic,usa": (-93.480190, 37.120050),
    "albemarle,usa": (-80.200060, 35.350140),
    "basford,uk": (-1.183330, 52.966670),
    "el camino real,usa": (-117.776680, 33.696620),
    "country walk,usa": (-80.432280, 25.633990),
    "dianga,china": (103.213580, 34.063630),
    "riverdale,usa": (-84.413260, 33.572610),
    "limehouse,uk": (-0.032820, 51.514120),
    "dashan,china": (100.114890, 23.002380),
    "floral park,usa": (-73.704850, 40.723710),
    "seven sisters,uk": (-0.078950, 51.577690),
    "prosper,usa": (-96.801110, 33.236230),
    "walnut park,usa": (-118.225070, 33.968070),
    "kippax,uk": (-1.370990, 53.766870),
    "pecan grove,usa": (-95.731620, 29.626070),
    "overland,usa": (-90.362340, 38.701160),
    "grandville,usa": (-85.763090, 42.909750),
    "ealing common,uk": (-0.295460, 51.506860),
    "sunland park,usa": (-106.579990, 31.796500),
    "conisbrough,uk": (-1.232140, 53.481880),
    "north liberty,usa": (-91.597950, 41.749180),
    "lijia,china": (106.493120, 29.678780),
    "parole,usa": (-76.545000, 38.981000),
    "vincent,usa": (-118.116460, 34.500550),
    "southchase,usa": (-81.383400, 28.393060),
    "ukiah,usa": (-123.207780, 39.150170),
    "la marque,usa": (-94.971310, 29.368570),
    "north arlington,usa": (-74.133200, 40.788430),
    "la palma,usa": (-118.046730, 33.846400),
    "seagoville,usa": (-96.538320, 32.639580),
    "pearl river,usa": (-74.021810, 41.058990),
    "conyers,usa": (-84.017690, 33.667610),
    "myrtle grove,usa": (-87.307470, 30.421030),
    "aldine,usa": (-95.380210, 29.932450),
    "narragansett,usa": (-71.449500, 41.450100),
    "carmarthen,uk": (-4.305350, 51.855520),
    "kaukauna,usa": (-88.272050, 44.278040),
    "azhatebage,china": (77.466400, 38.658830),
    "port washington,usa": (-73.698190, 40.825660),
    "hoyland nether,uk": (-1.450000, 53.500000),
    "new port richey,usa": (-82.719270, 28.244180),
    "tadley,uk": (-1.128500, 51.350450),
    "adams morgan,usa": (-77.042200, 38.921500),
    "kidlington,uk": (-1.288600, 51.821660),
    "rutland,usa": (-72.972610, 43.610620),
    "asbury park,usa": (-74.012080, 40.220390),
    "pok hong,china": (114.195840, 22.375580),
    "lutherville-timonium,usa": (-76.610990, 39.439970),
    "uc irvine,usa": (-117.841640, 33.639670),
    "hybla valley,usa": (-77.083030, 38.747610),
    "lianhu,china": (108.435280, 29.698080),
    "longmeadow,usa": (-72.582870, 42.050100),
    "elkton,usa": (-75.833270, 39.606780),
    "royston,uk": (-0.024380, 52.048320),
    "strawberry mansion,usa": (-75.182680, 39.983450),
    "bebington,uk": (-3.016670, 53.350000),
    "grosse pointe woods,usa": (-82.906860, 42.443650),
    "new cross,uk": (-0.038370, 51.475340),
    "pinehurst,usa": (-79.469480, 35.195430),
    "groves,usa": (-93.917120, 29.948270),
    "west university place,usa": (-95.433830, 29.718010),
    "orient heights,usa": (-71.003660, 42.387600),
    "hunts cross,uk": (-2.865720, 53.355780),
    "swanscombe,uk": (0.310280, 51.447130),
    "wilkinsburg,usa": (-79.881990, 40.441740),
    "manassas park,usa": (-77.469710, 38.784000),
    "willow grove,usa": (-75.115730, 40.144000),
    "gatesville,usa": (-97.743910, 31.435160),
    "avon center,usa": (-82.019590, 41.459760),
    "la grange,usa": (-87.869230, 41.805030),
    "great bend,usa": (-98.764810, 38.364460),
    "shively,usa": (-85.822740, 38.200070),
    "highland springs,usa": (-77.327760, 37.545980),
    "baildon,uk": (-1.787850, 53.847110),
    "hueytown,usa": (-86.996660, 33.451220),
    "talladega,usa": (-86.105800, 33.435940),
    "mill creek east,usa": (-122.187660, 47.836020),
    "koolauloa,usa": (-157.926500, 21.605790),
    "middleburg heights,usa": (-81.812910, 41.361440),
    "pacific grove,usa": (-121.916620, 36.617740),
    "porthcawl,uk": (-3.703620, 51.479030),
    "tieshan,china": (105.501000, 29.689470),
    "mitchell,usa": (-98.029800, 43.709430),
    "humble,usa": (-95.262160, 29.998830),
    "ponders end,uk": (-0.046520, 51.644500),
    "greenwood village,usa": (-104.950810, 39.617210),
    "hale,uk": (-0.789080, 51.229460),
    "fu cheong estate,china": (114.153990, 22.328910),
    "to kwa wan,china": (114.190520, 22.316930),
    "bryn mawr-skyway,usa": (-122.240920, 47.494300),
    "keynsham,uk": (-2.497800, 51.413870),
    "elland,uk": (-1.838780, 53.685100),
    "lee on,china": (114.241330, 22.426350),
    "perry vale,uk": (-0.044420, 51.436390),
    "bradley,usa": (-87.861150, 41.141980),
    "belle vale,uk": (-2.860220, 53.392130),
    "yumen,china": (97.045410, 40.291450),
    "mckinley park,usa": (-87.673660, 41.831700),
    "old swan,uk": (-2.908890, 53.413920),
    "elkridge,usa": (-76.713580, 39.212610),
    "north myrtle beach,usa": (-78.680020, 33.816010),
    "williamstown,usa": (-74.995170, 39.686230),
    "saltash,uk": (-4.225140, 50.409590),
    "earlsfield,uk": (-0.185400, 51.443900),
    "baituo,china": (106.001670, 34.851110),
    "west ham,uk": (0.016670, 51.533330),
    "otsego,usa": (-93.591350, 45.274130),
    "boulder city,usa": (-114.832490, 35.978590),
    "fillmore,usa": (-118.918150, 34.399160),
    "lake wales,usa": (-81.585910, 27.901410),
    "allerton,uk": (-2.894000, 53.366970),
    "alum rock,usa": (-121.827180, 37.366050),
    "erskine,uk": (-4.450280, 55.900500),
    "zengfu,china": (106.985770, 29.510660),
    "gaogu,china": (108.065790, 29.395570),
    "wombwell,uk": (-1.396980, 53.521890),
    "fengling,china": (109.554740, 31.319400),
    "east riverdale,usa": (-76.911000, 38.958000),
    "laurinburg,usa": (-79.462820, 34.774050),
    "furzedown,uk": (-0.146560, 51.424560),
    "hernando,usa": (-89.993700, 34.823990),
    "hurricane,usa": (-113.289950, 37.175260),
    "lithia springs,usa": (-84.660490, 33.794000),
    "butterfly,china": (113.962510, 22.375910),
    "south hayling,uk": (-0.976970, 50.787730),
    "fazhanhe,china": (100.173100, 22.334240),
    "prince edward,china": (114.179380, 22.323600),
    "farmingville,usa": (-73.029550, 40.831210),
    "mastic,usa": (-72.840940, 40.802040),
    "setauket-east setauket,usa": (-73.101790, 40.930640),
    "blackwood,uk": (-3.207500, 51.667780),
    "martha lake,usa": (-122.239300, 47.850930),
    "indianola,usa": (-93.557440, 41.358050),
    "daxie,china": (108.110270, 30.072920),
    "mid levels,china": (114.149580, 22.283990),
    "fortress hill,china": (114.194170, 22.288580),
    "perry,usa": (-83.731570, 32.458210),
    "atwater village,usa": (-118.256460, 34.116400),
    "zhen'an,china": (108.316750, 31.152260),
    "wangjia,china": (106.698120, 29.767160),
    "jasper,usa": (-86.931110, 38.391440),
    "winder,usa": (-83.720170, 33.992610),
    "clive,usa": (-93.724110, 41.603040),
    "clemson,usa": (-82.837370, 34.683440),
    "tung tau estate,china": (114.192770, 22.332120),
    "tavares,usa": (-81.725630, 28.804160),
    "awuliya,china": (81.693170, 43.930330),
    "terrace heights,usa": (-73.769300, 40.721490),
    "emerson hill,usa": (-74.095980, 40.608720),
    "avocado heights,usa": (-117.991180, 34.036120),
    "city one,china": (114.202750, 22.386790),
    "eden,usa": (-79.766700, 36.488470),
    "bay village,usa": (-81.922080, 41.484770),
    "lake butler,usa": (-81.540910, 28.501670),
    "makakilo city,usa": (-158.085830, 21.346940),
    "donghui,china": (99.800100, 22.440520),
    "westbury,usa": (-73.587630, 40.755660),
    "bostonia,usa": (-116.936420, 32.807550),
    "llandudno,uk": (-3.831480, 53.324980),
    "iona,usa": (-81.963980, 26.520360),
    "broxburn,uk": (-3.471330, 55.934150),
    "dickson,usa": (-87.387790, 36.077000),
    "neston,uk": (-2.200560, 51.412220),
    "cullman,usa": (-86.843610, 34.174820),
    "roanoke rapids,usa": (-77.654150, 36.461540),
    "storrs,usa": (-72.249520, 41.808430),
    "loyang,singapore": (103.971670, 1.378610),
    "kampong loyang,singapore": (103.959440, 1.377780),
    "the dalles,usa": (-121.178680, 45.594560),
    "houshan,china": (108.028660, 30.825890),
    "los lunas,usa": (-106.733360, 34.806170),
    "qinglong,china": (109.256410, 30.779770),
    "manor park,uk": (0.048670, 51.549320),
    "sunland,usa": (-118.302300, 34.266950),
    "millbrook,usa": (-86.361920, 32.479860),
    "wailuku,usa": (-156.506040, 20.891330),
    "warren township,usa": (-74.518030, 40.608220),
    "houhai,china": (113.925460, 22.512260),
    "seaford,usa": (-73.488180, 40.665930),
    "washougal,usa": (-122.353420, 45.582620),
    "changba,china": (107.474960, 29.334660),
    "guochuan,china": (105.810000, 34.683800),
    "graniteville,usa": (-74.148480, 40.624830),
    "stallings,usa": (-80.686180, 35.090700),
    "river falls,usa": (-92.623810, 44.861360),
    "berkley,usa": (-83.183540, 42.503090),
    "hazel grove,uk": (-2.116670, 53.383330),
    "tanjia,china": (108.498610, 31.455740),
    "darton,uk": (-1.526760, 53.587050),
    "damascus,usa": (-77.203870, 39.288440),
    "dure,china": (88.533890, 46.511880),
    "kennedy street,usa": (-77.017990, 38.956300),
    "orpington,uk": (0.097850, 51.374570),
    "roxbury crossing,usa": (-71.091160, 42.330650),
    "susanville,usa": (-120.653010, 40.416280),
    "pataskala,usa": (-82.674330, 39.995620),
    "wanmu,china": (108.500240, 28.632750),
    "traverse city,usa": (-85.620630, 44.763060),
    "south yuba city,usa": (-121.639130, 39.116560),
    "yongxi,china": (105.979410, 29.738530),
    "city garden,china": (114.192590, 22.289970),
    "merrifield,usa": (-77.226930, 38.874280),
    "ledyard,usa": (-72.014240, 41.439820),
    "saffron walden,uk": (0.242340, 52.023370),
    "shihui,china": (108.610170, 29.571770),
    "haslingden,uk": (-2.323820, 53.703260),
    "port glasgow,uk": (-4.689500, 55.934640),
    "oymak,china": (86.989550, 47.878090),
    "fords,usa": (-74.315980, 40.529270),
    "new territory,usa": (-95.680780, 29.594120),
    "kapolei,usa": (-158.058200, 21.335550),
    "clearlake,usa": (-122.626370, 38.958230),
    "penrith,uk": (-2.757570, 54.665790),
    "mckinleyville,usa": (-124.100620, 40.946520),
    "west ealing,uk": (-0.322900, 51.513550),
    "highview,usa": (-85.624130, 38.142850),
    "xiping,china": (105.115000, 34.605700),
    "palmers green,uk": (-0.110120, 51.617940),
    "totteridge,uk": (-0.200000, 51.633330),
    "belvedere park,usa": (-84.267420, 33.754830),
    "ripon,usa": (-121.124380, 37.741590),
    "depew,usa": (-78.692250, 42.903950),
    "seven oaks,usa": (-81.146480, 34.048760),
    "wilmington island,usa": (-80.973720, 32.003550),
    "parlier,usa": (-119.527070, 36.611620),
    "gates-north gates,usa": (-77.700660, 43.165470),
    "east rancho dominguez,usa": (-118.195350, 33.898070),
    "southwest waterfront,usa": (-77.017580, 38.879340),
    "sinfin,uk": (-1.486810, 52.881570),
    "natchez,usa": (-91.403290, 31.560170),
    "bredbury,uk": (-2.116670, 53.416670),
    "cloverly,usa": (-76.997750, 39.108160),
    "tiong bahru estate,singapore": (103.832780, 1.283330),
    "lamont,usa": (-118.914270, 35.259680),
    "east brainerd,usa": (-85.150230, 34.995910),
    "shadwell,uk": (-0.056630, 51.511350),
    "vandalia,usa": (-84.198830, 39.890610),
    "rio linda,usa": (-121.448570, 38.691010),
    "east longmeadow,usa": (-72.512590, 42.064540),
    "west park,usa": (-80.198940, 25.984540),
    "greeneville,usa": (-82.830990, 36.163160),
    "adelphi,usa": (-76.971920, 39.003170),
    "mexborough,uk": (-1.292430, 53.493890),
    "front royal,usa": (-78.194440, 38.918170),
    "newport pagnell,uk": (-0.722180, 52.087310),
    "tottenham hale,uk": (-0.059620, 51.593660),
    "spanish springs,usa": (-119.707410, 39.649080),
    "yiu tung estate,china": (114.222990, 22.278490),
    "fort leonard wood,usa": (-92.157170, 37.705730),
    "duxbury,usa": (-70.672260, 42.041770),
    "capitol hill,usa": (-77.000250, 38.889000),
    "three lakes,usa": (-80.398390, 25.642050),
    "auburndale,usa": (-81.788690, 28.065300),
    "gloversville,usa": (-74.343750, 43.052850),
    "hereford,usa": (-102.399320, 34.815210),
    "larkhall,uk": (-3.966670, 55.733330),
    "eggertsville,usa": (-78.803920, 42.963390),
    "dumas,usa": (-101.973240, 35.865590),
}

def _norm_place(s: str) -> str:
    return (s or "").strip().lower()

def _lookup_city_lonlat(city: str, country: str):
    key = f"{_norm_place(city)},{_norm_place(country)}"
    return _CITY_LONLAT.get(key)

def _solar_to_str(solar) -> str:
    # Best-effort string for Solar object without assuming exact API version.
    for meth in ("toYmdHms", "toFullString", "toString", "toYmd"):
        try:
            v = getattr(solar, meth)()
            if isinstance(v, str):
                return v
        except Exception:
            pass
    # Fallback: try common getters
    try:
        y = solar.getYear(); m = solar.getMonth(); d = solar.getDay()
        hh = solar.getHour(); mm = solar.getMinute(); ss = solar.getSecond()
        return f"{y:04d}-{m:02d}-{d:02d} {hh:02d}:{mm:02d}:{ss:02d}"
    except Exception:
        return str(solar)


def _resolve_lon_lat(city, country, lon, lat, allow_geocode: bool = False):
    # Return (lon, lat, source_str).
    # Priority:
    #   1) explicit --lon/--lat
    #   2) built-in city table (offline)
    #   3) optional online geocoding (only if allow_geocode=True)
    if lon is not None:
        return float(lon), (float(lat) if lat is not None else None), 'manual'
    if not city or not country:
        return None, None, 'none'

    hit = _lookup_city_lonlat(city, country)
    if hit is not None:
        lon_hit, lat_hit = hit
        return float(lon_hit), float(lat_hit), 'builtin'

    if not allow_geocode:
        return None, None, 'no_geocode'

    if Nominatim is None:
        return None, None, 'geopy_not_installed'

    try:
        # Nominatim can return 403 on some networks / without proper headers.
        geolocator = Nominatim(user_agent='bazi_true_solar/1.0 (offline-first)')
        loc = geolocator.geocode(f'{city}, {country}', timeout=10)
        if loc is None:
            return None, None, 'geocode_failed'
        return float(loc.longitude), float(loc.latitude), 'geocoded'
    except (GeocoderInsufficientPrivileges, GeocoderServiceError, Exception):
        return None, None, 'geocode_error'

def _resolve_timezone(tz_name, country, city):
    # Resolve a pytz timezone. If tz_name is provided, use it. If missing and country is China, default to Asia/Shanghai.
    if tz_name:
        return pytz.timezone(tz_name)
    if country and country.strip().lower() in ('china', 'prc', "people's republic of china", '中华人民共和国', '中国'):
        return pytz.timezone('Asia/Shanghai')
    return None

def to_true_solar_datetime(local_dt: datetime.datetime, lon_deg: float, tz, use_dst: bool = False) -> datetime.datetime:
    # Convert localized civil time to 真太阳时 (apparent solar time approximation):
    # TrueSolar = StandardTime + 4*(lon - LSTM) + EoT, in minutes.
    if local_dt.tzinfo is None:
        local_dt = tz.localize(local_dt)
    else:
        local_dt = local_dt.astimezone(tz)

    offset = local_dt.utcoffset()
    offset_hours = (offset.total_seconds() / 3600.0) if offset else 0.0
    if (not use_dst) and bool(local_dt.dst()):
        offset_hours -= 1.0  # remove DST

    lstm = 15.0 * offset_hours  # Local Standard Time Meridian, degrees
    eot = _equation_of_time_minutes(local_dt.replace(tzinfo=None))
    tc = 4.0 * (lon_deg - lstm) + eot
    return (local_dt.replace(tzinfo=None) + datetime.timedelta(minutes=tc))

options = parser.parse_args()

Gans = collections.namedtuple("Gans", "year month day time")
Zhis = collections.namedtuple("Zhis", "year month day time")

print("-"*120)

if options.b:
    import sxtwl
    gans = Gans(year=options.year[0], month=options.month[0], 
                day=options.day[0],  time=options.time[0])
    zhis = Gans(year=options.year[1], month=options.month[1], 
                day=options.day[1],  time=options.time[1])
    jds = sxtwl.siZhu2Year(getGZ(options.year), getGZ(options.month), getGZ(options.day), getGZ(options.time), options.start, int(options.end));
    for jd in jds:
        t = sxtwl.JD2DD(jd )
        print("可能出生时间: python bazi.py -g %d %d %d %d :%d:%d"%(t.Y, t.M, t.D, t.h, t.m, round(t.s)))   
    
else:

    # Parse input time (civil clock time)
    hour, minute, second = parse_time_arg(options.time)

    # Build an initial Solar from the user's input time (civil clock time)
    if options.g:
        solar = Solar.fromYmdHms(int(options.year), int(options.month), int(options.day), hour, minute, second)
    else:
        month_ = int(options.month) * -1 if options.r else int(options.month)
        lunar_tmp = Lunar.fromYmdHms(int(options.year), month_, int(options.day), hour, minute, second)
        solar = lunar_tmp.getSolar()

    solar_civil = solar  # user's civil clock time (before 真太阳时 correction)

# Convert to 真太阳时 (apparent solar time) if location info is provided
    true_solar_dt = None
    if options.city or options.country or (options.lon is not None):
        tz = _resolve_timezone(options.tz, options.country, options.city)
        if tz is None:
            raise SystemExit('When using --city/--country for 真太阳时 conversion, please also provide --tz (IANA timezone, e.g., Asia/Shanghai). '
                             'China defaults to Asia/Shanghai if --tz is omitted.')
        lon_deg, lat_deg, src = _resolve_lon_lat(options.city, options.country, options.lon, options.lat, allow_geocode=options.geocode)
        if lon_deg is None:
            raise SystemExit('Could not determine longitude for 真太阳时 conversion. Provide --lon (and optionally --lat), e.g., Qingdao China: --lon 120.3826 --lat 36.0671. '
                             'or ensure --city/--country can be geocoded.')
        local_dt = datetime.datetime(int(options.year), int(options.month), int(options.day), hour, minute, second)
        true_solar_dt = to_true_solar_datetime(local_dt, lon_deg=lon_deg, tz=tz, use_dst=options.use_dst)
        solar = Solar.fromYmdHms(true_solar_dt.year, true_solar_dt.month, true_solar_dt.day,
                                 true_solar_dt.hour, true_solar_dt.minute, true_solar_dt.second)

    solar_true = solar  # after 真太阳时 correction (or same as civil)

    # Show time inputs so the output visibly reflects your time and location
    print(f"输入钟表时间: {_solar_to_str(solar_civil)}")
    if true_solar_dt is not None:
        print(f"真太阳时: {true_solar_dt.strftime('%Y-%m-%d %H:%M:%S')} (lon={lon_deg:.4f}, src={src}, tz={tz.zone})")
    else:
        print("真太阳时: (未转换; 未提供地点/经度)")
    print('-'*120)

    lunar = solar_true.getLunar()
    day = lunar
    ba = lunar.getEightChar() 
    gans = Gans(year=ba.getYearGan(), month=ba.getMonthGan(), day=ba.getDayGan(), time=ba.getTimeGan())
    zhis = Zhis(year=ba.getYearZhi(), month=ba.getMonthZhi(), day=ba.getDayZhi(), time=ba.getTimeZhi())


me = gans.day
month = zhis.month
alls = list(gans) + list(zhis)
zhus = [item for item in zip(gans, zhis)]

gan_shens = []
for seq, item in enumerate(gans):    
    if seq == 2:
        gan_shens.append('--')
    else:
        gan_shens.append(ten_deities[me][item])
#print(gan_shens)

zhi_shens = [] # 地支的主气神
for item in zhis:
    d = zhi5[item]
    zhi_shens.append(ten_deities[me][max(d, key=d.get)])
#print(zhi_shens)
shens = gan_shens + zhi_shens

zhi_shens2 = [] # 地支的所有神，包含余气和尾气, 混合在一起
zhi_shen3 = [] # 地支所有神，字符串格式
for item in zhis:
    d = zhi5[item]
    tmp = ''
    for item2 in d:
        zhi_shens2.append(ten_deities[me][item2])
        tmp += ten_deities[me][item2]
    zhi_shen3.append(tmp)
shens2 = gan_shens + zhi_shens2
    


# 计算五行分数 http://www.131.com.tw/word/b3_2_14.htm

scores = {"金":0, "木":0, "水":0, "火":0, "土":0}
gan_scores = {"甲":0, "乙":0, "丙":0, "丁":0, "戊":0, "己":0, "庚":0, "辛":0,
              "壬":0, "癸":0}   

for item in gans:  
    scores[gan5[item]] += 5
    gan_scores[item] += 5


for item in list(zhis) + [zhis.month]:  
    for gan in zhi5[item]:
        scores[gan5[gan]] += zhi5[item][gan]
        gan_scores[gan] += zhi5[item][gan]


# 计算八字强弱
# 子平真诠的计算
weak = True
me_status = []
for item in zhis:
    me_status.append(ten_deities[me][item])
    if ten_deities[me][item] in ('长', '帝', '建'):
        weak = False
        

if weak:
    if shens.count('比') + me_status.count('库') >2:
        weak = False

# 计算大运
seq = Gan.index(gans.year)
if options.n:
    if seq % 2 == 0:
        direction = -1
    else:
        direction = 1
else:
    if seq % 2 == 0:
        direction = 1
    else:
        direction = -1

dayuns = []
gan_seq = Gan.index(gans.month)
zhi_seq = Zhi.index(zhis.month)
for i in range(12):
    gan_seq += direction
    zhi_seq += direction
    dayuns.append(Gan[gan_seq%10] + Zhi[zhi_seq%12])

# 网上的计算
me_attrs_ = ten_deities[me].inverse
strong = gan_scores[me_attrs_['比']] + gan_scores[me_attrs_['劫']] \
    + gan_scores[me_attrs_['枭']] + gan_scores[me_attrs_['印']]


if not options.b:
    #print("direction",direction)
    sex = '女' if options.n else '男'
    print("{}命".format(sex), end=' ')
    print("	公历:", end=' ')
    print("{}年{}月{}日".format(solar.getYear(), solar.getMonth(), solar.getDay()), end=' ')
    print("  时间(输入): {:02d}:{:02d}:{:02d}".format(hour, minute, second), end=' ')
    if true_solar_dt is not None:
        print("  真太阳时: {:02d}:{:02d}:{:02d}".format(true_solar_dt.hour, true_solar_dt.minute, true_solar_dt.second), end=' ')

    yun = ba.getYun(not options.n)   
    print("  农历:", end=' ')
    print("{}年{}月{}日 穿=害 上运时间：{} 命宫:{} 胎元:{} 身宫:{}\n".format(lunar.getYear(), lunar.getMonth(), 
        lunar.getDay(), yun.getStartSolar().toFullString().split()[0], ba.getMingGong(), ba.getTaiYuan(), ba.getShenGong()), end=' ')
    print("\t", siling[zhis.month], lunar.getPrevJieQi(True), lunar.getPrevJieQi(True).getSolar().toYmdHms(),lunar.getNextJieQi(True), 
        lunar.getNextJieQi(True).getSolar().toYmdHms())
    

print("-"*120)

#print(zhi_3hes, "生：寅申巳亥 败：子午卯酉　库：辰戌丑未")
#print("地支六合:", zhi_6hes)
out = ' '
for item in list(xiuqius[zhis.month].items()):
    out = out + "{}:{} ".format(item[0], item[1])

for item in list(scores.items()):
    out = out + " {}{} ".format(item[0], item[1])

out = "{} {}:{} {} {} {}".format(out, "强弱", strong, "中值29", "强根:", '无' if weak else '有')



print('\033[1;36;40m' + ' '.join(list(gans)), ' '*5, ' '.join(list(gan_shens)) + '\033[0m',' '*3, out)

temps_scores = temps[gans.year] + temps[gans.month] + temps[me] + temps[gans.time] + temps[zhis.year] + temps[zhis.month]*2 + temps[zhis.day] + temps[zhis.time]
out = str(temps_scores) + " 湿度[-6,6] 拱：" + str(get_gong(zhis))
print('\033[1;36;40m' + ' '.join(list(zhis)), ' '*5, ' '.join(list(zhi_shens)) + '\033[0m', ' '*3, out, "解读:钉ding或v信pythontesting: 四柱：" + ' '.join([''.join(item) for item in zip(gans, zhis)]),)
print("-"*120)
print("{1:{0}^15s}{2:{0}^15s}{3:{0}^15s}{4:{0}^15s}".format(chr(12288), '【年】{}:{}{}{}'.format(temps[gans.year],temps[zhis.year],ten_deities[gans.year].inverse['建'], gan_zhi_he(zhus[0])), 
    '【月】{}:{}{}{}'.format(temps[gans.month],temps[zhis.month], ten_deities[gans.month].inverse['建'], gan_zhi_he(zhus[1])),
    '【日】{}:{}{}'.format(temps[me], temps[zhis.day], gan_zhi_he(zhus[2])), 
    '【时】{}:{}{}{}'.format(temps[gans.time], temps[zhis.time], ten_deities[gans.time].inverse['建'], gan_zhi_he(zhus[3]))))
print("-"*120)


print("\033[1;36;40m{1:{0}<15s}{2:{0}<15s}{3:{0}<15s}{4:{0}<15s}\033[0m".format(
    chr(12288),
    '{}{}{}【{}】{}'.format(
        gans.year, yinyang(gans.year), gan5[gans.year], ten_deities[me][gans.year], check_gan(gans.year, gans)),
    '{}{}{}【{}】{}'.format(
        gans.month, yinyang(gans.month), gan5[gans.month], ten_deities[me][gans.month], check_gan(gans.month, gans)),
    '{}{}{}{}'.format(me, yinyang(me),gan5[me], check_gan(me, gans)),
    '{}{}{}【{}】{}'.format(gans.time, yinyang(gans.time), gan5[gans.time], ten_deities[me][gans.time], check_gan(gans.time, gans)),
))

print("\033[1;36;40m{1:{0}<15s}{2:{0}<15s}{3:{0}<15s}{4:{0}<15s}\033[0m".format(
    chr(12288),
    "{}{}{}{}【{}】{}{}".format(
        zhis.year, yinyang(zhis.year), ten_deities[gans.year][zhis.year], ten_deities[gans.month][zhis.year],ten_deities[me][zhis.year], ten_deities[gans.time][zhis.year], get_empty(zhus[2],zhis.year)),
    "{}{}{}{}【{}】{}{}".format(
        zhis.month, yinyang(zhis.month), ten_deities[gans.year][zhis.month], ten_deities[gans.month][zhis.month],ten_deities[me][zhis.month], ten_deities[gans.time][zhis.month], get_empty(zhus[2],zhis.month)),
    "{}{}{}{}【{}】{}".format(zhis.day, yinyang(zhis.day),  ten_deities[gans.year][zhis.day], ten_deities[gans.month][zhis.day], ten_deities[me][zhis.day], ten_deities[gans.time][zhis.day],),   
    "{}{}{}{}【{}】{}{}".format(
        zhis.time, yinyang(zhis.time), ten_deities[gans.year][zhis.time], ten_deities[gans.month][zhis.time],ten_deities[me][zhis.time], ten_deities[gans.time][zhis.time], get_empty(zhus[2],zhis.time)),
))

statuses = [ten_deities[me][item] for item in zhis]


for seq, item in enumerate(zhis):
    out = ''
    multi = 2 if item == zhis.month and seq == 1 else 1

    for gan in zhi5[item]:
        out = out + "{}{}{}　".format(gan, gan5[gan], ten_deities[me][gan])
    print("\033[1;36;40m{1:{0}<15s}\033[0m".format(chr(12288), out.rstrip('　')), end='')

print()
# 输出地支关系
for seq, item in enumerate(zhis):

    output = ''
    others = zhis[:seq] + zhis[seq+1:] 
    for type_ in zhi_atts[item]:
        flag = False
        if type_ in ('害',"破","会",'刑'):
            continue
        for zhi in zhi_atts[item][type_]:
            if zhi in others:
                if not flag:
                    output = output + "　" + type_ + "：" if type_ not in ('冲','暗') else output + "　" + type_
                    flag = True
                if type_ not in ('冲','暗'):
                    output += zhi
        output = output.lstrip('　')
    print("\033[1;36;40m{1:{0}<15s}\033[0m".format(chr(12288), output), end='')

print()

# 输出地支minor关系
for seq, item in enumerate(zhis):

    output = ''
    others = zhis[:seq] + zhis[seq+1:] 
    for type_ in zhi_atts[item]:
        flag = False
        if type_ not in ('害',"破","会",'刑'):
            continue
        for zhi in zhi_atts[item][type_]:
            if zhi in others:
                if not flag:
                    output = output + "　" + type_ + "："
                    flag = True
                output += zhi
    output = output.lstrip('　')
    print("\033[1;36;40m{1:{0}<15s}\033[0m".format(chr(12288), output), end='')

print()

# 输出根
for  item in gans:
    output = output.lstrip('　')
    print("\033[1;36;40m{1:{0}<15s}\033[0m".format(chr(12288), get_gen(item, zhis)), end='')

print()

for seq, item in enumerate(zhus):

    # 检查空亡 
    result = "{}－{}".format(nayins[item], '亡') if zhis[seq] == wangs[zhis[0]] else nayins[item]
    
    # 天干与地支关系
    result = relations[(gan5[gans[seq]], zhi_wuhangs[zhis[seq]])] + result
        
    # 检查劫杀 
    result = "{}－{}".format(result, '劫杀') if zhis[seq] == jieshas[zhis[0]] else result
    # 检查元辰
    result = "{}－{}".format(result, '元辰') if zhis[seq] == Zhi[(Zhi.index(zhis[0]) + direction*-1*5)%12] else result    
    print("{1:{0}<15s} ".format(chr(12288), result), end='')

print()

all_ges = []

# 神煞计算

strs = ['','','','',]

all_shens = set()
all_shens_list = []

for item in year_shens:
    for i in (1,2,3):
        if zhis[i] in year_shens[item][zhis.year]:    
            strs[i] = item if not strs[i] else strs[i] + chr(12288) + item
            all_shens.add(item)
            all_shens_list.append(item)
            
for item in month_shens:
    for i in range(4):
        if gans[i] in month_shens[item][zhis.month] or zhis[i] in month_shens[item][zhis.month]:     
            strs[i] = item if not strs[i] else strs[i] + chr(12288) + item
            if i == 2 and gans[i] in month_shens[item][zhis.month]:
                strs[i] = strs[i] + "●"
            all_shens.add(item)
            all_shens_list.append(item)
            
for item in day_shens:
    for i in (0,1,3):
        if zhis[i] in day_shens[item][zhis.day]:     
            strs[i] = item if not strs[i] else strs[i] + chr(12288) + item    
            all_shens.add(item)
            all_shens_list.append(item)
            
for item in g_shens:
    for i in range(4):
        if zhis[i] in g_shens[item][me]:    
            strs[i] = item if not strs[i] else strs[i] + chr(12288) + item
            all_shens.add(item)
            all_shens_list.append(item)
            
# print(all_shens_list)
#print(strs)           
for seq in range(2):
    print("{1:{0}<15s} ".format(chr(12288), strs[seq]), end='')
for seq in range(2,4):
    print("{1:{0}<14s} ".format(chr(12288), strs[seq]), end='')
    


# 计算六合:相邻的才算合

zhi_6he = [False, False, False, False]

for i in range(3):
    if zhi_atts[zhis[i]]['六'] == zhis[i+1]:
        zhi_6he[i] = zhi_6he[i+1] = True
        
# 计算六冲:相邻的才算合

zhi_6chong = [False, False, False, False]

for i in range(3):
    if zhi_atts[zhis[i]]['冲'] == zhis[i+1]:
        zhi_6chong[i] = zhi_6chong[i+1] = True
        
# 计算干合:相邻的才算合

gan_he = [False, False, False, False]
for i in range(3):
    if (gans[i],gans[i+1]) in set(gan_hes) or (gans[i+1],gans[i]) in set(gan_hes):
        gan_he[i] = gan_he[i+1] = True
        
# 计算刑:相邻的才算

zhi_xing = [False, False, False, False]

for i in range(3):
    if zhi_atts[zhis[i]]['刑'] == zhis[i+1] or zhi_atts[zhis[i+1]]['刑'] == zhis[i]:
        zhi_xing[i] = zhi_xing[i+1] = True
print()
print("-"*120)       


if options.b:
    print("大运：", end=' ')
    for item in dayuns:
        print(item, end=' ')
    print()

else:
    for dayun in yun.getDaYun()[1:]:
        gan_ = dayun.getGanZhi()[0]
        zhi_ = dayun.getGanZhi()[1]
        fu = '*' if (gan_, zhi_) in zhus else " "
        zhi5_ = ''
        for gan in zhi5[zhi_]:
            zhi5_ = zhi5_ + "{}{}　".format(gan, ten_deities[me][gan]) 
        
        zhi__ = set() # 大运地支关系
        
        for item in zhis:
        
            for type_ in zhi_atts[zhi_]:
                if item in zhi_atts[zhi_][type_]:
                    zhi__.add(type_ + ":" + item)
        zhi__ = '  '.join(zhi__)
        
        empty = chr(12288)
        if zhi_ in empties[zhus[2]]:
            empty = '空'        
        
        jia = ""
        if gan_ in gans:
            for i in range(4):
                if gan_ == gans[i]:
                    if abs(Zhi.index(zhi_) - Zhi.index(zhis[i])) == 2:
                        jia = jia + "  --夹：" +  Zhi[( Zhi.index(zhi_) + Zhi.index(zhis[i]) )//2]
                    if abs( Zhi.index(zhi_) - Zhi.index(zhis[i]) ) == 10:
                        jia = jia + "  --夹：" +  Zhi[(Zhi.index(zhi_) + Zhi.index(zhis[i]))%12]
                
        out = "{1:<4d}{2:<5s}{3} {15} {14} {13}  {4}:{5}{8}{6:{0}<6s}{12}{7}{8}{9} - {10:{0}<10s} {11}".format(
            chr(12288), dayun.getStartAge(), '', dayun.getGanZhi(),ten_deities[me][gan_], gan_,check_gan(gan_, gans), 
            zhi_, yinyang(zhi_), ten_deities[me][zhi_], zhi5_, zhi__,empty, fu, nayins[(gan_, zhi_)], ten_deities[me][zhi_]) 
        gan_index = Gan.index(gan_)
        zhi_index = Zhi.index(zhi_)
        out = out + jia + get_shens(gans, zhis, gan_, zhi_)
        
        print(out)
        zhis2 = list(zhis) + [zhi_]
        gans2 = list(gans) + [gan_]

print("-"*120)

me_lu = ten_deities[me].inverse['建']

me_jue = ten_deities[me].inverse['绝']
me_tai = ten_deities[me].inverse['胎']
me_di = ten_deities[me].inverse['帝']
shang = ten_deities[me].inverse['伤']
shang_lu = ten_deities[shang].inverse['建']
shang_di = ten_deities[shang].inverse['帝']
yin = ten_deities[me].inverse['印']
yin_lu = ten_deities[yin].inverse['建']
xiao = ten_deities[me].inverse['枭']
xiao_lu = ten_deities[xiao].inverse['建']
cai = ten_deities[me].inverse['财']
cai_lu = ten_deities[cai].inverse['建']
cai_di = ten_deities[cai].inverse['帝']
piancai = ten_deities[me].inverse['才']
piancai_lu = ten_deities[piancai].inverse['建']
piancai_di = ten_deities[piancai].inverse['帝']
guan = ten_deities[me].inverse['官']
guan_lu = ten_deities[guan].inverse['建']
guan_di = ten_deities[guan].inverse['帝']
sha = ten_deities[me].inverse['杀']
sha_lu = ten_deities[sha].inverse['建']
sha_di = ten_deities[sha].inverse['帝']

jie = ten_deities[me].inverse['劫']
shi = ten_deities[me].inverse['食']
shi_lu = ten_deities[shi].inverse['建']
shi_di = ten_deities[shi].inverse['帝']

me_ku = ten_deities[me]['库'][0]
cai_ku = ten_deities[cai]['库'][0]
guan_ku = ten_deities[guan]['库'][0]
yin_ku = ten_deities[yin]['库'][0]
shi_ku = ten_deities[shi]['库'][0]



print("调候：", tiaohous['{}{}'.format(me, zhis[1])], "\t##金不换大运：", jinbuhuan['{}{}'.format(me, zhis[1])])
print("金不换大运：说明：", jins['{}'.format(me)])
print("格局选用：", ges[ten_deities[me]['本']][zhis[1]])
if len(set('寅申巳亥')&set(zhis)) == 0:
    print("缺四生：一生不敢作为")
if len(set('子午卯酉')&set(zhis)) == 0:
    print("缺四柱地支缺四正，一生避是非")
if len(set('辰戌丑未')&set(zhis)) == 0:
    print("四柱地支缺四库，一生没有潜伏性凶灾。")
if ( '甲', '戊', '庚',) in (tuple(gans)[:3], tuple(gans)[1:]):
    print("地上三奇：白天生有申佳，需身强四柱有贵人。")
if ( '辛', '壬', '癸',) in (tuple(gans)[:3], tuple(gans)[1:]):
    print("人间三奇，需身强四柱有贵人。")
if ( '乙', '丙', '丁',) in (tuple(gans)[:3], tuple(gans)[1:]):
    print("天上三奇：晚上生有亥佳，需身强四柱有贵人。")
    
if zhi_shens2.count('亡神') > 1:
    print("二重亡神，先丧母；")
    
if get_empty(zhus[2],zhis.time):
    print("时坐空亡，子息少。 母法P24-41 母法P79-4：损破祖业，后另再成就。")
    
if zhis.count(me_jue) + zhis.count(me_tai) > 2:
    print("胎绝超过3个：夭或穷。母法P24-44 丁未 壬子 丙子 戊子")
       
if not_yang() and zhi_ku(zhis[2], (me,jie)) and zhi_ku(zhis[3], (me,jie)):
    print("阴日主时日支入比劫库：性格孤独，难发达。母法P28-112 甲申 辛未 辛丑 己丑 母法P55-11 为人孤独，且有灾疾")

#print(cai_lu, piancai_lu)
if zhis[1:].count(piancai_lu) + zhis[1:].count(cai_lu) + zhis[1:].count(piancai_di) + zhis[1:].count(cai_di) == 0:
    print("月日时支没有财或偏财的禄旺。")
    
if zhis[1:].count(guan_lu) + zhis[1:].count(guan_di) == 0:
    print("月日时支没有官的禄旺。")
    
if '辰' in zhis and ('戌' not in zhis) and options.n: 
    print("女命有辰无戌：孤。")
if '戌' in zhis and ('辰' not in zhis) and options.n: 
    print("女命有戌无辰：带禄。")
    
if emptie4s.get(zhus[2], 0) != 0:
    if scores[emptie4s.get(zhus[2], 0)] == 0:
        print("四大空亡：33岁以前身体不佳！")

for item in all_shens:
    print(item, ":",  shens_infos[item])
    
if options.n:
    print("#"*20, "女命")
    if all_shens_list.count("驿马") > 1:
        print("二逢驿马，母家荒凉。P110 丙申 丙申 甲寅 丁卯")
    if gan_shens[0] == '伤':
        print("年上伤官：带疾生产。P110 戊寅 戊午 丁未 丁未")    

print("-"*120)
            


children = ['食','伤'] if options.n else ['官','杀']

liuqins = bidict({'才': '父亲',"财":'财' if options.n else '妻', "印": '母亲', "枭": '偏印' if options.n else '祖父',
                  "官":'丈夫' if options.n else '女儿', "杀":'情夫' if options.n else '儿子', "劫":'兄弟' if options.n else '姐妹', "比":'姐妹' if options.n else '兄弟', 
                  "食":'女儿' if options.n else '下属', "伤":'儿子' if options.n else '孙女'})

# 六亲分析
for item in Gan:
    print("{}:{} {}-{} {} {} {}".format(item, ten_deities[me][item], liuqins[ten_deities[me][item]],  ten_deities[item][zhis[0]] ,ten_deities[item][zhis[1]], ten_deities[item][zhis[2]], ten_deities[item][zhis[3]]), end='  ')
    if Gan.index(item) == 4:
        print()
    
print()
print()

# 计算上运时间，有年份时才适用



gongs = get_gong(zhis)
zhis_g = set(zhis) | set(gongs)

jus = []
for item in zhi_hes:
    if set(item).issubset(zhis_g):
        print("三合局", item)
        jus.append(ju[ten_deities[me].inverse[zhi_hes[item]]])
        
        
for item in zhi_huis:
    if set(item).issubset(zhis_g):
        print("三会局", item)
        jus.append(ju[ten_deities[me].inverse[zhi_huis[item]]])

for item in gan_scores:  
    print("{}[{}]-{} ".format(
        item, ten_deities[me][item], gan_scores[item]),  end='  ')    
print()
print("-"*120)
yinyangs(zhis)
shen_zhus = list(zip(gan_shens, zhi_shens))

minggong = Zhi[::-1][(Zhi.index(zhis[1]) + Zhi.index(zhis[3]) -6  )%12 ]
print(minggong, minggongs[minggong])
print("坐：", rizhus[me+zhis.day])



# 地网
if '辰' in zhis and '巳' in zhis:
    print("地网：地支辰巳。天罗：戌亥。天罗地网全凶。")
    
# 天罗
if '戌' in zhis and '亥' in zhis:
    print("天罗：戌亥。地网：地支辰巳。天罗地网全凶。")

# 魁罡格
if zhus[2] in (('庚','辰'), ('庚','戌'),('壬','辰'), ('戊','戌'),):
    print("魁罡格：基础96，日主庚辰,庚戌,壬辰, 戊戌，重叠方有力。日主强，无刑冲佳。")
    print("魁罡四柱曰多同，贵气朝来在此中，日主独逢冲克重，财官显露祸无穷。魁罡重叠是贵人，天元健旺喜临身，财官一见生灾祸，刑煞俱全定苦辛。")

# 金神格
if zhus[3] in (('乙','丑'), ('己','巳'),('癸','酉')):
    print("金神格：基础97，时柱乙丑、己巳、癸酉。只有甲和己日，甲日为主，甲子、甲辰最突出。月支通金火2局为佳命。不通可以选其他格")
    
# 六阴朝阳
if me == '辛' and zhis.time == '子':
    print("六阴朝阳格：基础98，辛日时辰为子。")
    
# 六乙鼠贵
if me == '乙' and zhis.time == '子':
    print("六阴朝阳格：基础99，乙日时辰为子。忌讳午冲，丑合，不适合有2个子。月支最好通木局，水也可以，不适合金火。申酉大运有凶，午也不行。夏季为伤官。入其他格以格局论。")

# 从格
if max(scores.values()) > 25:
    print("有五行大于25分，需要考虑专格或者从格。")
    print("从旺格：安居远害、退身避位、淡泊名利,基础94;从势格：日主无根。")
    
    
if zhi_6he[3]:
    if abs(Gan.index(gans[3]) - Gan.index(gans[2])) == 1:
        print("日时干邻支合：连珠得合：妻贤子佳，与事业无关。母法总则P21-11")
        
for i,item in enumerate(zhis):
    if item == me_ku:
        if gan_shens[i] in ('才','财'):
            print("财坐劫库，大破败。母法P61-4 戊寅 丙辰 壬辰 庚子")
            
#print(zhi_6chong[3], gans, me)
if zhi_6chong[3] and  gans[3] == me:
    print("日时天比地冲：女为家庭辛劳，男艺术宗教。 母法P61-5 己丑 丙寅 甲辰 甲戌")
    
#print(zhi_6chong[3], gans, me)
if zhi_xing[3] and  gan_ke(me, gans[3]):
    print("日时天克地刑：破败祖业、自立发展、后无终局。 母法P61-7 己丑 丙寅 甲午 庚午") 
    
if (cai,yin_lu) in zhus and (cai not in zhi_shens2):
    print("浮财坐印禄:破祖之后，自己也败。 母法P78-29 辛丑 丁酉 壬寅 庚子") 
    
    
for i in range(3):
    if is_yang():
        break
    if zhi_xing[i] and zhi_xing[i+1] and gan_ke(gans[i], gans[i+1]):
        print("阴日主天克地刑：孤独、双妻。 母法P61-7 己丑 丙寅 甲午 庚午") 


# 建禄格
if zhi_shens[1] == '比':
    all_ges.append('建')
    print("建禄格：最好天干有财官。如果官杀不成格，有兄弟，且任性。有争财和理财的双重性格。如果创业独自搞比较好，如果合伙有完善的财务制度也可以。")
    if gan_shens[0] in '比劫':
        print("\t建禄年透比劫凶")
    elif '财' in gan_shens and '官' in gan_shens:
        print("\t建禄财官双透，吉")
    if me in ('甲','乙'):
        print("\t甲乙建禄四柱劫财多，无祖财，克妻，一生不聚财，做事虚诈，为人大模大样，不踏实。乙财官多可为吉。甲壬申时佳；乙辛巳时佳；")

    if me in ('丙'):
        print("\t丙：己亥时辰佳；")        
    if me in ('丁'):
        print("\t丁：阴男克1妻，阳男克3妻。财官多可为吉。庚子时辰佳；")
    if me in ('戊'):
        print("\t戊：四柱无财克妻，无祖业，后代多事端。如合申子辰，子息晚，有2子。甲寅时辰佳；")       
    if me in ('己'):
        print("\t己：即使官财出干成格，妻也晚。偏财、杀印成格为佳。乙丑时辰佳；")    
    if me in ('庚'):
        print("\t庚：上半月生难有祖财，下半月较好，财格比官杀要好。丙戌时辰佳；")   
    if me in ('辛'):
        print("\t辛：干透劫财，妻迟财少；丁酉时辰佳；")      
    if me in ('壬'):
        print("\t 壬：戊申时辰佳；")  
    if me in ('癸'):
        print("\t 癸：己亥时辰佳")      
                

        
# 甲分析 

if me == '甲':
    if zhis.count('辰') > 1 or zhis.count('戌') > 1:
        print("甲日：辰或戌多、性能急躁不能忍。")
    if zhis[2] == '子':
        print("甲子：调候要火。")
    if zhis[2] == '寅':
        print("甲寅：有主见之人，需要财官旺支。")        
    if zhis[2] == '辰':
        print("甲辰：印库、性柔和而有实权。")   
    if zhis[2] == '午':
        print("甲午：一生有财、调候要水。")        
    if zhis[2] == '戌':
        print("甲戌：自坐伤官，不易生财，为人仁善。")      
        
if me in ('庚', '辛') and zhis[1] == '子' and zhis.count('子') >1:
    print("冬金子月，再有一子字，孤克。 母法P28-106 甲戌 丙子 庚子 丁丑")  
    

# 比肩分析
if '比' in gan_shens:
    print("比：同性相斥。讨厌自己。老是想之前有没有搞错。没有持久性，最多跟你三五年。 散财，月上比肩，做事没有定性，不看重钱，感情不持久。不怀疑人家，人心很好。善意好心惹麻烦。年上问题不大。")
    
    if gan_shens[0] == '比' and gan_shens[1] == '比':
        print("比肩年月天干并现：不是老大，出身平常。女仪容端庄，有自己的思想；不重视钱财,话多不能守秘。30随以前是非小人不断。")

    if gan_shens[1] == '比' and '比' in zhi_shen3[1]:
        print("月柱干支比肩：争夫感情丰富。30岁以前钱不够花。")
        
    if gan_shens[0] == '比':
        print("年干比：上面有哥或姐，出身一般。")
        
    if zhi_shens[2] == '比':
        print("基52女坐比透比:夫妻互恨 丙辰 辛卯 辛酉 甲午。")  
                
        
    if gan_shens.count('比') > 1:
        print("""----基51:天干2比
        自我排斥，易后悔、举棋不定、匆促决定而有失；男倾向于群力，自己决策容易孤注一掷，小事谨慎，大事决定后不再重复考虑。
        女有自己的思想、容貌佳，注意细节，喜欢小孩重过丈夫。轻视老公。对丈夫多疑心，容易吃醋冲动。
        男不得女欢心.
        难以保守秘密，不适合多言；
        地支有根，一生小是非不断。没官杀制，无耐心。 END""")
    
                
    # 比肩过多
    if shens2.count('比') > 2 and '比' in zhi_shens:
        #print(shens2, zhi_shens2)
        print('''----比肩过多基51：
        女的爱子女超过丈夫；轻易否定丈夫。 换一种说法：有理想、自信、贪财、不惧内。男的双妻。
        兄弟之间缺乏帮助。夫妻有时不太和谐。好友知交相处不会很久。
        即使成好格局，也是劳累命，事必躬亲。除非有官杀制服。感情烦心。
        基53：善意多言，引无畏之争；难以保守秘密，不适合多言；易犯无事忙的自我表现；不好意思拒绝他人;累积情绪而突然放弃。
        比肩过多，女：你有帮夫运，多协助他的事业，多提意见，偶尔有争执，问题也不大。女：感情啰嗦
        对人警惕性低，乐天知命;情感过程多有波折
        ''') 
        
        if (not '官' in shens) and  (not '杀' in shens):
            print("基51: 比肩多，四柱无正官七杀，性情急躁。")            
            

        if '劫' in gan_shens:
            print("天干比劫并立，比肩地支专位，女命感情丰富，多遇争夫。基52")    
            
        if gan_shens[0] == '比':
            print("年干为比，不是长子，父母缘较薄，晚婚。")  
            
        if gan_shens[3] == '比':
            print("母法总则P21-6：时干为比，如日时地支冲，男的对妻子不利，女的为夫辛劳，九流艺术、宗教则关系不大。")              
            
        if gan_shens[1] == '比':
            if zhi_shens[1] == '食':
                print("月柱比坐食，易得贵人相助。")
            if zhi_shens[1] == '伤':
                print("月柱比坐伤，一生只有小财气，难富贵。")    
            if zhi_shens[1] == '比':
                print("月柱比坐比，单亲家庭，一婚不能到头。地支三合或三会比，天干2比也如此。")
            if zhi_shens[1] == '财':
                print("月柱比坐财，不利妻，也主父母身体不佳。因亲友、人情等招财物的无谓损失。")      
            if zhi_shens[1] == '杀':
                print("月柱比坐杀，稳重。")                   
        
        
    for seq, gan_ in enumerate(gan_shens):
        if gan_ != '比':
            continue
        if zhis[seq] in  empties[zhus[2]]:
            print("基51:比肩坐空亡，不利父亲与妻。年不利父，月不利父和妻，在时则没有关系。甲戌 丙寅 甲子 己巳\n\t基52女：夫妻缘分偏薄，在年只是不利父，在月30岁以前夫妻缘薄 E")
        if zhi_shens[seq] == '比':
            print("比坐比-平吉：与官杀对立，无主权。养子：克偏财，泄正印。吉：为朋友尽力；凶：受兄弟朋友拖累。父缘分薄，自我孤僻，男多迟婚")   
        if zhi_shens[seq] == '劫':
            print("女比肩坐劫:夫妻互恨，基52丁丑 壬子 壬戌 壬寅。\n\t还有刑冲且为羊刃，女恐有不测之灾：比如车祸、开刀和意外等。基52丙午 庚子 丙戌 丙申")     
            print("比坐劫-大凶：为忌亲友受损，合作事业中途解散，与妻子不合。如年月3见比，父缘薄或已死别。")   
            if ten_deities[gans[seq]][zhis[seq]] == '绝' and seq < 2:
                print("比肩坐绝，兄弟不多，或者很难谋面。戊己和壬癸的准确率偏低些。")   
        if zhi_shens[seq] == '财':
            print("比肩坐财：因亲人、人情等原因引起无谓损失。")  
        if zhi_shens[seq] == '杀':
            print("比肩坐杀:稳重。")    
        if zhi_shens[seq] == '枭':
            print("比肩坐偏印：三五年发达，后面守成。")    
        if zhi_shens[seq] == '劫' and Gan.index(me) % 2 == 0:
            print("比肩坐阳刃：父亲先亡，基于在哪柱判断时间。基51：丙午 丙申 丙申 丁酉。E在年不利父，在其他有刀伤、车祸、意外灾害。\t基52女命年克父亲，月若30岁以前结婚不利婚姻")    
        if zhi_shens[seq] in ('劫','比') and'劫' in gan_shens:
            print("天干比劫并立，比肩又坐比劫，女多遇争夫，个性强，不易协调。")   
        if  zhi_xing[seq]:
            print("比肩坐刑(注意不是半刑)，幼年艰苦，白手自立长。 甲申 己巳 甲寅 庚午 基51")
            if zhi_shens[seq] == '劫':
                print("比肩坐刑劫,兄弟不合、也可能与妻子分居。")      
        if zhi_6chong[seq]:
            print("比肩冲，手足不和，基于柱定时间 甲申 己巳 甲寅 庚午 基51。女命忌讳比劫和合官杀，多为任性引发困难之事。")                
                        
if zhi_shens[2] == '比':
    print("日支比：1-39对家务事有家长式领导；钱来得不容易且有时有小损财。e 自我，如有刑冲，不喜归家！")
if zhi_shens[3] == '比':
    print("时支比：子女为人公正倔强、行动力强，能得资产。")    
if '比' in (gan_shens[1],zhi_shens[1]):
    print("月柱比：三十岁以前难有成就。冒进、不稳定。女友不持久、大男子主义。")
if '比' in (gan_shens[3],zhi_shens[3]):
    print("时柱比：与亲人意见不合。")

if shens.count('比') + shens.count('劫') > 1:
    print("比劫大于2，男：感情阻碍、事业起伏不定。")
    

# 日坐禄   
if me_lu == zhis[2]:
    
    if zhis.count(me_lu) > 1:
        if yin_lu in zhis:
            if '比' in gan_shens or '劫' in gan_shens:
                
                print("双禄带比印（专旺）、孤克之命。比论孤，劫论凶。母法总则P20-3。比禄印劫不可合见四位")
                
    if zhi_6he[2] and '比' in gan_shens:
        if yin_lu in zhis:   
            print("透比，坐禄六合，有印专旺：官非、残疾。六合近似劫财，如地支会印，法死。 母法总则P20-4")
          
        print("透比，坐禄六合，如地支会印，法死。 母法总则P20-4")    
        

    if (zhi_xing[3] and gan_he[3] and gan_shens[3] == '财') or (zhi_xing[2] and gan_he[2] and zhi_xing[1] and gan_he[1] and gan_shens[1] == '财'):
          
        print("日禄与正财干合支刑：克妻子，即便是吉命，也无天伦之乐。 母法总则P22-21")    
        
if zhis.count(me_lu) > 2:
    print("禄有三，孤。 母法总则P23-36")
    
    
if zhis[3] == me_ku:
    if '财' in gan_shens or '才' in gan_shens:
        print("时支日库，透财：清高、艺术九流。 母法总则P59-5 己未 辛未 丁巳 庚戌 P61-8 丁未 壬寅 癸卯 丙辰")
        
    if piancai_lu == zhis[2]:
        print("时支日库，坐偏财：吉祥近贵，但亲属淡薄。 母法总则P59-6 辛未 辛卯 丁酉 庚戌")
    


    
# 时坐禄   
if me_lu == zhis[3]:
    if '伤' in gan_shens and '伤' in zhi_shens2:   
        print("时禄，伤官格，晚年吉。 母法总则P56-26 己未 丙寅 乙丑 己卯")
    if '杀' == gan_shens[3]:   
        print("杀坐时禄：为人反复不定。 母法总则P56-28 己未 丙寅 乙丑 己卯")
    
# 自坐劫库
if  zhis[2] == me_ku: 
    if gan_shens[3] == '杀' and '杀' in zhi_shen3[3]:
        print("自坐劫库,时杀格，贵！母法总则P30-143 辛未 辛卯 壬辰 戊申 母法总则P55-14 P60-22")  
        
    if gan_shens[3] == '官' and '官' in zhi_shen3[3]:
        print("自坐劫库,正官格，孤贵！母法总则P56-24 辛未 辛卯 壬辰 戊申 母法总则P55-14")   
            
    if zhi_ku(zhis[3], (cai,piancai)):
        print("自坐劫库,时财库，另有刃禄孤刑艺术，无者辛劳！母法总则P30-149 母法总则P56-17 56-18") 
        
    if gan_shens[3] == '财' and '财' in zhi_shen3[3]:
        print("自坐劫库，时正财格，双妻，丧妻。 母法总则P55-13 己酉 戊寅 壬辰 丁未 P61-6 乙酉 戊寅 壬辰 丁未")
        
    if (yin, me_lu) in zhus:
        print("自坐劫库,即便吉，也会猝亡 母法总则P61-9 丁丑 甲辰 壬辰 辛亥")


# 劫财分析
if '劫' in gan_shens:
    print("劫财扶助，无微不至。劫财多者谦虚之中带有傲气。凡事先理情，而后情理。先细节后全局。性刚强、精明干练、女命不适合干透支藏。")
    print("务实，不喜欢抽象性的空谈。不容易认错，比较倔。有理想，但是不够灵活。不怕闲言闲语干扰。不顾及别人面子。")
    print("合作事业有始无终。太重细节。做小领导还是可以的。有志向，自信。杀或食透干可解所有负面。女命忌讳比劫和合官杀，多为任性引发困难之事。")
    
    if gan_shens[0] == '劫' and gan_shens[1] == '劫':
        print("劫年月天干并现：喜怒形于色，30岁以前大失败一次。过度自信，精明反被精明误。")

    if gan_shens[1] == '劫':
        if  '劫' in zhi_shen3[1]:
            print("月柱干支劫：与父亲无缘，30岁以前任性，早婚防分手，自我精神压力极其重。")
        if  zhis[1] == cai_lu and zhis.count(yin_lu) > 1:
            print("月干劫：月支财禄，如地支2旺印，旺财不敌，官非、刑名意外。")            
          
        
    if shens2.count('劫') > 2:
        print('----劫财过多, 婚姻不好')
    if zhi_shens[2] == '劫':
        print("日坐劫财，透天干。在年父早亡，在月夫妻关系不好。比如财产互相防范；鄙视对方；自己决定，哪怕对方不同意；老夫少妻；身世有差距；斤斤计较；敢爱敢恨的后遗症\n\t以上多针对女。男的一般有双妻。天干有杀或食可解。基54丁未 己酉 丙午 己丑") 
            
if zhus[2] in (('壬','子'),('丙','午'), ('戊','午')):
    print("日主专位劫财，壬子和丙午，晚婚。不透天干，一般是眼光高、独立性强。对配偶不利，互相轻视；若刑冲，做事立场不明遭嫉妒，但不会有大灾。女性婚后通常还有自己的事业,能办事。") 
if ('劫','伤') in shen_zhus or ('伤','劫',) in shen_zhus:
        print("同一柱中，劫财、阳刃伤官都有，外表华美，富屋穷人，婚姻不稳定，富而不久；年柱不利家长，月柱不利婚姻，时柱不利子女。伤官的狂妄。基55丙申 丁酉 甲子 丁卯")      

if gan_shens[0] == '劫':
    print("年干劫财：家运不济。克父，如果坐劫财，通常少年失父；反之要看地支劫财根在哪一柱子。")
        
if '劫' in (gan_shens[1],zhi_shens[1]):
    print("月柱劫：容易孤注一掷，30岁以前难稳定。男早婚不利。")
if '劫' in (gan_shens[3],zhi_shens[3]):
    print("时柱劫：只要不是去经济大权还好。")   
if zhi_shens[2] == '劫':
    print("日支劫：男的克妻，一说是家庭有纠纷，对外尚无重大损失。如再透月或时天干，有严重内忧外患。")
    
if '劫' in shens2 and  '比' in zhi_shens and '印' in shens2 and not_yang():
    print("阴干比劫印齐全，单身，可入道！")
    
if zhi_shens[0] == '劫' and is_yang(): 
    print("年阳刃：得不到长辈福；不知足、施恩反怨。")
if zhi_shens[3] == '劫' and is_yang(): 
    print("时阳刃：与妻子不和，晚无结果，四柱再有比刃，有疾病与外灾。")
    
# 阳刃格        
if zhi_shens[1] == '劫' and is_yang():
    all_ges.append('刃')
    print("阳刃格：喜七杀或三四个官。基础90 甲戊庚逢冲多祸，壬丙逢冲还好。")  
    if me in ('庚', '壬','戊'):
        print("阳刃'庚', '壬','午'忌讳正财运。庚逢辛酉凶，丁酉吉，庚辰和丁酉六合不凶。壬逢壬子凶，戊子吉；壬午和戊子换禄不凶。")
    else:
        print("阳刃'甲', '丙',忌讳杀运，正财偏财财库运还好。甲：乙卯凶，辛卯吉；甲申与丁卯暗合吉。丙：丙午凶，壬午吉。丙子和壬午换禄不凶。")
        
    if zhis.count(yin_lu) > 0 and gan_shens[1] == '劫': # 母法总则P20-1
        print("阳刃格月干为劫：如果印禄位有2个，过旺，凶灾。不透劫财，有一印禄,食伤泄，仍然可以吉。 母法总则P20-1")
        
    if gan_shens[3] == '枭' and '枭' in zhi_shen3[3]:
        
        print("阳刃格:时柱成偏印格，贫、夭、带疾。 母法总则P28-107 癸未 辛酉 庚寅 戊寅")
                
        
if zhi_shens.count('劫') > 1 and Gan.index(me) % 2 == 0:
    if zhis.day == yin_lu:
        print("双阳刃，自坐印专位：刑妻、妨子。凶终、官非、意外灾害。母法总则P21-13")
        
if zhi_shens[1:].count('劫') > 0 and Gan.index(me) % 2 == 0:
    if zhis.day == yin_lu and ('劫' in gan_shens or '比' in gan_shens):
        print("阳刃，自坐印专位，透比或劫：刑妻。母法总则P36-8 己酉 丁卯 甲子 乙亥")
        
if zhis[2] in (me_lu,me_di) and zhis[3] in (me_lu,me_di):
    print("日时禄刃全，如没有官杀制，刑伤父母，妨碍妻子。母法总则P30-151 丁酉 癸卯 壬子 辛亥 母法总则P31-153 ")
    
#print(gan_shens)
for seq, gan_ in enumerate(gan_shens):
    if gan_ != '劫':
        continue    
    if zhis[seq] in (cai_lu, piancai_lu):
        print("劫财坐财禄，如逢冲，大凶。先冲后合和稍缓解！母法总则P21-7 书上实例不准！")
        
        if zhi_shens[seq] == '财' and zhi_6he[seq]:
            print("劫财坐六合财支：久疾暗病！母法总则P28-113 乙未 丙戌 辛亥 庚寅！")

if gan_shens[1] == '劫' and zhis[1] in (cai_lu, piancai_lu)  and zhis.count(yin_lu) > 1 and '劫' in gan_shens:
    print("月干劫坐财禄，有2印禄，劫透，财旺也败：官非、刑名、意外灾害！  母法总则P20-2")
    
# 自坐阳刃
if '劫' in zhi_shen3[2] and is_yang() and zhis[2] in zhengs:  
    if zhis[3] in (cai_lu, piancai_lu):
        print("坐阳刃,时支财禄，吉祥但是妻子性格不受管制！母法总则P30-137 丁未 庚戌 壬子 乙巳")
    if zhi_ku(zhis[3], (cai, piancai)):
        print("坐阳刃,时支财库，名利时进时退！母法总则P30-148 丙寅 壬寅 壬子 庚戌")
            
    if gan_shens[3] == '杀' and '杀' in zhi_shen3[3]:
        print("坐阳刃,时杀格，贵人提携而富贵！母法总则P30-143 甲戌 丙寅 壬子 戊申")
    
 
# 偏印分析    
if '枭' in gan_shens:
    print("----偏印在天干如成格：偏印在前，偏财(财次之)在后，有天月德就是佳命(偏印格在日时，不在月透天干也麻烦)。忌讳倒食，但是坐绝没有这能力。")
    print("经典认为：偏印不能扶身，要身旺；偏印见官杀未必是福；喜伤官，喜财；忌日主无根；   女顾兄弟姐妹；男六亲似冰")
    print("偏印格干支有冲、合、刑，地支是偏印的绝位也不佳。")
    
    #print(zhi_shen3)  
    if (gan_shens[1] == '枭' and '枭' in zhi_shen3[1]):        
        print("枭月重叠：福薄慧多，青年孤独，有文艺宗教倾向。")
        
    if zhi_shens2.count('枭') > 1:
        print("偏印根透2柱，孤独有色情之患难。做事有始无终，女声誉不佳！pd40")

    if  zhi_shens2.count('枭'):
        print("偏印成格基础89生财、配印；最喜偏财同时成格，偏印在前，偏财在后。最忌讳日时坐实比劫刃。")
        all_ges.append('枭')
              
    if shens2.count('枭') > 2:
        print("偏印过多，性格孤僻，表达太含蓄，要别人猜，说话有时带刺。偏悲观。有偏财和天月德贵人可以改善。有艺术天赋。做事大多有始无终。如四柱全阴，女性声誉不佳。")
        print("对兄弟姐妹不错。男的因才干受子女尊敬。女的偏印多，子女不多。第1克伤食，第2艺术性。")
        if '伤' in gan_shens: 
            print("女命偏印多，又与伤官同透，夫离子散。有偏财和天月德贵人可以改善。")
        
    if gan_shens.count('枭') > 1:
        print("天干两个偏印：迟婚，独身等，婚姻不好。三偏印，家族人口少，亲属不多建。基56甲午 甲戌 丙午 丙申")
        
    if shen_zhus[0] == ('枭', '枭'):
        print("偏印在年，干支俱透，不利于长辈。偏母当令，正母无权，可能是领养，庶出、同父异母等。 基56乙卯 甲申 丁丑 丁未")

    if zhi_shen3[1] == ['枭']:
        print("月专位偏印：有手艺。坐衰其貌不扬。")
        
    
for seq, zhi_ in enumerate(zhi_shens):
    if zhi_ != '枭' and gan_shens[seq] != '枭':
        continue   

    if ten_deities[gans[seq]][zhis[seq]] == '绝':
        print("偏印坐绝，或者天干坐偏印为绝，难以得志。费力不讨好。基56辛酉 辛卯 丁巳 甲辰  丁卯 丁未 己丑 丁卯")    

    if  gan_shens[seq] == '枭':
        if '枭' in zhi_shen3[seq] :
            print("干支都与偏印，克夫福薄！")  

        if '比' in zhi_shen3[seq] :
            print("偏印坐比：劳心劳力，常遇阴折 pd41")   

        if zhi_shens[seq] == '伤':
            print("偏印坐伤官：克夫丧子 pd41")        

    
if zhi_shens[3]  == '枭' and gan_shens[0]  == '枭':
    print("偏印透年干-时支，一直受家里影响。")
    
if '枭' in (gan_shens[0],zhi_shens[0]):
    print("偏印在年：少有富贵家庭；有宗教素养，不喜享乐，第六感强。")
if '枭' in (gan_shens[1],zhi_shens[1]):
    print("偏印在月：有慧少福，能舍己为人。")
    if zhi_shens[1]  == '枭' and zhis[1] in "子午卯酉":
        print("偏印专位在月支：比较适合音乐，艺术，宗教等。子午卯酉。22-30之间职业定型。基56：壬午 癸卯 丁丑 丁未")
        if gan_shens[1] == '枭':
            print("干支偏印月柱，专位入格，有慧福浅，不争名利。基57:戊子 辛酉 癸未 丁巳")    
if '枭' in (gan_shens[3],zhi_shens[3]):
    print("偏印在时：女与后代分居；男50以前奠定基础，晚年享清福。")     
if zhi_shens[2] == '枭' or zhis.day == xiao_lu:
    print("偏印在日支：家庭生活沉闷")
    if zhi_6chong[2] or zhi_xing[2]:
        print("偏印在日支(专位？),有冲刑：孤独。基57：甲午 癸酉 丁卯 丁未 母法总则P55-5： 辛丑 辛卯 癸酉 戊午 P77-13")
    if zhus[2] in (('丁','卯'),('癸','酉')):
        print("日专坐偏印：丁卯和癸酉。婚姻不顺。又刑冲，因性格而起争端而意外伤害。 基56")   
    if zhis[3] == me_jue:
        print("日坐偏印，日支绝：无亲人依靠，贫乏。 母法总则P55-5：丙辰 丙申 丁卯 壬子。pd41 专位偏印：男女姻缘都不佳。")  
    
    if '枭' in gan_shens and is_yang() and zhis.time == me_di:
        
        print("日坐偏印成格，时支阳刃：不利妻子，自身有疾病。 母法总则P55-6：甲子 甲戌 丙寅 甲午")  
    if gan_shens[3] == zhi_shens[3] == '劫':
        print("日坐偏印，时干支劫：因自己性格而引灾。 母法总则P57-34：甲子 甲戌 丙寅 甲午")
        
    if zhis.count(me_di) > 1 and is_yang():
        print("日坐偏印，地支双阳刃：性格有极端倾向。 母法总则P57-35：甲申 庚午 丙寅 甲午")

        
if zhis.time == xiao_lu:
    if zhi_shens[3] == '枭' and '枭' in gan_shens:
        if '财' in shens2 or '才' in shens2:
            print("时支偏印成格有财：因机智引凶。 母法总则P60-18：甲申 乙亥 丁亥 癸卯")        
        else:
            print("时支偏印成格无财：顽固引凶。 母法总则P60-17：甲子 乙亥 丁亥 癸卯")
        

# 印分析    
if '印' in gan_shens:
    if '印' in zhi_shens2:
        print("基础82，成格喜官杀、身弱、忌财克印。合印留财，见利忘义.透财官杀通关或印生比劫；合冲印若无他格或调候破格。日主强凶，禄刃一支可以食伤泄。")
        all_ges.append('印')
        
    if (gan_shens[1] == '印' and '印' in zhi_shen3[1]):        
        print("印月重叠：女迟婚，月阳刃者离寡，能独立谋生，有修养的才女。")

    if gan_shens[0] == '印' :        
        print("年干印为喜：出身于富贵之家。")
            
    if shens2.count('印') > 2:
        print("正印多的：聪明有谋略，比较含蓄，不害人，识时务。正印不怕日主死绝，反而怕太强。日主强，正印多，孤寂，不善理财。 pd41男的克妻，子嗣少。女的克母。")
    for seq, gan_ in enumerate(gan_shens):
        if gan_ != '印':
            continue   
        if ten_deities[gans[seq]][zhis[seq]] in ('绝', '死'):
            if seq <3:
                print("正印坐死绝，或天干正印地支有冲刑，不利母亲。时柱不算。")   
        if zhi_shens[seq] == '财':
            print("男正印坐正财，夫妻不好。月柱正印坐正财专位，必离婚。在时柱，50多岁才有正常婚姻。(男) 基59 乙酉 己卯 庚子 丁亥  庚申 庚辰 庚午 己卯")   
        if zhi_shens[seq] == '印':
            print("正印坐正印，专位，过于自信。基59：戊辰 乙卯 丙申 丙申。务实，拿得起放得下。女的话大多晚婚。母长寿；女子息迟，头胎恐流产。女四柱没有官杀，没有良缘。男的搞艺术比较好，经商则孤僻，不聚财。")          

        if zhi_shens[seq] == '枭' and len(zhi5[zhis[seq]]) == 1:
            print("正印坐偏印专位：基59壬寅 壬子 乙酉 甲申。有多种职业;家庭不吉：亲人有疾或者特别嗜好。子息迟;财务双关。明一套，暗一套。女的双重性格。")   
            
        if zhi_shens[seq] == '伤':
            print("正印坐伤官：适合清高的职业。不适合追逐名利，女的婚姻不好。基59辛未 丁酉 戊子 丙辰")    
            
        if zhi_shens[seq] == '劫' and me in ('甲','庚','壬'):
            print("正印坐阳刃，身心多伤，心疲力竭，偶有因公殉职。主要指月柱。工作看得比较重要。")    
                        
            
    if '杀' in gan_shens and '劫' in zhi_shens and me in ('甲','庚','壬'):
        print("正印、七杀、阳刃全：基60癸巳 庚申 甲寅 丁卯：女命宗教人，否则独身，清高，身体恐有隐疾，性格狭隘缺耐心。男小疾多，纸上谈兵，婚姻不佳，恐非婚生子女，心思细腻对人要求也高。")    
            
    if '官' in gan_shens or '杀' in gan_shens: 
        print("身弱官杀和印都透天干，格局佳。")
    else:
        print("单独正印主秀气、艺术、文才。性格保守")  
    if '官' in gan_shens or '杀' in gan_shens or '比' in gan_shens: 
        print("正印多者，有比肩在天干，不怕财。有官杀在天干也不怕。财不强也没关系。")  
    else:
        print("正印怕财。") 
    if '财' in gan_shens:     
        print("印和财都透天干，都有根，最好先财后印，一生吉祥。先印后财，能力不错，但多为他人奔波。(男)") 
       
       
if zhi_shens[1]  == '印':
    print("月支印：女命觉得丈夫不如自己，分居是常态，自己有能力。")  
    if gan_shens[1]  == '印':
        print("月干支印：男权重于名，女命很自信，与夫平权。pd41:聪明有权谋，自我")    
        if '比' in gan_shens:
            print("月干支印格，透比，有冲亡。")
            
if zhi_shens[2]  == '印':
    if gan_shens[3] == '才' and '才' in zhi_shen3[3]:
        print("坐印，时偏财格：他乡发迹，改弦易宗，妻贤子孝。 母法总则：P55-1 丁丑 丁未 甲子 戊辰") 
        
    if gan_shens[3] == '财' and ('财' in zhi_shen3[3] or zhis[3] in (cai_di, cai_lu)):
        print("坐印，时财正格：晚年发达，妻贤子不孝。 母法总则：P55-2 乙酉 丙申 甲子 己巳") 

            
if zhi_shens[3]  == '印' and zhis[3] in zhengs:
    print("时支专位正印。男忙碌到老。女的子女各居一方。亲情淡薄。")  
    
if gan_shens[3]  == '印' and '印' in zhi_shen3[3]:
    print("时柱正印格，不论男女，老年辛苦。女的到死都要控制家产。子女无缘。")   
    
if gan_shens.count('印') + gan_shens.count('枭') > 1:
    print("印枭在年干月干，性格迂腐，故作清高，女子息迟，婚姻有阻碍。印枭在时干，不利母子，性格不和谐。")  
    

if zhis[1] in (yin_lu, xiao_lu) :
    print("印或枭在月支，有压制丈夫的心态。")  
    
if zhis[3] in (yin_lu, xiao_lu) :
    print("印或枭在时支，夫灾子寡。")  
 
# 坐印库   
if zhi_ku(zhis[2], (yin, xiao)):
    if shens2.count('印') >2:
        print("母法总则P21-5: 日坐印库，又成印格，意外伤残，凶终。过旺。")
    if zhi_shens[3] == '劫':
        print("自坐印库，时阳刃。带比禄印者贫，不带吉。 母法总则P21-14")  

if zhis.count("印") > 1:
    if gan_shens[1] == "印" and zhi_shens[1] == "印" and '比' in gan_shens:
        print("月干支印，印旺，透比，旺而不久，冲亡。母法总则P21-8") 
        
if zhis[1] == yin_lu:
    if ('财' in gan_shens and '财' in zhi_shens) or ('才' in gan_shens and '才' in zhi_shens):
        print("母法总则P22-18 自坐正印专旺，成财格，移他乡易宗，妻贤子孝。") 
        
        
# 偏财分析    
if '才' in gan_shens:
    print("偏财明现天干，不论是否有根:财富外人可见;实际财力不及外观一半。没钱别人都不相信;协助他人常超过自己的能力")
    print("偏财出天干，又与天月德贵人同一天干者。在年月有声明远扬的父亲，月时有聪慧的红颜知己。喜奉承。")
    print("偏财透天干，四柱没有刑冲，长寿。女子为孝顺女，主要针对年月。时柱表示中年以后有自己的事业，善于理财。")
    if '才' in zhi_shens2:
        print("财格基础80:比劫用食伤通关或官杀制；身弱有比劫仍然用食伤通关。如果时柱坐实比劫，晚年破产。")  
        all_ges.append('才')
    print("偏财透天干，讲究原则，不拘小节。喜奉承，善于享受。财格基础80")
    
    if '比' in gan_shens or '劫' in gan_shens and gan_shens[3] == '才':
        print("年月比劫，时干透出偏财。祖业凋零，再白手起家。有刑冲为千金散尽还复来")
    if '杀' in gan_shens and '杀' in zhi_shens:
        print("偏财和七杀并位，地支又有根，父子外合心不合。因为偏财生杀攻身。偏财七杀在日时，则为有难伺候的女朋友。 基62壬午 甲辰 戊寅 癸亥")
        
    if zhi_shens[0]  == '才':
        print("偏财根透年柱，家世良好，且能承受祖业。")
        
    for seq, gan_ in enumerate(gan_shens):
        if gan_ != '才':
            pass
        if '劫' in zhi_shen3[seq] and zhis[seq] in zhengs:
            print("偏财坐阳刃劫财,可做父缘薄，也可幼年家贫。也可以父先亡，要参考第一大运。偏财坐专位阳刃劫财,父亲去他乡.基61壬午 壬寅 戊子 丁巳")   
        if get_empty(zhus[2],zhis[seq]) == '空':
            print("偏财坐空亡，财官难求。")                    
                
if shens2.count('才') > 2:
    print("偏财多的人慷慨，得失看淡。花钱一般不会后悔。偏乐观，甚至是浮夸。生活习惯颠倒。适应能力强。有团队精神。得女性欢心。小事很少失信。")
    print("乐善好施，有团队精神，女命偏财，听父亲的话。时柱偏财女，善于理财，中年以后有事业。")
if (zhi_shens[2]  == '才' and len(zhi5[zhis[2]]) == 1) or (zhi_shens[3]  == '才' and len(zhi5[zhis[3]]) == 1):
    print("日时地支坐专位偏财。不见刑冲，时干不是比劫，大运也没有比劫刑冲，晚年发达。")
    
    
    
# 财分析    

if (gan_shens[0] in ('财', '才')  and gan_shens[1]  in ('财', '才')) or (gan_shens[1] in ('财', '才') and ('财' in zhi_shen3[1] or '才' in zhi_shen3[1])):
    print("财或偏财月重叠：女职业妇女，有理财办事能力。因自己理财能力而影响婚姻。一财得所，红颜失配。男的双妻。")
    

if '财' in gan_shens:
    if '财' in zhi_shens2:
        all_ges.append('财')
        
    if is_yang():        
        print("男日主合财星，夫妻恩爱。如果争合或天干有劫财，双妻。")
    if '财' in zhi_shens:
        print("财格基础80:比劫用食伤通关或官杀制；身弱有比劫仍然用食伤通关。")
        
    if '官' in gan_shens:
        print("正官正财并行透出，(身强)出身书香门第。")
    if '官' in gan_shens or '杀' in gan_shens:
        print("官或杀与财并行透出，女压夫，财生官杀，老公压力大。")
    if gan_shens[0] == '财':
        print("年干正财若为喜，富裕家庭，但不利母亲。")
    if '财' in zhi_shens:
        if '官' in gan_shens or '杀' in gan_shens:
            print("男财旺透官杀，女厌夫。")
    if gan_shens.count('财') > 1:
        print("天干两正财，财源多，大多做好几种生意，好赶潮流，人云亦云。有时会做自己外行的生意。")
        if '财' not in zhi_shens2:
            print("正财多而无根虚而不踏实。重财不富。")
            
for seq, gan_ in enumerate(gan_shens):
    if gan_ != '财' and zhis[seq] != '财':
        continue   
    if zhis[seq] in day_shens['驿马'][zhis.day] and seq != 2:
        print("女柱有财+驿马，动力持家。")
    if zhis[seq] in day_shens['桃花'][zhis.day] and seq != 2:
        print("女柱有财+桃花，不吉利。")        
    if zhis[seq] in empties[zhus[2]]:
        print("财坐空亡，不持久。")    
    if ten_deities[gans[seq]][zhis[seq]] in ('绝', '墓'):
        print("男财坐绝或墓，不利婚姻。")
            
if shens2.count('财') > 2:
    print("正财多者，为人端正，有信用，简朴稳重。")
    if '财' in zhi_shens2 and (me not in zhi_shens2):
        print("正财多而有根，日主不在生旺库，身弱惧内。")   
        
if zhi_shens[1] == '财' and options.n:
    print("女命月支正财，有务实的婚姻观。")
    
if zhi_shens[1] == '财':
    print("月令正财，无冲刑，有贤内助，但是母亲与妻子不和。生活简朴，多为理财人士。")
if zhi_shens[3] == '财' and len(zhi5[zhis[3]]) == 1:
    print("时支正财，一般两个儿子。")
if zhus[2] in (('戊','子'),) or zhus[3] in (('戊','子'),):
    print("日支专位正财，得勤俭老婆。即戊子。日时专位支正财，又透正官，中年以后发达，独立富贵。") 
    
if zhus[2] in (('壬','午'),('癸','巳'),):
    print("坐财官印，只要四柱没有刑冲，大吉！") 
    
if zhus[2] in (('甲','戌'),('乙','亥'),):
    print("女('甲','戌'),('乙','亥'） 晚婚 -- 不准！") 
    
if '财' == gan_shens[3] or  '财' == zhi_shens[3]:
    
    print("未必准确：时柱有正财，口快心直，不喜拖泥带水，刑冲则浮躁。阳刃也不佳.反之有美妻佳子") 
if (not '财' in shens2) and (not '才' in shens2):
    print("四柱无财，即便逢财运，也是虚名虚利. 男的晚婚")
    

#print("shang", shang, ten_deities[shang].inverse['建'], zhi_shens)
#if ten_deities[shang].inverse['建'] in zhis:
    #print("女命一财得所，红颜失配。")  
    
if zhis.day in (cai_lu, cai_di):
    if (zhi_shens[1] == '劫' or zhi_shens[3] == '劫' ) and Gan.index(me) % 2 == 0:
        print("自坐财禄，月支或时支为阳刃，凶。无冲是非多，冲刑主病灾。 母法总则P22-15  母法总则P36-4 丙寅 戊戌 甲午 丁卯 P56-32 己未 丙寅 丙申 甲午")   
    if ('劫' in zhi_shens ) and Gan.index(me) % 2 == 0 and '劫' in gan_shens :
        print("自坐财禄，透劫财，有阳刃，刑妻无结局。 母法总则P36-7 戊子 乙卯 甲午 乙亥") 
    if me in ('甲', '乙') and ('戊' in gans or '己' in gans):
        print("火土代用财，如果透财，多成多败，早年灰心。 母法总则P22-19 辛未 癸巳 甲午 戊辰") 
        
    if gan_shens[3] == '枭':
        print("财禄时干偏印：主亲属孤独 母法总则P31-158 丁丑 丙午 甲辰 己巳")
        if '枭' in zhi_shen3[3]:
            print("财禄时干偏印格：财虽吉、人丁孤单、性格艺术化 母法总则P56-20 己巳 丙辰 甲午 壬申")
            
    if zhis[3] == yin_lu:
        print("坐财禄，时支印禄：先难后易 母法总则P30-147 甲申 己巳 壬午 己酉 母法总则P55-16")
                  
     
if (gan_he[3] and gan_shens[3] == '财' and jin_jiao(zhis[2], zhis[3]) ) or (gan_he[2] and gan_he[1] and gan_shens[1] == '财' and jin_jiao(zhis[1], zhis[2])):
      
    print("日主合财且进角合：一生吉祥、平安有裕！ 母法总则P22-22 丁丑 丙午 甲辰 己巳")    
    
    
if zhis.day == cai_lu or zhi_shens[2] == '财':
    if gan_shens[3] == '枭' and ('枭' in zhi_shen3[3] or zhis[3] == xiao_lu ):
        print("日坐财，时偏印格：他乡有成，为人敦厚。母法总则P55-4 甲寅 辛未 甲午 壬申")
    if zhi_6chong[2] or zhi_xing[2]:
        print("日坐财，有冲或刑：财吉而有疾。母法总则P55-10 丙寅 戊戌 甲午 甲子")    

        
if gan_shens[3] == '财' and zhi_ku(zhis[3], (me,jie)):
    print("正财坐日库于时柱:孤独、难为父母，但事业有成。 母法总则P31-156 丁丑 丙午 甲辰 己巳")

# 自坐财库    
if zhis[2] == cai_ku: 
    if zhis[3] == me_ku :
        print("自坐财库,时劫库：有财而孤单。 母法总则P30-136 丁丑 丙午 甲辰 己巳 母法总则P55-11 P61-5 甲子 己巳 壬戌 甲辰")
        
    if zhis[2] == zhis[3]:
        print("自坐财库,时坐财库：妻有灾，妻反被妾制服。 母法总则P30-150 辛酉 乙未 壬戌 庚戌 母法总则P56-19")
    
        
    if gan_shens[3] == '杀' and '杀' in zhi_shen3[3]:
        print("自坐财库,时杀格，财生杀，凶！母法总则P30-147 甲寅 己巳 壬戌 戊申 有可能是时柱有杀就算。 母法总则P55-15")    
    
# 时坐财库    
if zhi_ku(zhis[3], (cai,piancai)): 
    if '伤' in gan_shens and '伤' in zhi_shens:
        print("时坐财库,伤官生财:财好，体弱，旺处寿倾倒！母法总则P59-8 戊申 辛酉 戊子 丙辰")

if gan_shens[3] == '财' and '财' in zhi_shen3[3]:
    print("时上正财格:不必财旺，因妻致富。 母法总则P30-140 丙午 戊戌 壬寅 丁未 母法总则P60-21") 
    
    if zhis[3] == me_ku:
        print("时上正财格坐比劫库，克妻。 母法总则P30-141 丙午 戊戌 壬寅 丁未")
    if zhis[2] == cai_ku:
        print("时上正财格自坐财库，妻佳，中年丧妻，续弦也佳。 母法总则P30-142 庚子 辛巳 壬戌 丁未 P61-7")

#print(cai_di, cai_lu, zhis, gan_he)        
if zhis[3] in (cai_di, cai_lu):
    if gan_he[3]:
        print("时财禄，天干日时双合，损妻家财。 母法总则P31-157 庚戌 戊寅 癸酉 戊午")
    if '伤' == gan_shens[3] and '伤' in zhi_shens2:
        print("时支正财时干伤成格：虽富有也刑克。 母法总则P59-1 丁丑 壬寅 丁巳 戊申")
    #print(zhi_ku(zhis[1], (shi,shang)) , (shi,shang), zhis[3] == cai_lu)
    if zhi_ku(zhis[1], (shi,shang)) and zhis[3] == cai_lu:
        print("时支正财禄，月支伤入墓：生财极为辛勤。 母法总则P59-4 甲子 戊辰 庚戌 己卯")
        
# print(cai_di, cai_lu, zhis, gan_he)        
if zhis[3] == cai_lu:
    if zhi_xing[3] or zhi_6chong[3]:
        print("时支正财禄有冲刑：得女伴且文学清贵。 母法总则P60-11 丁丑 辛亥 己巳 乙亥")
    if any(zhi_xing[:3]) or any(zhi_6chong[:3]):
        print("时支正财禄,它支有冲刑：刑妻、孤高、艺术、近贵人。 母法00总则P60-19 乙未 己丑 庚寅 己卯")
    if gan_shens.count('财') >1 :
        print("时支正财禄,天干财星多：孤雅、九流、表面风光。 母法总则P60-20 乙酉 乙酉 庚辰 己卯")
    

# 官分析    
if '官' in gan_shens:
    if '官' in zhi_shens2:
        print("官若成格：忌伤；忌混杂；基础78。有伤用财通关或印制。混杂用合或者身官两停。日主弱则不可扶。")
        all_ges.append('官')
        
        if '比' in gan_shens or '劫' in gan_shens:
            print("官格透比或劫：故做清高或有洁癖的文人。")

        if '伤' in gan_shens:
            print("官格透伤：表里不一。")    
            
        if '财' in gan_shens or '才' in gan_shens:
            print("官格透财：聚财。")     
            
        if '印' in gan_shens:
            print("官格透印：人品清雅。")   
            
        if not ('印' in gan_shens or '财' in gan_shens or '才' in gan_shens):
            print("官独透成格：敦厚人。")               

        
    if (gan_shens[0] == '官' and gan_shens[1] == '官') or (gan_shens[1] == '官' and '官' in zhi_shen3[1]):
        print("官月重叠：女易离婚，早婚不吉利。为人性格温和。")
            
    if gan_shens[3] == '官' and len(zhi5[zhis[3]]) == 1:
        print("官专位时坐地支，男有得力子息。")
    if gan_shens[0] == '官' :
        print("年干为官，身强有可能出身书香门第。")
        if gan_shens[3] == '官':
            print("男命年干，时干都为官，对后代和头胎不利。")
    if (not '财' in gan_shens) and (not '印' in gan_shens):
        print("官独透天干成格，四柱无财或印，为老实人。")
    if '伤' in gan_shens:
        print("正官伤官通根透，又无其他格局，失策。尤其是女命，异地分居居多，婚姻不美满。基64:辛未 丁酉 甲戌 辛未 ")
    if '杀' in gan_shens:
        print("年月干杀和偏官，30以前婚姻不稳定。月时多为体弱多病。")
        
    if '印' in gan_shens and '印' in zhi_shens2 and '官' in zhi_shens2:
        print("官印同根透，无刑冲合，吉。")
        if '财' in gan_shens and '财' in zhi_shens2:
            print("财官印同根透，无刑冲合，吉。")
        
    if gan_shens[1] == '官' in ten_deities[me][zhis[1]] in ('绝', '墓'):
        print("官在月坐墓绝，不是特殊婚姻就是迟婚。如果与天月德同柱，依然不错。丈夫在库中：1，老夫少妻；2，不为外人所知的亲密感情；3，特殊又合法的婚姻。")
    if zhi_shens[1] == '官' and gan_shens[1] == '官':
        print("月柱正官坐正官，婚变。月柱不宜通。坐禄的。")  

    
    for seq, gan_ in enumerate(gan_shens):
        if gan_ != '官':
            continue   
        if zhi_shens[seq] in ('劫','比') :
            print("天干正官，地支比肩或劫财，亲友之间不适合合作，但是他适合经营烂摊子。")
        if zhi_shens[seq] == '杀' :
            print("正官坐七杀，男命恐有诉讼之灾。女命婚姻不佳。月柱尤其麻烦，二度有感情纠纷。年不算，时从轻。 基64 壬子 壬子 丁丑 癸卯")
        if zhi_shens[seq] == '劫' and Gan.index(me) % 2 == 0:
            print("官坐羊刃：要杀才能制服阳刃，有力不从心之事情。 辛卯 丁酉 庚午 庚辰 基65")   
        if zhi_shens[seq] == '印':
            print("官坐印，无刑冲合，吉")   
        
            
if shens2.count('官') > 2 and '官' in gan_shens and '官' in zhi_shens2:
    print("正官多者，虚名。为人性格温和，比较实在。做七杀看")
if zhis.day == guan_lu or zhi_shens[2] == '官':
    print("日坐正官专位，淑女。 基65 庚申 癸未 丙子 乙未")
    if is_yang() and zhis.time == me_di:
        print("日坐正官，时支阳刃：先富后败，再东山再起。 子平母法 P55-7")
    
if gan_shens.count('官') > 2 :
    print("天干2官，女下有弟妹要照顾，一生为情所困。")   
    

if zhi_shens[1] == '官' and '伤' in zhi_shens2:
    print("月支正官，又成伤官格，难做真正夫妻。有实，无名。 基66辛丑 辛卯 戊子 辛酉")
    
    
# 杀分析    
if '杀' in gan_shens:
    print("七杀是非多。但是对男人有时是贵格。比如毛主席等。成格基础85可杀生印或食制印、身杀两停、阳刃驾杀。")
    if '杀' in zhi_shens2:
        print("杀格：喜食神制，要食在前，杀在后。阳刃驾杀：杀在前，刃在后。身杀两停：比如甲寅日庚申月。杀印相生，忌食同成格。")
        all_ges.append('杀')
        
        if '比' in gan_shens or '劫' in gan_shens:
            print("杀格透比或劫：性急但还有分寸。")

        if '杀' in gan_shens:
            print("杀格透官：精明琐屑，不怕脏。")    
            
        if '食' in gan_shens or '伤' in gan_shens:
            print("杀格透食伤：外表宁静，内心刚毅。")     
            
        if '印' in gan_shens:
            print("杀格透印：圆润、精明干练。")   
        
    if (gan_shens[0] == '杀' and gan_shens[1] == '杀') :
        print("杀月干年干重叠：不是老大，出身平常，多灾，为人不稳重。")
        
    if (gan_shens[1] == '杀' and '杀' in zhi_shen3[1]):        
        print("杀月重叠：女易离婚，其他格一生多病。")
        
    if gan_shens[0] == '杀':
        print("年干七杀，早年不好。或家里穷或身体不好。")
        if gan_shens[1] == '杀':
            print("年月天干七杀，家庭复杂。")
    if '官' in gan_shens:
        print("官和杀同见天干不佳。女在年干月干，30以前婚姻不佳，或体弱多病。基65 甲寅 乙亥 戊子 丙辰")
    if gan_shens[1] == '杀' and zhi_shens[1] == '杀':
        print("月柱都是七杀，克得太过。有福不会享。六亲福薄。时柱没关系。")
        if '杀' not in zhi_shens2 :
            print("七杀年月浮现天干，性格好变，不容易定下来。30岁以前不行。")        
    if '杀' in zhi_shens and '劫' in zhi_shens:
        print("七杀地支有根时要有阳刃强为佳。杀身两停。")
    if gan_shens[1] == '杀' and gan_shens[3] == '杀':
        print("月时天干为七杀：体弱多病")    
    if gan_shens[0] == '杀' and gan_shens[3] == '杀':
        print("七杀年干时干：男头胎麻烦（概率），女婚姻有阻碍。")  
    if gan_shens[3] == '杀':
        print("七杀在时干，固执有毅力。基67")       
    if '印' in gan_shens:
        print("身弱杀生印，不少是精明练达的商人。")  
    if '财' in gan_shens or '才' in gan_shens:
        print("财生杀，如果不是身弱有印，不佳。")  
        for zhi_ in zhis: 
            if set((ten_deities[me].inverse['杀'], ten_deities[me].inverse['财'])) in set(zhi5[zhi_]):
                print("杀不喜与财同根透出，这样杀的力量太强。")  


for seq, gan_ in enumerate(gan_shens):
    if gan_ != '杀' and zhi_shens[seq] != '杀':
        continue   
    if gan_ == '杀' and '杀' in zhi_shen3[seq] and seq != 3:
        print("七杀坐七杀，六亲福薄。")
    if get_empty(zhus[2],zhis[seq]) == '空':
        print("七杀坐空亡，女命夫缘薄。 基68 壬申 庚戌 甲子 丙寅")
    if zhis[seq] == '食':
        print("七杀坐食：易有错误判断。")
    if zhi_xing[seq] or zhi_6chong[seq]:
        print("七杀坐刑或对冲，夫妻不和。")
        
            
if shens2.count('杀') > 2:
    print("杀多者如果无制，性格刚强。打抱不平，不易听人劝。女的喜欢佩服的人。")
if zhi_shens[2]  == '杀' and len(zhi5[zhis[2]]) == 1:
    print("天元坐杀：乙酉，己卯，如无食神，阳刃，性急，聪明，对人不信任。如果七杀还透出月干无制，体弱多病，甚至夭折。如果在时干，晚年不好。")
    
if zhus[2] in (('丁', '卯'), ('丁', '亥'), ('丁', '未')) and zhis.time == '子':
    print("七杀坐桃花，如有刑冲，引感情引祸。忌讳午运。")
    
if gan_shens.count('杀') > 2 :
    print("天干2杀，不是老大、性格浮躁不持久。")   

if ten_deities[shang].inverse['建'] in zhis and options.n:
    print("女地支有杀的禄：丈夫条件还可以。对外性格急，对丈夫还算顺从。")  
    
    
    
if zhis[2] == me_jue:
    print("#"*10, "自坐绝")
    if zhi_6he[2]:
        
        print("自己坐绝（天元坐杀）：日支与它支合化、双妻，子息迟。母法总则P21-9 P56-30 d第10点暂未编码。") 
        
    print("自己坐绝支，绝支合会，先贫后富。母法总则P57-3 母法总则P23-33")  
    if zhis[3] == zhis[2]:
        print("日主日时绝，旺达则有刑灾。母法总则P57-2 母法总则P24-43 戊午 癸亥 乙酉 乙酉")  
        
    if zhis[3] == zhis[2] == zhis[1]:
        print("日主月日时绝，旺达则有刑灾，平常人不要紧。母法总则P57-1")  
    if zhi_shens.count('比') + zhi_shens.count('劫') > 1 :
        print("自坐绝，地支比劫大于1，旺衰巨变，凶：母法总则P22-16。 母法总则P36-5月支或时支都为阳刃，凶。")
    
    if zhis[1] == me_jue:
        print("日主月日绝，有格也疾病夭。母法总则P23-35")  
        
    if zhis[3] == cai_lu:
        print(" 母法总则P59-2  自坐绝，月支财禄:身弱财旺有衰困时，克妻子。书上例子不对")   
        
    if zhis[3] == cai_di:
        print(" 母法总则P59-3  自坐绝，月支偏财禄:有困顿时娶背景不佳妻。书上例子不对")   



        
if zhis[3] == me_jue:
    print("#"*10, "自己时坐绝: 母法总则P57-4: 若成伤官格，难求功名，适合艺术九流。")
    if zhi_shens[2] == '枭':
        print("母法总则P57-5: 自时支坐绝，自坐枭: 不是生意人，清贫艺术九流人士。")
    #print(zhi_shens, cai_di, cai_lu)
    if zhis[1] in (cai_di, cai_lu):
        print(" 母法总则P57-6  自时支坐绝，月支坐财:先富，晚年大败，刑破。 癸未 庚申 丁巳 庚子")    

    if zhis[1] in (me_lu, me_di):
        print(" 母法总则P28-114  自时支坐绝，月支帝:刑妻克子。 甲子 癸酉 辛丑 辛卯 -- 阴干也算阳刃？")   
        
    if zhis[3] in (cai_di,cai_lu):
        print(" 母法总则P57-8  自时支坐绝，时支财:中年发后无作为。 甲子 癸酉 辛丑 辛卯")   
        

if zhis[2] == sha_lu:
    if zhi_ku(zhis[3], (guan, sha)):
        print("自坐杀禄，时支为官杀库，一生有疾，生计平常。 母法总则P21-12 母法总则P55-8 甲子 丙寅 乙酉 己丑 P56-31")    
        
if zhis[3] == sha_lu:
    if zhi_xing[3] or zhi_6chong[3]:
        
        print("时支杀禄带刑冲：纵然吉命也带疾不永寿。 母法总则P60-15 乙未 乙酉 戊申 甲寅")  

if gan_shens[3] == '杀' and zhis[3] in (cai_di, cai_lu):
    print("七杀时柱坐财禄旺：性格严肃。 母法总则P59-7 母法总则P79-3 双妻，子息迟。 ")  

#print(sha_lu, zhi_6chong,zhi_xing )    
if zhis[3] == sha_lu:
    if (zhi_6chong[3] or zhi_xing[3]):
        print("七杀时禄旺：遇刑冲寿夭带疾。 母法总则P28-118 冲别的柱也算？ 乙未 戊寅 辛丑 甲午 ") 
    if zhis[1] == sha_lu:
        print("七杀时月禄旺：体疾。 母法总则P28-119 甲寅 庚午 辛丑 甲午  母法总则P60-16")
 
#print(zhi_ku(zhis[2], (guan,sha)),set(zhis), set('辰戌丑未'))      
if zhi_ku(zhis[2], (guan,sha)):
    if set(zhis).issubset(set('辰戌丑未')):
        print("自坐七杀入墓：地支都为库，孤独艺术。 母法总则P57-33  丙辰 戊戌 乙丑 庚辰") 
        
if '杀' in gan_shens and zhi_shens.count('杀') > 1:
    print("七杀透干，地支双根，不论贫富，亲属离散。母法总则P79-6 乙未 丙戌 戊寅 甲寅") 
    
if  '杀' in jus + all_ges:

    if '比' in gan_shens or '劫' in gan_shens:
        print("杀格透比或劫：性急但还有分寸。")
    
    if '杀' in gan_shens:
        print("杀格透官：精明琐屑，不怕脏。")    
        
    if '食' in gan_shens or '伤' in gan_shens:
        print("杀格透食伤：外表宁静，内心刚毅。")     
        
    if '印' in gan_shens:
        print("杀格透印：圆润、精明干练。")   
     
# 食分析    
if '食' in gan_shens:
    if '食' in zhi_shens2:
        print("食神成格的情况下，寿命比较好。食神和偏财格比较长寿。食神厚道，为人不慷慨。食神有口福。成格基础84，喜财忌偏印(只能偏财制)。")
        print("食神无财一生衣食无忧，无大福。有印用比劫通关或财制。")
        all_ges.append('食')
        
        
    if (gan_shens[0] == '食' and gan_shens[1] == '食') or (gan_shens[1] == '食' and '食' in zhi_shen3[1]):
        print("食月重叠：生长安定环境，性格仁慈、无冲刑长寿。女早年得子。无冲刑偏印者是佳命。")


    if '枭' in gan_shens:
        print("男的食神碰到偏印，身体不好。怕偏印，正印要好一点。四柱透出偏财可解。")
        if '劫' in gan_shens:
            print("食神不宜与劫财、偏印齐出干。体弱多病。基69")
        if '杀' in gan_shens:
            print("食神不宜与杀、偏印齐成格。体弱多病。")
    if '食' in zhi_shens:
        print("食神天透地藏，女命阳日主适合社会性职业，阴日主适合上班族。")
    if (not '财' in gan_shens) and (not '才' in gan_shens):
        print("食神多，要食伤生财才好，无财难发。")
    if '伤' in gan_shens:
        print("食伤混杂：食神和伤官同透天干：志大才疏。")
    if '杀' in gan_shens:
        print("食神制杀，杀不是主格，施舍后后悔。")



    for seq, gan_ in enumerate(gan_shens):
        if gan_ != '食':
            continue   
        if zhi_shens[seq] =='劫':
            print("食神坐阳刃，辛劳。基69 戊申 戊午 丙子 丙申")
        
            
if shens2.count('食') > 2:
    print("食神四个及以上的为多，做伤官处理。食神多，要食伤生财才好，无财难发。")
    if '劫' in gan_shens or '比' in gan_shens:
        print("食神带比劫，好施舍，乐于做社会服务。")
        
if ('杀', '食') in shen_zhus or ( '食', '杀') in shen_zhus:
    print("食神与七杀同一柱，易怒。食神制杀，最好食在前。有一定概率。基69辛未 丁酉 乙未 戊寅")
    
if ('枭', '食') in shen_zhus or ( '食', '枭') in shen_zhus:
    print("女命最怕食神偏印同一柱。不利后代，时柱尤其重要。基69庚午 己卯 丁未 丁未")
    
if '食' in zhi_shen3[2] and zhis[2] in zhengs:
    print("日支食神专位容易发胖，有福。只有2日：癸卯，己酉。男命有有助之妻。")
if zhi_shens[2]  == '食' and zhi_shens[2]  == '杀':
    print("自坐食神，时支杀专，二者不出天干，多成败，最后失局。")  
    
if zhi_shens[2]  == '食':
    print("自坐食神，相敬相助，即使透枭也无事，不过心思不定，做事毅力不足，也可能假客气。专位容易发胖，有福。")
 
    
if zhis[2]  == shi_lu:
    if zhis[3]  == sha_lu and (sha not in gan_shens):
        print("自坐食，时支专杀不透干：多成败，终局失制。母法总则P56-22 丙子 庚寅 己酉 丁卯")

if '食' in zhi_shen3[3] and '枭' in zhi_shen3[3] + gan_shens[3]:
    print("时支食神逢偏印：体弱，慢性病，女的一婚不到头。")  
    
if zhis[2] in kus and zhi_shen3[2][2] in ('食', '伤'):
    print("自坐食伤库：总觉得钱不够。")
    
if  '食' in (gan_shens[0], zhi_shens[0]):
    print("年柱食：可三代同堂。")

if zhi_ku(zhis[3], (shi, shang)) and ('食' in zhi_shen3[1] or '伤' in zhi_shen3[1]):
    print("时食库，月食当令，孤克。")

# 自坐食伤库
if zhi_ku(zhis[2], (shi, shang)):  
    if zhis[3] == guan_lu:
        print("坐食伤库：时支官，发达时接近寿终。 母法总则P60-13 乙丑 丙戌 庚辰 壬午")

# 自坐食伤库
if zhi_ku(zhis[3], (shi, shang)):  
        
    if zhis[1] in (shi_di, shi_lu):
        print("坐食伤库：月支食伤当令，吉命而孤克。 母法总则P60-14 甲戌 丙子 辛卯 壬辰")
    

# 伤分析    
if '伤' in gan_shens:
    print("伤官有才华，但是清高。要生财，或者印制。")
    if '伤' in zhi_shens2:
        print("食神重成伤官，不适合伤官配印。金水、土金、木火命造更高。火土要调候，容易火炎土燥。伤官和七杀的局不适合月支为库。")
        all_ges.append('伤')
        print("伤官成格基础87生财、配印。不考虑调候逆用比顺用好，调候更重要。生正财用偏印，生偏财用正印。\n伤官配印，如果透杀，透财不佳。伤官七杀同时成格，不透财为上好命局。")

    if (gan_shens[0] == '伤' and gan_shens[1] == '伤') or (gan_shens[1] == '伤' and '伤' in zhi_shen3[1]):
        print("父母兄弟均无缘。孤苦，性刚毅好掌权。30岁以前有严重感情苦重，适合老夫少妻，继室先同居后结婚。")


    if '印' in gan_shens and ('财' not in gan_shens):
        print("伤官配印，无财，有手艺，但是不善于理财。有一定个性")
    if gan_shens[0] == '伤' and gan_shens[1] == '伤' and (not '伤' in zhi_shens2):
        print("年月天干都浮现伤官，亲属少。")

    if zhi_shens[1]  == '伤' and len(zhi5[zhis[1]]) == 1 and gan_shens[1] == '伤':
        print("月柱：伤官坐专位伤官，夫缘不定。假夫妻。比如老板和小蜜。")


    for seq, gan_ in enumerate(gan_shens):
        if gan_ != '伤':
            continue   
        if zhi_shens[seq] =='劫':
            print("伤官地支坐阳刃，力不从心 基70己酉 丁卯 甲午 辛未。背禄逐马，克官劫财。影响15年。伤官坐劫财：只适合纯粹之精明商人或严谨掌握财之人。")       
            
if shens2.count('伤') > 2:
    if options.n:        
        print("女命伤官多，即使不入伤官格，也缘分浅，多有苦情。")
    if gan_shens.count('伤') > 2:
        print("天干2伤官：性骄，六亲不靠。婚前诉说家人，婚后埋怨老公。30岁以前为婚姻危机期。")
        
    
if zhi_shens[2]  == '伤' and len(zhi5[zhis[2]]) == 1:
    print("女命婚姻宫伤官：强势克夫。男的对妻子不利。只有庚子日。")
    
if gan_shens[3]  == '伤' and me_lu == zhis[3]:
    print("伤官坐时禄：六亲不靠，无冲刑晚年发，有冲刑不发。 母法P27-96己未 壬申 己亥 庚午, 可以参三命。")

if zhis[3]  in (shang_lu, shang_di) and  zhis[1]  in (shang_lu, shang_di):
    print("月支时支食伤当令：日主无根，泄尽日主，凶。 母法P28-104 甲午 乙亥 庚戌 丙子  母法P60-104")
    
#print("shang", shang, ten_deities[shang].inverse['建'], zhi_shens)
if ten_deities[shang].inverse['建'] in zhis and options.n:
    print("女命地支伤官禄：婚姻受不得穷。")        
    
print("局", jus, "格", all_ges, )

print("\n\n《六十日用法口诀》")    
print("=========================")      
print(days60[me+zhis.day])

if me+zhis.month in months:
    print("\n\n《穷通宝鉴》")    
    print("=========================")      
    print(months[me+zhis.month])


sum_index = ''.join([me, '日', *zhus[3]])
if sum_index in summarys:
    print("\n\n《三命通会》")    
    print("=========================")      
    print(summarys[sum_index])

print("\n\n《十二时辰（初中末）出生吉凶》")    
print("=========================")      
print(chens[zhis.time])

if not options.b:
    print("\n\n大运")    
    print("="*120)  
    for dayun in yun.getDaYun()[1:]:
        gan_ = dayun.getGanZhi()[0]
        zhi_ = dayun.getGanZhi()[1]
        fu = '*' if (gan_, zhi_) in zhus else " "
        zhi5_ = ''
        for gan in zhi5[zhi_]:
            zhi5_ = zhi5_ + "{}{}　".format(gan, ten_deities[me][gan]) 
        
        zhi__ = set() # 大运地支关系
        
        for item in zhis:
        
            for type_ in zhi_atts[zhi_]:
                if item in zhi_atts[zhi_][type_]:
                    zhi__.add(type_ + ":" + item)
        zhi__ = '  '.join(zhi__)
        
        empty = chr(12288)
        if zhi_ in empties[zhus[2]]:
            empty = '空'        
        
        jia = ""
        if gan_ in gans:
            for i in range(4):
                if gan_ == gans[i]:
                    if abs(Zhi.index(zhi_) - Zhi.index(zhis[i])) == 2:
                        jia = jia + "  --夹：" +  Zhi[( Zhi.index(zhi_) + Zhi.index(zhis[i]) )//2]
                    if abs( Zhi.index(zhi_) - Zhi.index(zhis[i]) ) == 10:
                        jia = jia + "  --夹：" +  Zhi[(Zhi.index(zhi_) + Zhi.index(zhis[i]))%12]
                
        out = "{1:<4d}{2:<5s}{3} {15} {14} {13}  {4}:{5}{8}{6:{0}<6s}{12}{7}{8}{9} - {10:{0}<10s} {11}".format(
            chr(12288), dayun.getStartAge(), '', dayun.getGanZhi(),ten_deities[me][gan_], gan_,check_gan(gan_, gans), 
            zhi_, yinyang(zhi_), ten_deities[me][zhi_], zhi5_, zhi__,empty, fu, nayins[(gan_, zhi_)], ten_deities[me][zhi_]) 
        gan_index = Gan.index(gan_)
        zhi_index = Zhi.index(zhi_)
        out = out + jia + get_shens(gans, zhis, gan_, zhi_)
        
        print(out)
        zhis2 = list(zhis) + [zhi_]
        gans2 = list(gans) + [gan_]
        for liunian in dayun.getLiuNian():
            gan2_ = liunian.getGanZhi()[0]
            zhi2_ = liunian.getGanZhi()[1]
            fu2 = '*' if (gan2_, zhi2_) in zhus else " "
            #print(fu2, (gan2_, zhi2_),zhus)
            
            zhi6_ = ''
            for gan in zhi5[zhi2_]:
                zhi6_ = zhi6_ + "{}{}　".format(gan, ten_deities[me][gan])        
            
            # 大运地支关系
            zhi__ = set() # 大运地支关系
            for item in zhis2:
            
                for type_ in zhi_atts[zhi2_]:
                    if type_ == '破':
                        continue
                    if item in zhi_atts[zhi2_][type_]:
                        zhi__.add(type_ + ":" + item)
            zhi__ = '  '.join(zhi__)
            
            empty = chr(12288)
            if zhi2_ in empties[zhus[2]]:
                empty = '空'       
            out = "{1:>3d} {2:<5d}{3} {15} {14} {13}  {4}:{5}{8}{6:{0}<6s}{12}{7}{8}{9} - {10:{0}<10s} {11}".format(
                chr(12288), liunian.getAge(), liunian.getYear(), gan2_+zhi2_,ten_deities[me][gan2_], gan2_,check_gan(gan2_, gans2), 
                zhi2_, yinyang(zhi2_), ten_deities[me][zhi2_], zhi6_, zhi__,empty, fu2, nayins[(gan2_, zhi2_)], ten_deities[me][zhi2_]) 
            
            jia = ""
            if gan2_ in gans2:
                for i in range(5):
                    if gan2_ == gans2[i]:
                        zhi1 = zhis2[i]
                        if abs(Zhi.index(zhi2_) - Zhi.index(zhis2[i])) == 2:
                            # print(2, zhi2_, zhis2[i])
                            jia = jia + "  --夹：" +  Zhi[( Zhi.index(zhi2_) + Zhi.index(zhis2[i]) )//2]
                        if abs( Zhi.index(zhi2_) - Zhi.index(zhis2[i]) ) == 10:
                            # print(10, zhi2_, zhis2[i])
                            jia = jia + "  --夹：" +  Zhi[(Zhi.index(zhi2_) + Zhi.index(zhis2[i]))%12]  

                        if (zhi1 + zhi2_ in gong_he) and (gong_he[zhi1 + zhi2_] not in zhis):
                            jia = jia + "  --拱：" + gong_he[zhi1 + zhi2_]
                            
            out = out + jia + get_shens(gans, zhis, gan2_, zhi2_)
            all_zhis = set(zhis2) | set(zhi2_)
            if set('戌亥辰巳').issubset(all_zhis):
                out = out + "  天罗地网：戌亥辰巳"
            if set('寅申巳亥').issubset(all_zhis) and len(set('寅申巳亥')&set(zhis)) == 2 :
                out = out + "  四生：寅申巳亥"   
            if set('子午卯酉').issubset(all_zhis) and len(set('子午卯酉')&set(zhis)) == 2 :
                out = out + "  四败：子午卯酉"  
            if set('辰戌丑未').issubset(all_zhis) and len(set('辰戌丑未')&set(zhis)) == 2 :
                out = out + "  四库：辰戌丑未"             
            print(out)
            
        
    
    # 计算星宿
    d2 = datetime.date(1, 1, 4)
    print("星宿", lunar.getXiu(), lunar.getXiuSong())
    
    # 计算建除
    seq = 12 - Zhi.index(zhis.month)
    print(jianchus[(Zhi.index(zhis.day) + seq)%12])        
    
# 检查三会 三合的拱合
result = ''
#for i in range(2):
    #result += check_gong(zhis, i*2, i*2+1, me, gong_he)
    #result += check_gong(zhis, i*2, i*2+1, me, gong_hui, '三会拱')

result += check_gong(zhis, 1, 2, me, gong_he)
result += check_gong(zhis, 1, 2, me, gong_hui, '三会拱')
    
if result:
    print(result)

print("="*120)   



# 格局分析
ge = ''
if (me, zhis.month) in jianlus:
    print(jianlu_desc)
    print("-"*120)
    print(jianlus[(me, zhis.month)]) 
    print("-"*120 + "\n")
    ge = '建'
#elif (me == '丙' and ('丙','申') in zhus) or (me == '甲' and ('己','巳') in zhus):
    #print("格局：专财. 运行官旺 财神不背,大发财官。忌行伤官、劫财、冲刑、破禄之运。喜身财俱旺")
elif (me, zhis.month) in (('甲','卯'), ('庚','酉'), ('壬','子')):
    ge = '月刃'
else:
    zhi = zhis[1]
    if zhi in wuhangs['土'] or (me, zhis.month) in (('乙','寅'), ('丙','午'),  ('丁','巳'), ('戊','午'), ('己','巳'), ('辛','申'), ('癸','亥')):
        for item in zhi5[zhi]:
            if item in gans[:2] + gans[3:]:
                ge = ten_deities[me][item]
    else:
        d = zhi5[zhi]
        ge = ten_deities[me][max(d, key=d.get)]

# 天乙贵人
flag = False
for items in tianyis[me]:
    for item in items:
        if item in zhis:
            if not flag:
                print("| 天乙贵人：", end=' ')
                flag = True
            print(item, end=' ')
            
# 玉堂贵人
flag = False
for items in yutangs[me]:
    for item in items:
        if item in zhis:
            if not flag:
                print("| 玉堂贵人：", end=' ')
                flag = True
            print(item, end=' ')            

# 天罗
if  nayins[zhus[0]][-1] == '火':			
    if zhis.day in '戌亥':
        print("| 天罗：{}".format(zhis.day), end=' ') 

# 地网		
if  nayins[zhus[0]][-1] in '水土':			
    if zhis.day in '辰巳':
        print("| 地网：{}".format(zhis.day), end=' ') 		



# 学堂分析
for seq, item in enumerate(statuses):
    if item == '长':
        print("学堂:", zhis[seq], "\t", end=' ')
        if  nayins[zhus[seq]][-1] == ten_deities[me]['本']:
            print("正学堂:", nayins[zhus[seq]], "\t", end=' ')


#xuetang = xuetangs[ten_deities[me]['本']][1]
#if xuetang in zhis:
    #print("学堂:", xuetang, "\t\t", end=' ')
    #if xuetangs[ten_deities[me]['本']] in zhus:
        #print("正学堂:", xuetangs[ten_deities[me]['本']], "\t\t", end=' ')

# 学堂分析

for seq, item in enumerate(statuses):
    if item == '建':
        print("| 词馆:", zhis[seq], end=' ')
        if  nayins[zhus[seq]][-1] == ten_deities[me]['本']:
            print("- 正词馆:", nayins[zhus[seq]], end=' ')


ku = ten_deities[me]['库'][0]    
if ku in zhis:
    print("库：",ku, end=' ')

    for item in zhus: 
        if ku != zhus[1]:
            continue
        if nayins[item][-1] == ten_deities[me]['克']:
            print("库中有财，其人必丰厚")
        if nayins[item][-1] == ten_deities[me]['被克']:
            print(item, ten_deities[me]['被克'])
            print("绝处无依，其人必滞")    

print()

# 天元分析
for item in zhi5[zhis[2]]:    
    name = ten_deities[me][item]
    print(self_zuo[name])
print("-"*120)


# 出身分析
cai = ten_deities[me].inverse['财']
guan = ten_deities[me].inverse['官']
jie = ten_deities[me].inverse['劫']
births = tuple(gans[:2])
if cai in births and guan in births:
    birth = '不错'
#elif cai in births or guan in births:
    #birth = '较好'
else:
    birth = '一般'

print("出身:", birth)    

guan_num = shens.count("官")
sha_num = shens.count("杀")
cai_num = shens.count("财")
piancai_num = shens.count("才")
jie_num = shens.count("劫")
bi_num = shens.count("比")
yin_num = shens.count("印")





# 食神分析
if ge == '食':
    print("\n****食神分析****: 格要日主食神俱生旺，无冲破。有财辅助财有用。  食神可生偏财、克杀")
    print(" 阳日食神暗官星，阴日食神暗正印。食神格人聪明、乐观、优雅、多才多艺。食居先，煞居后，功名显达。")
    print("======================================")  
    print('''
    喜:身旺 宜行财乡 逢食看财  忌:身弱 比 倒食(偏印)  一名进神　　二名爵星　　三名寿星
    月令建禄最佳，时禄次之，更逢贵人运
    ''')

    shi_num = shens.count("食")
    if shi_num > 2:
        print("食神过多:食神重见，变为伤官，令人少子，纵有，或带破拗性. 行印运",end=' ')
    if set(('财','食')) in set(gan_shens[:2] + zhi_shens[:2]):
        print("祖父荫业丰隆", end=' ')
    if set(('财','食')) in set(gan_shens[2:] + zhi_shens[2:]):
        print("妻男获福，怕母子俱衰绝，两皆无成", end=' ')
    if cai_num >1:
        print("财多则不清，富而已", end=' ')

    for seq, item in enumerate(gan_shens):
        if item == '食':
            if ten_deities[gans[seq]][zhis[seq]] == '墓':
                print("食入墓，即是伤官入墓，住寿难延。")  


    for seq, item in enumerate(gan_shens):
        if item == '食' or zhi_shens[seq] == '食':
            if get_empty(zhus[2],zhis[seq]):
                print("大忌空亡，更有官煞显露，为太医师巫术数九流之士，若食神逢克，又遇空亡，则不贵，再行死绝或枭运，则因食上气上生灾，翻胃噎食，缺衣食，忍饥寒而已")                     

    # 倒食分析
    if '枭' in shens and (me not in ['庚', '辛','壬']) and ten_deities[me] != '建':
        flag = True
        for item in zhi5[zhis.day]:
            if ten_deities[me]['合'] == item:
                flag = False
                break
        if flag:
            print("倒食:凡命带倒食，福薄寿夭，若有制合没事，主要为地支为天干的杀;日支或者偏印的坐支为日主的建禄状态。偏印和日支的主要成分天干合")  
            print("凡命有食遇枭，犹尊长之制我，不得自由，作事进退悔懒，有始无终，财源屡成屡败，容貌欹斜，身品琐小，胆怯心虚，凡事无成，克害六亲，幼时克母，长大伤妻子") 
            print("身旺遇此方为福")
    print()
    print("-"*120)

# 伤官分析
if ge == '伤':
    print("\n****伤官分析****: 喜:身旺,财星,印绶,伤尽 忌:身弱,无财,刑冲,入墓枭印　")
    print(" 多材艺，傲物气高，心险无忌惮，多谋少遂，弄巧成拙，常以天下之人不如己，而人亦惮之、恶之。 一名剥官神　　二名羊刃煞")
    print(" 身旺用财，身弱用印。用印不忌讳官煞。用印者须去财方能发福")
    print("官星隐显，伤之不尽，岁运再见官星，官来乘旺，再见刑冲破害，刃煞克身，身弱财旺，必主徒流死亡，五行有救，亦残疾。若四柱无官而遇伤煞重者，运入官乡，岁君又遇，若不目疾，必主灾破。")
    print("娇贵伤不起、谨慎过头了略显胆小，节俭近于吝啬")
    print("======================================")  

    if '财' in shens or '才' in shens:
        print("伤官生财")
    else:
        print("伤官无财，主贫穷")
        
    if '印' in shens or '枭' in shens:
        print('印能制伤，所以为贵，反要伤官旺，身稍弱，始为秀气;印旺极深，不必多见，偏正叠出，反为不秀，故伤轻身重而印绶多见，贫穷之格也。')   
        if '财' in shens or '才' in shens:
            print('财印相克，本不并用，只要干头两清而不相碍；又必生财者，财太旺而带印，佩印者印太重而带财，调停中和，遂为贵格')
    if ('官' in shens) :
        print(shang_guans[ten_deities[me]['本']])   
        print('金水独宜，然要财印为辅，不可伤官并透。若冬金用官，而又化伤为财，则尤为极秀极贵。若孤官无辅，或官伤并透，则发福不大矣。')
    if ('杀' in shens) :
        print("煞因伤而有制，两得其宜，只要无财，便为贵格")   
    if gan_shens[0] == '伤':
        print("年干伤官最重，谓之福基受伤，终身不可除去，若月支更有，甚于伤身七煞")

    for seq, item in enumerate(gan_shens):
        if item == '伤':
            if ten_deities[gans[seq]][zhis[seq]] == '墓':
                print("食入墓，即是伤官入墓，住寿难延。")  


    for seq, item in enumerate(gan_shens):
        if item == '食' or zhi_shens[seq] == '食':
            if get_empty(zhus[2],zhis[seq]):
                print("大忌空亡，更有官煞显露，为太医师巫术数九流之士，若食神逢克，又遇空亡，则不贵，再行死绝或枭运，则因食上气上生灾，翻胃噎食，缺衣食，忍饥寒而已")                     
    print()
    print("-"*120)    

# 劫财分析
if ge == '劫':
    print("\n****劫财(阳刃)分析****：阳刃冲合岁君,勃然祸至。身弱不作凶。")
    print("======================================")  
    if "劫" == gan_shens[3] or "劫" == zhi_shens[3]:
        print("劫财阳刃,切忌时逢,岁运并临,灾殃立至,独阳刃以时言,重于年月日也。")

    shi_num = shens.count("食")
    print("-"*120)

# 财分析

if ge == '财' or ge == '才':
    print("\n****财分析 **** 喜:旺,印,食,官 忌:比 羊刃 空绝 冲合   财星,天马星,催官星,壮志神")
    if gan_shens.count('财') + gan_shens.count('才') > 1:
        print('财喜根深，不宜太露，然透一位以清用，格所最喜，不为之露。即非月令用神，若寅透乙、卯透甲之类，一亦不为过，太多则露矣。')
        print('财旺生官，露亦不忌，盖露不忌，盖露以防劫，生官则劫退，譬如府库钱粮，有官守护，即使露白，谁敢劫之？')
    if '伤' in gan_shens:
        print("有伤官，财不能生官")    
    if '食' in shens:
        print("有财用食生者，身强而不露官，略带一位比劫，益觉有情")     
        if '印' in shens or '枭' in 'shens':
            print("注意印食冲突")  
    if '比' in shens:
        print("比不吉，但是伤官食神可化!")   
    if '杀' in shens:
        print("不论合煞制煞，运喜食伤身旺之方!")          
    
    if "财" == zhi_shens[0]:
        print("岁带正马：月令有财或伤食，不犯刑冲分夺，旺祖业丰厚。同类月令且带比，或遇运行伤劫 贫")
    if "财" == zhi_shens[3]:
        print("时带正马：无冲刑破劫，主招美妻，得外来财物，生子荣贵，财产丰厚，此非父母之财，乃身外之财，招来产业，宜俭不宜奢。")      
    if "财" == zhi_shens[2] and (me not in ('壬','癸')):
        print("天元坐财：喜印食 畏官煞，喜月令旺 ")              
    if ('官' not in shens) and ('伤' not in shens) and ('食' not in shens):
        print("财旺生官:若月令财无损克，亦主登科")


    if cai_num > 2 and ('劫' not in shens) and ('比' not in shens) \
       and ('比' not in shens) and ('印' not in shens):
        print("财　不重叠多见　财多身弱，柱无印助; 若财多身弱，柱无印助不为福。")

    if '印' in shens:
        print("先财后印，反成其福，先印后财，反成其辱是也?")      
    if '官' in gan_shens:
        print("官星显露，别无伤损，或更食生印助日主健旺，富贵双全")          
    if '财' in gan_shens and (('劫' not in shens) and ('比' not in shens)):
        print("财不宜明露")  
    for seq, item in enumerate(gan_shens):
        if item == '财':
            if ten_deities[gans[seq]][zhis[seq]] == '墓':
                print("财星入墓，必定刑妻")  
            if ten_deities[gans[seq]][zhis[seq]] == '长':   
                print("财遇长生，田园万顷")  

    if ('官' not in shens) and (('劫' in shens) or ('比' in shens)):
        print("切忌有姊妹兄弟分夺，柱无官星，祸患百出。")

    if bi_num + jie_num > 1:
        print("兄弟辈出: 纵入官乡，发福必渺.")        

    for seq, item in enumerate(zhi_shens):
        if item == '才' or ten_deities[me][zhis[seq]] == '才':
            if get_empty(zhus[2],zhis[seq]):
                print("空亡 官将不成，财将不住")  

    print("-"*120)         

# 财库分析
if ten_deities[ten_deities[me].inverse["财"]]['库'][-1] in zhis:
    print("财临库墓: 一生财帛丰厚，因财致官, 天干透土更佳")   
if cai_num < 2 and (('劫' in shens) or ('比' in shens)):
    print("财少身强，柱有比劫，不为福")   




# 官分析
if ge == "官":
    print("\n**** 官分析 ****\n 喜:身旺 财印   忌：身弱 偏官 伤官 刑冲 泄气 贪合 入墓")
    print("一曰正官 二曰禄神 最忌刑冲破害、伤官七煞，贪合忘官，劫财比等等，遇到这些情况便成为破格 财印并存要分开")
    print("运：财旺印衰喜印，忌食伤生财；旺印财衰喜财，喜食伤生财；带伤食用印制；")
    print("带煞伤食不碍。劫合煞财运可行，伤食可行，身旺，印绶亦可行；伤官合煞，则伤食与财俱可行，而不宜逢印")
    print("======================================")  
    if guan_num > 1:
        print("官多变杀，以干为准")
    if "财" in shens and "印" in shens and ("伤" not in shens) and ("杀" not in shens):
        print("官星通过天干显露出来，又得到财、印两方面的扶持，四柱中又没有伤煞，行运再引到官乡，是大富大贵的命。")
    if "财" in shens or '才' in shens:
        print("有财辅助")       
    if "印" in shens or "枭" in shens:
        print("有印辅助　正官带伤食而用印制，运喜官旺印旺之乡，财运切忌。若印绶叠出，财运亦无害矣。")   
    if "食" in shens:
        print("又曰凡论官星，略见一位食神坐实，便能损局，有杀则无妨。惟月令隐禄，见食却为三奇之贵。因为食神和官相合。")    
    if "伤" in shens:
        print("伤官需要印或偏印来抑制，　有杀也无妨")         
    if "杀" in shens:
        print("伤官需要印或偏印来抑制。用劫合煞，则财运可行，伤食可行，身旺，印绶亦可行，只不过复露七煞。若命用伤官合煞，则伤食与财俱可行，而不宜逢印矣。")        

    if zhi_shens[2] in ("财","印"):
        print("凡用官，日干自坐财印，终显")           
    if zhi_shens[2] in ("伤","杀"):
        print("自坐伤、煞，终有节病")   



    # 检查天福贵人
    if (guan, ten_deities[guan].inverse['建']) in zhus:
        print("天福贵人:主科名巍峨，官职尊崇，多掌丝纶文翰之美!")

    # 天元坐禄    
    if guan in zhi5[zhis[2]]:
        print("天元作禄: 日主与官星并旺,才是贵命。大多不贵即富,即使是命局中有缺点,行到好的大运时,便能一发如雷。")
        print(tianyuans[ten_deities[me]['本']])         

    # 岁德正官
    if gan_shens[0] == '官' or zhi_shens[0] == '官':
        print("岁德正官: 必生宦族,或荫袭祖父之职,若月居财官分野,运向财官旺地,日主健旺,贵无疑矣。凡年干遇官,福气最重,发达必早。")    

    # 时上正官
    if gan_shens[0] == '官' or zhi_shens[0] == '官':
        print("时上正官: 正官有用不须多，多则伤身少则和，日旺再逢生印绶，定须平步擢高科。")        

    print()
    print("-"*120)  
# 官库分析
if ten_deities[ten_deities[me].inverse["官"]]['库'][-1] in zhis:
    print("官临库墓")   
    if lu_ku_cai[me] in zhis:
        print("官印禄库: 有官库，且库中有财")

# 杀(偏官)分析
if ge == "杀":
    print("\n杀(偏官)分析 **** 喜:身旺  印绶  合煞  食制 羊刃  比  逢煞看印及刃  以食为引   忌：身弱  财星  正官  刑冲  入墓")
    print("一曰偏官 二曰七煞 三曰五鬼 四曰将星 五曰孤极星 原有制伏,煞出为福,原无制伏,煞出为祸   性情如虎，急躁如风,尤其是七杀为丙、丁火时。")
    print("坐长生、临官、帝旺,更多带比同类相扶,则能化鬼为官,化煞为权,行运引至印乡,必发富贵。倘岁运再遇煞地,祸不旋踵。")
    print("七杀喜酒色而偏争好斗、爱轩昂而扶弱欺强")
    print("======================================")  
    if "财" in shens:
        print("逢煞看财,如身强煞弱,有财星则吉,身弱煞强,有财引鬼盗气,非贫则夭;")
    if "比" in shens:
        print("如果比比自己弱，可以先挨杀。")        
    if "食" in shens:
        print("有食神透制,即《经》云:一见制伏,却为贵本")   
        if "财" in shens or "印" in shens or '才' in shens or "枭" in shens:
            print("煞用食制，不要露财透印，以财能转食生煞，而印能去食护煞也。然而财先食后，财生煞而食以制之，或印先食后，食太旺而印制，则格成大贵。")   
    if "劫" in shens:
        print("有阳刃配合,即《经》云:煞无刃不显,逢煞看刃是也。")    
    if "印" in shens:
        print("印: 则煞生印，印生身")           
    if sha_num > 1:
        print("七煞重逢") 
        if weak:
            print("弃命从煞，须要会煞从财.四柱无一点比印绶方论，如遇运扶身旺，与煞为敌，从煞不专，故为祸患")
            print("阴干从地支，煞纯者多贵，以阴柔能从物也。阳干从地支，煞纯者亦贵，但次于阴，以阳不受制也。")
            print("水火金土皆从，惟阳木不能从，死木受斧斤，反遭其伤故也。")
            print("古歌曰：五阳坐日全逢煞，弃命相从寿不坚，如是五阴逢此地，身衰煞旺吉堪言。")            
    if "杀" == zhi_shens[2]:
        print("为人心多性急，阴险怀毒，僭伪谋害，不近人情")      
    if "杀" == zhi_shens[3] or "杀" == gan_shens[3]:
        print(" 时杀：月制干强，其煞反为权印。《经》云：时上偏官身要强，阳刃、冲刑煞敢当，制多要行煞旺运，煞多制少必为殃。")   
        print(" 一位为妙，年、月、日重见，反主辛苦劳碌。若身旺，煞制太过，喜行煞旺运，或三合煞运，如无制伏，要行制伏运方发。但忌身弱，纵得运扶持发福，运过依旧不济。")   
        print("《独步》云：时上一位，贵藏在支中，是日，主要旺强名利，方有气。")   
        print("《古歌》云：时上偏官喜刃冲，身强制伏禄丰隆。正官若也来相混，身弱财多主困穷。") 
        print("时上偏官一位强，日辰自旺喜非常。有财有印多财禄，定是天生作栋梁。") 
        print("煞临子位，必招悖逆之儿。")

    if "杀" == zhi_shens[0]:
        print(" 年上七煞：出身寒微，命有贵子。")   
        print("岁煞一位不宜制，四柱重见却宜制，日主生旺，制伏略多，喜行煞旺地，制伏太过，或煞旺身衰，官煞混杂，岁运如之，碌碌之辈。若制伏不及，运至身衰煞旺乡，必生祸患。")   
        print("《独步》云：时上一位，贵藏在支中，是日，主要旺强名利，方有气。")   
        print("《古歌》云：时上偏官喜刃冲，身强制伏禄丰隆。正官若也来相混，身弱财多主困穷。") 
        print("时上偏官一位强，日辰自旺喜非常。有财有印多财禄，定是天生作栋梁。")         
    if ('官' in shens) :
        print("官煞混杂：身弱多夭贫")

    for seq, item in enumerate(gan_shens):
        if item == '杀':
            if ten_deities[gans[seq]][zhis[seq]] == '长':   
                print("七煞遇长生乙位，女招贵夫。")  
    print()
    print("-"*120)      

# 印分析
if ge == "印":
    print("\n印分析 **** 喜:食神 天月德 七煞 逢印看煞 以官为引   忌： 刑冲 伤官 死墓 辰戊印怕木 丑未印不怕木")
    print("一曰正印 二曰魁星 三曰孙极星")
    print("以印绶多者为上,月最要,日时次之,年干虽重,须归禄月、日、时,方可取用,若年露印,月日时无,亦不济事。")
    print("======================================")  
    if "官" in shens:
        print("官能生印。身旺印强，不愁太过，只要官星清纯")      
    if "杀" in shens:
        print("喜七煞,但煞不可太多,多则伤身。原无七煞,行运遇之则发;原有七煞,行财运,或印绶死绝,或临墓地,皆凶。")    
    if "伤" in shens or "食" in shens:
        print("伤食：身强印旺，恐其太过，泄身以为秀气；若印浅身轻，而用层层伤食，则寒贫之局矣。")     
    if "财" in shens or "才" in shens:
        print("有印多而用财者，印重身强，透财以抑太过，权而用之，只要根深，无防财破。 若印轻财重，又无劫财以救，则为贪财破印，贫贱之局也。")             

    if yin_num > 1:
        print("印绶复遇拱禄、专禄、归禄、鼠贵、夹贵、时贵等格,尤为奇特,但主少子或无子,印绶多者清孤。")  
    if "劫" in shens:
        print("化印为劫；弃之以就财官")              
    print()
    print("-"*120)         
    
# 偏印分析
if ge == "枭":
    print("\n印分析 **** 喜:食神 天月德 七煞 逢印看煞 以官为引   忌： 刑冲 伤官 死墓 辰戊印怕木 丑未印不怕木")
    print("一曰正印 二曰魁星 三曰孙极星")
    print("以印绶多者为上,月最要,日时次之,年干虽重,须归禄月、日、时,方可取用,若年露印,月日时无,亦不济事。")
    print("======================================")  
    if "官" in shens:
        print("官能生印。身旺印强，不愁太过，只要官星清纯")      
    if "杀" in shens:
        print("喜七煞,但煞不可太多,多则伤身。原无七煞,行运遇之则发;原有七煞,行财运,或印绶死绝,或临墓地,皆凶。")    
    if "伤" in shens or "食" in shens:
        print("伤食：身强印旺，恐其太过，泄身以为秀气；若印浅身轻，而用层层伤食，则寒贫之局矣。")     
    if "财" in shens or "才" in shens:
        print("弃印就财。")             

    if yin_num > 1:
        print("印绶复遇拱禄、专禄、归禄、鼠贵、夹贵、时贵等格,尤为奇特,但主少子或无子,印绶多者清孤。")  
    if "劫" in shens:
        print("化印为劫；弃之以就财官")              
    print()
    print("-"*120)         



gan_ = tuple(gans)
for item in Gan:
    if gan_.count(item) == 3:
        print("三字干：", item, "--", gan3[item])
        break

gan_ = tuple(gans)
for item in Gan:
    if gan_.count(item) == 4:
        print("四字干：", item, "--", gan4[item])
        break    

zhi_ = tuple(zhis)
for item in Zhi:
    if zhi_.count(item) > 2:
        print("三字支：", item, "--", zhi3[item])
        break

print("="*120)  
print("你属:", me, "特点：--", gan_desc[me],"\n")
print("年份:", zhis[0], "特点：--", zhi_desc[zhis[0]],"\n")





# 羊刃分析
key = '帝' if Gan.index(me)%2 == 0 else '冠'

if ten_deities[me].inverse[key] in zhis:
    print("\n羊刃:", me, ten_deities[me].inverse[key])  
    print("======================参考：https://www.jianshu.com/p/c503f7b3ed04")  
    if ten_deities[me].inverse['冠']:
        print("羊刃重重又见禄，富贵饶金玉。 官、印相助福相资。")  
    else:
        print("劳累命！")




# 将星分析
me_zhi = zhis[2]
other_zhis = zhis[:2] + zhis[3:]
flag = False
tmp_list = []
if me_zhi in ("申", "子", "辰"):
    if "子" in other_zhis:
        flag = True
        tmp_list.append((me_zhi, '子'))
elif me_zhi in ("丑", "巳", "酉"):
    if "酉" in other_zhis:
        flag = True   
        tmp_list.append((me_zhi, '酉'))
elif me_zhi in ("寅", "午", "戌"):
    if "午" in other_zhis:
        flag = True     
        tmp_list.append((me_zhi, '午'))
elif me_zhi in ("亥", "卯", "未"):
    if "卯" in other_zhis:
        flag = True   
        tmp_list.append((me_zhi, '卯'))

if flag:
    print("\n\n将星: 常欲吉星相扶，贵煞加临乃为吉庆。")  
    print("=========================")   
    print('''理愚歌》云：将星若用亡神临，为国栋梁臣。言吉助之为贵，更夹贵库墓纯粹而
    不杂者，出将入相之格也，带华盖、正印而不夹库，两府之格也；只带库墓而带正印，员郎
    以上，既不带墓又不带正印，止有华盖，常调之禄也；带华印而正建驿马，名曰节印，主旌节
    之贵；若岁干库同库为两重福，主大贵。''')
    print(tmp_list)

# 华盖分析
flag = False
if me_zhi in ("申", "子", "辰"):
    if "辰" in other_zhis:
        flag = True
elif me_zhi in ("丑", "巳", "酉"):
    if "丑" in other_zhis:
        flag = True   
elif me_zhi in ("寅", "午", "戌"):
    if "戌" in other_zhis:
        flag = True     
elif me_zhi in ("亥", "卯", "未"):
    if "未" in other_zhis:
        flag = True   

if flag:
    print("\n\n华盖: 多主孤寡，总贵亦不免孤独，作僧道艺术论。")  
    print("=========================")   
    print('''《理愚歌》云：华盖虽吉亦有妨，或为孽子或孤孀。填房入赘多阙口，炉钳顶笠拔缁黄。
    又云：华盖星辰兄弟寡，天上孤高之宿也；生来若在时与胎，便是过房庶出者。''')    


# 咸池 桃花
flag = False
taohuas = []
year_zhi = zhis[0]
if me_zhi in ("申", "子", "辰") or year_zhi in ("申", "子", "辰"):
    if "酉" in zhis:
        flag = True
        taohuas.append("酉")
elif me_zhi in ("丑", "巳", "酉") or year_zhi in ("丑", "巳", "酉"):
    if "午" in other_zhis:
        flag = True   
        taohuas.append("午")
elif me_zhi in ("寅", "午", "戌") or year_zhi in ("寅", "午", "戌"):
    if "卯" in other_zhis:
        flag = True    
        taohuas.append("卯")
elif me_zhi in ("亥", "卯", "未") or year_zhi in ("亥", "卯", "未"):
    if "子" in other_zhis:
        flag = True   
        taohuas.append("子")

if flag:
    print("\n\n咸池(桃花): 墙里桃花，煞在年月；墙外桃花，煞在日时；")  
    print("=========================")   
    print('''一名败神，一名桃花煞，其神之奸邪淫鄙，如生旺则美容仪，耽酒色，疏财好欢，
    破散家业，唯务贪淫；如死绝，落魄不检，言行狡诈，游荡赌博，忘恩失信，私滥奸淫，
    靡所不为；与元辰并，更临生旺者，多得匪人为妻；与贵人建禄并，多因油盐酒货得生，
    或因妇人暗昧之财起家，平生有水厄、痨瘵之疾，累遭遗失暗昧之灾。此人入命，有破无成，
    非为吉兆，妇人尤忌之。
    咸池非吉煞，日时与水命遇之尤凶。''')  
    print(taohuas, zhis)

# 禄分析
flag = False
for item in zhus:
    if item in lu_types[me]:
        if not flag:
            print("\n\n禄分析:")  
            print("=========================")	    
        print(item,lu_types[me][item])
 

# 文星贵人
if wenxing[me] in zhis:
    print("文星贵人: ", me,  wenxing[me])  

# 天印贵人
if tianyin[me] in zhis:
    print("天印贵人: 此号天印贵，荣达受皇封", me,  tianyin[me])  


short = min(scores, key=scores.get)
print("\n\n五行缺{}的建议参见 http://t.cn/E6zwOMq".format(short))    

    
    
print("======================================")  
if '杀' in shens:
    if yinyang(me) == '+':
        print("阳杀:话多,热情外向,异性缘好")
    else:
        print("阴杀:话少,性格柔和")
if '印' in shens and '才' in shens and '官' in shens:
    print("印,偏财,官:三奇 怕正财")
if '才' in shens and '杀' in shens:
    print("男:因女致祸、因色致祸; 女:赔货")
    
if '才' in shens and '枭' in shens:
    print("偏印因偏财而不懒！")    
    
