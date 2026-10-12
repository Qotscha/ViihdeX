# Copyright (c) 2026 Qotscha

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
import configparser
import locale
import os
import platform
import re
import sys
import warnings
import xml.etree.ElementTree as ET
from subprocess import Popen
import requests
import langcodes
from pycaption import DFXPReader, SRTWriter

from bs4 import XMLParsedAsHTMLWarning
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

if os.name == 'nt':
    os.system('color')

finnish = bool(locale.getlocale()[0].split('_')[0] == 'Finnish')

def is_best_variant(b, w, h, cb, mb, mw, mh):
    if (mb and b > mb) or (mw and w > mw) or (mh and h > mh):
        return False
    elif b > cb:
        return True
    else:
        return False

def get_language(lang_code):
    lang = langcodes.Language.get(lang_code)
    return lang

def get_iso(language, to_iso = True, iso = 'alpha_3b'):
    if not to_iso and '-' in str(language):
        lcode = str(language)
    elif iso == 'alpha_2':
        lcode = language.language
    elif iso == 'alpha_3':
        lcode = langcodes.Language.get(language).to_alpha3(variant='t')
    elif iso == 'alpha_3b':
        lcode = langcodes.Language.get(language).to_alpha3(variant='b')
    return lcode

def lang_in_langs(lang, langs):
    l = False
    for x in langs:
        if lang.language == x.language:
            fields = [k for k, v in vars(x).items() if not k.startswith('_') and v is not None]
            l = True
            for f in fields:
                if lang[f] != x[f]:
                    l = False
                    break
    return l

def list_tracks(available, wanted, default_list, dl_always = False):
    dl_list = []
    defaults = []
    if wanted:
        for x in wanted:
            for y in available:
                if lang_in_langs(y, [x]):
                    dl_list.append(y)
    else:
        for x in default_list:
            for y in available:
                if lang_in_langs(y, [x]):
                    dl_list.append(y)
        dl_list += [x for x in available if not lang_in_langs(x, default_list)]

    for x in default_list:
        default_found = False
        if dl_always and not dl_list:
            for y in available:
                if lang_in_langs(y, [x]):
                    dl_list.append(y)
                    defaults.append(y)
                    default_found = True
            if default_found:
                break
        else:
            for y in dl_list:
                if lang_in_langs(y, [x]):
                    defaults.append(y)
                    default_found = True
            if default_found:
                break
    if dl_always and not dl_list:
        dl_list = [available[0]]
    return dl_list, defaults

def is_hi_sub(name):
    sub_names = ['ohjelmatekstitys', 'hard of hearing']
    for x in sub_names:
        if x in name:
            return True
    else:
        return False

def download_sub(name, sub_url, tl):
    srt = ''
    for i, t in enumerate(range (int(tl['t']), (int(tl['r']) + 1) * int(tl['d']), int(tl['d']))):
        r = requests.get(sub_url.replace('$Time$', str(t)))
        frag = r.content.decode(encoding = 'utf-8', errors = 'ignore')
        d = frag.split('mdat', 1)[1]
        # print(t)
        # print(d)
        try:
            ttml = DFXPReader().read(d)
        except:
            continue
        sr = SRTWriter().write(ttml)
        srt += sr
        srt += '\n'

    j = 1
    sl = srt.splitlines()
    sl.pop()
    pattern = r"^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$"
    for i, l in enumerate(sl):
        if l.isdigit() and bool(re.fullmatch(pattern, sl[i+1].strip())):
            sl[i] = l.replace(l, str(j))
            j += 1

    with open (name, 'w', encoding="utf-8") as f:
        f.writelines(line + '\n' for line in sl)
    if finnish:
        print('Tekstitys ladattu.')
    else:
        print('Subtitle downloaded')

