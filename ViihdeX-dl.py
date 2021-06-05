# Copyright (c) 2021 Qotscha

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

import configparser
import requests
import pycountry
import sys
from subprocess import Popen

def getLanguage(langCode):
    if len(langCode) == 2:
        lang = pycountry.languages.get(alpha_2=langCode)
    elif len(langCode) == 3:
        lang = pycountry.languages.get(bibliographic=langCode)
        if not lang:
            lang = pycountry.languages.get(alpha_3=langCode)
    else:
        lang = pycountry.languages.lookup(langCode)
    return lang

def getBibliographic(language):
    try:
        bibl = language.bibliographic
    except:
        bibl = language.alpha_3
    return bibl

# Load config
config = configparser.ConfigParser()
config.read('dlsettings.ini')
dlSettings = config['Download settings']

# Read arguments
recordingUrl = sys.argv[1]
filename = sys.argv[2]
subOnly = False
extSubs = False
if len(sys.argv) > 3:
    if sys.argv[3] == '-s':
        subOnly = True
    elif sys.argv[3] == '-e':
        extSubs = True

# Download HLS master playlist
getPlaylist = requests.get(recordingUrl)

# Parse playlist and create FFmpeg command
playlistLines = getPlaylist.text.splitlines()
recordingUrl = getPlaylist.url
hlsUrl = recordingUrl.rsplit('/',1)[0]
audioList = []
audioListISO = []
audioMetadata = ''
subList = []
subInputs = ''
subMappings = ''
subMetadata = ''
wantedAudio = [] if not dlSettings['audio languages'] else [getLanguage(x.strip()) for x in dlSettings['audio languages'].split(',')]
wantedSubs = [] if not dlSettings['subtitle languages'] else [getLanguage(x.strip()) for x in dlSettings['subtitle languages'].split(',')]
defaultAudio = None if not dlSettings['default audio'] else getLanguage(dlSettings['default audio'])
defaultSubtitle = None if not dlSettings['default subtitle'] else getLanguage(dlSettings['default subtitle'])
visualImpaired = None if not dlSettings['visual impaired'] else getLanguage(dlSettings['visual impaired'])
hearingImpaired = None if not dlSettings['hearing impaired'] else getLanguage(dlSettings['hearing impaired'])
variant = 0
subtitles = 0
maxBw = 0
maxDlBw = 0 if not dlSettings['maximum bandwidth'] else int(dlSettings['maximum bandwidth'])
if subOnly:
    cmd = ''
    for x in playlistLines:
        if x.startswith('#EXT-X-MEDIA:TYPE=SUBTITLES'):
            l = x.split('LANGUAGE=', 1)[1].split(',', 1)[0].strip('"')
            lang = getLanguage(l)
            if not wantedSubs or lang in wantedSubs:
                subUri = x.rsplit('URI=', 1)[1].strip('"')
                if not (subUri.startswith('http://') or subUri.startswith('https://')):
                    subUri = hlsUrl + '/' + subUri
                if not wantedSubs or lang == wantedSubs[0]:
                    completeFilename = filename + '.' + getBibliographic(lang) + '.srt'
                    cmd = 'ffmpeg ' + dlSettings['ffmpeg options'] + ' -i \"' + subUri + '\" -c:s subrip \"' + completeFilename + '\"'
                    print('Aloitetaan tekstityksen ' + completeFilename + ' lataus.\n')
                    break
    Popen(cmd).wait()

else:
    for x in playlistLines:
        if x.startswith('#EXT-X-MEDIA:TYPE=AUDIO'):
            l = x.split('LANGUAGE=', 1)[1].split(',', 1)[0].strip('"')
            lang = getLanguage(l)
            if (not wantedAudio or lang in wantedAudio) and lang not in audioList:
                audioList.append(lang)
                audioListISO.append(l)
        elif x.startswith('#EXT-X-MEDIA:TYPE=SUBTITLES'):
            l = x.split('LANGUAGE=', 1)[1].split(',', 1)[0].strip('"')
            lang = getLanguage(l)
            if not wantedSubs or lang in wantedSubs:
                subUri = x.rsplit('URI=', 1)[1].strip('"')
                if not (subUri.startswith('http://') or subUri.startswith('https://')):
                    subUri = hlsUrl + '/' + subUri
                if extSubs:
                    completeFilename = filename + '.' + getBibliographic(lang) + '.srt'
                    subCmd = 'ffmpeg ' + dlSettings['ffmpeg options'] + ' -i \"' + subUri + '\" -c:s subrip \"' + completeFilename + '\"'
                    print('Aloitetaan tekstityksen ' + completeFilename + ' lataus.\n')
                    Popen(subCmd).wait()
                    print()
                else:
                    subInputs += ' -i \"' + subUri + '\"'
                    subList.append(lang)
                    subMappings += ' -map ' + str(subtitles + 1) + ':s'
                    subMetadata += ' -metadata:s:s:' + str(subtitles) + ' language=' + getBibliographic(lang)
                    if lang == defaultSubtitle:
                        subMetadata += ' -disposition:s:' + str(subtitles) + ' default'
                    elif lang == hearingImpaired:
                        subMetadata += ' -disposition:s:' + str(subtitles) + ' hearing_impaired'
                    subtitles += 1
        elif x.startswith('#EXT-X-STREAM-INF:'):
            bandwidth = int(x.split('BANDWIDTH=', 1)[1].split(',', 1)[0])
            # print(bandwidth)
            if (not maxDlBw or bandwidth < maxDlBw) and bandwidth > maxBw:
                bestVariant = variant
                maxBw = bandwidth
            variant += 1
    mappings = ' -map 0:p:' + str(bestVariant) + ':v'
    if not audioList:
        mappings += ' -map 0:p:' + str(bestVariant) + ':a'
    else:
        for audio, x in enumerate(audioList):
            mappings += ' -map 0:p:' + str(bestVariant) + ':a:m:language:' + audioListISO[audio]
            audioMetadata += ' -metadata:s:a:' + str(audio) + ' language=' + getBibliographic(x)
            if x == defaultAudio:
                audioMetadata += ' -disposition:a:' + str(audio) + ' default'
            elif x == visualImpaired:
                audioMetadata += ' -disposition:a:' + str(audio) + ' visual_impaired'
    if dlSettings['file extension'] == 'mp4':
        subCodec = ' -c:s mov_text'
    else:
        subCodec = ' -c:s subrip'
    filename += '.' + dlSettings['file extension']
    cmd = ( 'ffmpeg ' + dlSettings['ffmpeg options'] + ' -i \"' + recordingUrl + '\"' + subInputs + mappings + subMappings
            + ' -c:v ' + dlSettings['ffmpeg video codec'] + ' -c:a ' + dlSettings['ffmpeg audio codec'] + subCodec
            + audioMetadata + subMetadata + ' \"' + filename + '\"' )

# Launch FFmpeg
    print('Aloitetaan tallenteen ' + filename + ' lataus.')
    print('Ladattavat ääniraidat: ' + ', '.join([getBibliographic(x) for x in audioList]))
    print('Ladattavat tekstitysraidat: ' + ', '.join([getBibliographic(x) for x in subList]))
    print()
    print(cmd)
    print()
    Popen(cmd).wait()