def create_config(config_path, config = None, write_config = True):
    config_changed = False
    default_config = configparser.ConfigParser()
    default_config['Download settings'] = { 'audio languages': '',
                                            'subtitle languages': '',
                                            'default audio': '',
                                            'default subtitle': '',
                                            'visual impaired': '',
                                            'hearing impaired': '',
                                            'maximum bandwidth': '0',
                                            'maximum width': '0',
                                            'maximum height': '0',
                                            'file extension': 'mkv',
                                            'external subtitles': 'true',
                                            'RFC 5646 to ISO 639': 'true',
                                            'ISO 639': 'alpha_3b',
                                            'ffmpeg options': '-v error -stats',
                                            'ffmpeg video codec': 'copy',
                                            'ffmpeg audio codec': 'copy',
                                            'overwrite': 'false',
                                            'never overwrite': 'false' }
    default_config['Headers'] = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0'}
    if not config:
        config = default_config
        config_changed = True
    else:
        if 'Download settings' in config:
            for k in default_config['Download settings']:
                if k in config['Download settings']:
                    default_config['Download settings'][k] = config['Download settings'][k]
                else:
                    config_changed = True
        else:
            config_changed = True
        if 'Headers' in config:
            if not 'User-Agent' in config['Headers']:
                config_changed = True
            for k in config['Headers']:
                default_config['Headers'][k] = config['Headers'][k]
        else:
            config_changed = True
    if write_config and config_changed:
        if not os.path.exists(config_path):
            os.makedirs(config_path)
        with open(os.path.join(config_path, 'settings.ini'), 'w') as configfile:
            default_config.write(configfile)
    return default_config

def main():
    # Read arguments
    parser = argparse.ArgumentParser(description='Download HLS streams.')
    parser.add_argument('url', metavar='URL', help='stream URL')
    parser.add_argument('filename', metavar='OUTPUT', help='output file')
    parser.add_argument('-v', '--verbose', help='print FFmpeg command', action='store_true')
    parser.add_argument('-c', '--config', help='config file', metavar='CONFIG FILE')
    parser.add_argument('-s', '--subonly', help='download subtitles only', action='store_true')
    parser.add_argument('-e', '--extsubs', help='download subtitles to external files', action='store_true')
    parser.add_argument('-m', '--muxsubs', help='mux subtitles to video file', action='store_true')
    parser.add_argument('-a', '--audio', help='audio languages, e.g. \"fin, en\"', metavar='AUDIO LANGUAGES', default=None)
    parser.add_argument('-u', '--subtitles', help='subtitle languages', default=None)
    parser.add_argument('-b', '--begin', help='start live stream from the first segment', action='store_true')
    parser.add_argument('-l', '--live_start_index', help='start live stream from segment', default=None)
    parser.add_argument('-mw', '--max_width', help='maximum video width in pixels', default=None)
    parser.add_argument('-mh', '--max_height', help='maximum video height in pixels', default=None)
    parser.add_argument('-mb', '--max_bitrate', help='maximum video bitrate (bps)', default=None)
    parser.add_argument('-r', '--variant', help='select variant', default=None)
    parser.add_argument('-y', '--overwrite', help='overwrite output files without asking', action='store_true')
    parser.add_argument('-n', '--never', help='never overwrite existing files', action='store_true')
    # parser.add_argument('-f', '--ffmpeg_options', help='ffmpeg general and input options', default=None)
    args = parser.parse_args()

    # Load config
    if os.name == 'nt':
        config_path = os.path.join(os.environ['APPDATA'], 'viihdexdl')
    elif os.name == 'posix' and sys.platform != 'darwin':
        config_path = os.path.join(os.path.expanduser('~/.config'), 'viihdexdl')
    if not args.config:
        if not os.path.exists(os.path.join(config_path, 'settings.ini')):
            config = create_config(config_path)
        else:
            config = configparser.ConfigParser()
            config.read(os.path.join(config_path, 'settings.ini'))
            config = create_config(config_path, config)
    else:
        config = configparser.ConfigParser()
        config.read(args.config)
        config = create_config(config_path, config, False)
    dl_settings = config['Download settings']
    headers = config['Headers']
    ffmpeg_ua = f' -user_agent "{headers['User-Agent']}"' if headers.get('User-Agent') else ''

    recording_url = args.url
    filename = args.filename
    sub_only = args.subonly
    ext_subs = args.extsubs if args.extsubs else dl_settings.getboolean('external subtitles')
    if args.muxsubs:
        ext_subs = False
    if dl_settings.getboolean('overwrite') or args.overwrite:
        dl_settings['ffmpeg options'] = dl_settings['ffmpeg options'] + ' ' + '-y'
    if dl_settings.getboolean('never overwrite') or args.never:
        dl_settings['ffmpeg options'] = dl_settings['ffmpeg options'] + ' ' + '-n'
    if args.begin:
        dl_settings['ffmpeg options'] = dl_settings['ffmpeg options'] + ' ' + '-live_start_index 0'
    elif args.live_start_index:
        dl_settings['ffmpeg options'] = dl_settings['ffmpeg options'] + ' ' + '-live_start_index ' + args.live_start_index

    # if args.ffmpeg_options:
        # dl_settings['ffmpeg_options'] = dl_settings['ffmpeg_options'] + ' ' + args.ffmpeg_options

    dl_settings['audio languages'] = args.audio if args.audio else dl_settings['audio languages']
    dl_settings['subtitle languages'] = args.subtitles if args.subtitles else dl_settings['subtitle languages']
    to_iso = dl_settings.getboolean('RFC 5646 to ISO 639') if 'RFC 5646 to ISO 639' in dl_settings else True
    iso = dl_settings['ISO 639'] if 'ISO 639' in dl_settings else 'alpha_3b'

    if filename.endswith('.mkv'):
        dl_settings['file extension'] = 'mkv'
        filename = filename[:-4]
    elif filename.endswith('.mp4'):
        dl_settings['file extension'] = 'mp4'
        filename = filename[:-4]

    # Download DASH manifest
    get_playlist = requests.get(recording_url, headers = headers)

    ns = {'mpd':'urn:mpeg:dash:schema:mpd:2011'}
    root = ET.fromstring(get_playlist.text).find('mpd:Period', ns)
    aset = root.findall('mpd:AdaptationSet', ns)

    # Parse manifest and create FFmpeg command
    recording_url = get_playlist.url
    hls_url = recording_url.rsplit('.mpd', 1)[0].rsplit('/', 1)[0]
    av_audio = []
    audio_dict = {}
    audio_count = {}
    audio_metadata = ''
    av_subs = []
    sub_dict = {}
    wanted_audio = [] if not dl_settings['audio languages'] else [get_language(x.strip()) for x in dl_settings['audio languages'].split(',')]
    wanted_subs = [] if not dl_settings['subtitle languages'] else [get_language(x.strip()) for x in dl_settings['subtitle languages'].split(',')]
    default_audio_list = [] if not dl_settings['default audio'] else [get_language(x.strip()) for x in dl_settings['default audio'].split(',')]
    default_sub_list = [] if not dl_settings['default subtitle'] else [get_language(x.strip()) for x in dl_settings['default subtitle'].split(',')]
    visual_impaired = None if (not dl_settings['visual impaired'] or dl_settings['file extension'] == 'mp4') else get_language(dl_settings['visual impaired'])
    hearing_impaired = None if (not dl_settings['hearing impaired'] or dl_settings['file extension'] == 'mp4') else get_language(dl_settings['hearing impaired'])
    variant = 0
    avar = 0
    for x in ['maximum bandwidth', 'maximum width', 'maximum height']:
        if not dl_settings[x]:
            dl_settings[x] = '0'
    max_bw = 0
    max_dl_bw = int(args.max_bitrate) if args.max_bitrate else int(dl_settings['maximum bandwidth'])
    max_width = 0
    max_dl_width = int(args.max_width) if args.max_width else int(dl_settings['maximum width'])
    max_height = 0
    max_dl_height = int(args.max_height) if args.max_height else int(dl_settings['maximum height'])
    if sub_only:
        cmd = ''
        for x in aset:
            if x.get('contentType') == 'text':
                l = x.get('lang').strip('"')
                lang = get_language(l)
                if not lang_in_langs(lang, av_subs):
                    sub_uri = x.find('mpd:SegmentTemplate', ns).get('media')
                    sub_uri = sub_uri.replace('$RepresentationID$', x.find('mpd:Representation', ns).get('id'))
                    if not (sub_uri.startswith('http://') or sub_uri.startswith('https://')):
                        sub_uri = hls_url + '/dash/' + sub_uri
                    timeline = x.find('mpd:SegmentTemplate', ns).find('mpd:SegmentTimeline', ns).find('mpd:S', ns).attrib
                    av_subs.append(lang)
                    sub_dict[lang] = [sub_uri, timeline]
        print(sub_dict)
        if not sub_dict:
            if finnish:
                print('Tekstityksiä ei löytynyt.')
            else:
                print('No subtitles found.')
        else:
            sub = list_tracks(av_subs, wanted_subs, default_sub_list, True)[0][0]
            complete_filename = filename + '.' + get_iso(sub, to_iso, iso) + '.srt'
            if finnish:
                print('Aloitetaan tekstityksen \033[32m' + complete_filename + '\033[39m lataus.\n')
            else:
                print('Starting downloading subtitle \033[32m' + complete_filename + '\033[39m.\n')
            download_sub(complete_filename, sub_dict[sub][0], sub_dict[sub][1])

    else:
        for a in aset:
            # Parse available variants
            if a.get('contentType') == 'video':
                rep = a.findall('mpd:Representation', ns)
                for x in rep:
                    bandwidth = int(x.get('bandwidth'))
                    resolution = [int(x.get('width')), int(x.get('height'))]
                    # print(bandwidth)
                    # print(resolution)
                    if (args.variant is not None and variant == int(args.variant) or (not args.variant and
                        is_best_variant(bandwidth, resolution[0], resolution[1], max_bw, max_dl_bw, max_dl_width, max_dl_height))):
                        best_variant = variant
                        try:
                            audio_tracks = True
                            audio_group = x.split('AUDIO=', 1)[1].split(',', 1)[0]
                        except:
                            audio_tracks = False
                        try:
                            sub_tracks = True
                            sub_group = x.split('SUBTITLES=', 1)[1].split(',', 1)[0]
                        except:
                            sub_tracks = False
                        max_bw = bandwidth
                        max_width = resolution[0]
                        max_height = resolution[1]
                    variant += 1
        mappings = ' -map 0:v:' + str(best_variant)
        # print(mappings)

        for x in aset:
            # Parse available audio tracks
            if x.get('contentType') == 'audio':
                try:
                    l = x.get('lang')
                    lang = get_language(l)
                    rep = x.find('mpd:Representation', ns)
                    bandwidth = int(rep.get('bandwidth'))
                    if not lang_in_langs(lang, av_audio):
                        av_audio.append(lang)
                        audio_dict[lang] = [avar, bandwidth]
                        audio_count[lang] = 1
                    else:
                        if bandwidth > audio_dict[lang][1]:
                            audio_dict[lang] = [avar, bandwidth]
                    avar += 1
                except:
                    pass

            # Parse available subtitle tracks
            elif x.get('contentType') == 'text':
                l = x.get('lang')
                lang = get_language(l)
                n = ''
                sub_uri = x.find('mpd:SegmentTemplate', ns).get('media')
                sub_uri = sub_uri.replace('$RepresentationID$', x.find('mpd:Representation', ns).get('id'))
                if not (sub_uri.startswith('http://') or sub_uri.startswith('https://')):
                    sub_uri = hls_url + '/dash/' + sub_uri
                timeline = x.find('mpd:SegmentTemplate', ns).find('mpd:SegmentTimeline', ns).find('mpd:S', ns).attrib
                if not lang_in_langs(lang, av_subs):
                    av_subs.append(lang)
                    sub_dict[lang] = [([sub_uri, timeline], is_hi_sub(n), get_iso(lang, to_iso, iso))]
                else:
                    sub_dict[lang].append(([sub_uri, timeline], is_hi_sub(n), get_iso(lang, to_iso, iso)))

        # Create FFmpeg command
        if not av_audio:
            mappings += ' -map 0:a:0'
            audio_list = None
        else:
            audio_list, default_audio = list_tracks(av_audio, wanted_audio, default_audio_list, True)
            a = 0
            for i, x in enumerate(audio_list):
                mappings += ' -map 0:a:' + str(audio_dict[x][0])
                for j in range(audio_count[x]):
                    audio_metadata += ' -metadata:s:a:' + str(i+a) + ' language=' + get_iso(x, to_iso, iso)
                    a += 1
                a -= 1
                if x in default_audio:
                    audio_metadata += ' -disposition:a:' + str(i+a) + ' default'
                    if x == visual_impaired:
                        audio_metadata += '+visual_impaired'
                elif x == visual_impaired:
                    audio_metadata += ' -disposition:a:' + str(i+a) + ' visual_impaired'
        if av_subs:
            sub_list, default_sub = list_tracks(av_subs, wanted_subs, default_sub_list)
            if ext_subs:
                dl = {}
                dl_hi = {}
                for x in sub_list:
                    for y in sub_dict[x]:
                        if y[1]:
                            if not dl_hi.get(y[2]):
                                complete_filename = filename + '.' + y[2] + '.HI.srt'
                                dl_hi[y[2]] = 1
                            else:
                                complete_filename = filename + '.' + y[2] + '.HI.(' + str(dl_hi[y[2]]) + ')' + '.srt'
                                dl_hi[y[2]] += 1
                        else:
                            if not dl.get(y[2]):
                                complete_filename = filename + '.' + y[2] + '.srt'
                                dl[y[2]] = 1
                            else:
                                complete_filename = filename + '.' + y[2] + '.(' + str(dl[y[2]]) + ')' + '.srt'
                                dl[y[2]] += 1
                        if finnish:
                            print('Aloitetaan tekstityksen \033[32m' + complete_filename + '\033[39m lataus.\n')
                        else:
                            print('Starting downloading subtitle \033[32m' + complete_filename + '\033[39m.\n')
                        download_sub(complete_filename, y[0][0], y[0][1])
                        print()
            else:
                if finnish:
                    print('Ainoastaan erilliset tekstitystiedostot ovat tuettuja.')
                else:
                    print('Only external subtitles are supported')

        cmd = ( 'ffmpeg ' + dl_settings['ffmpeg options'] + ffmpeg_ua + ' -i \"' + recording_url + '\"' + mappings
                + ' -c:v ' + dl_settings['ffmpeg video codec'] + ' -c:a ' + dl_settings['ffmpeg audio codec']
                + audio_metadata + ' \"' + filename + '.' + dl_settings['file extension'] + '\"' )

    # Launch FFmpeg
        if finnish:
            print('Aloitetaan tallenteen \033[92m' + filename + '.' + dl_settings['file extension'] + '\033[39m lataus.')
        else:
            print('Starting downloading \033[92m' + filename + '.' + dl_settings['file extension'] + '\033[39m.')
        print(f'Video: {max_bw} bps, {max_width}x{max_height}')
        if not audio_list:
            if finnish:
                print('Ladattava ääniraita: (nimetön)')
            else:
                print('Audio track to download: (undefined)')
        else:
            if finnish:
                print('Ladattavat ääniraidat: ' + ', '.join([get_iso(x, to_iso, iso) for x in audio_list]))
            else:
                print('Audio tracks to download: ' + ', '.join([get_iso(x, to_iso, iso) for x in audio_list]))
        if not ext_subs:
            if not sub_tracks:
                if finnish:
                    print('Ei tekstityksiä')
                else:
                    print('No subtitles')
            else:
                if finnish:
                    print('Ladattavat tekstitysraidat: ' + sub_string[:-2])
                else:
                    print('Subtitle tracks to download: ' + sub_string[:-2])
        print()
        if args.verbose:
            print(cmd)
            print()
        Popen(cmd, shell=True).wait()

if __name__ == "__main__":
    main()
