﻿function vlcGetPath(){var a=regGetHKLMPath("SOFTWARE\\VideoLAN\\VLC");if(a==""){a=regGetHKLMPath("SOFTWARE\\Wow6432Node\\VideoLAN\\VLC")}return a}function regGetHKLMPath(b){var e=GetObject("winmgmts:{impersonationLevel=impersonate}!\\\\.\\root\\default:StdRegProv");var d=e.Methods_.Item("GetStringValue");var a=d.InParameters.SpawnInstance_();a.hDefKey=2147483650;a.sSubKeyName=b;a.sValueName="";var c=e.ExecMethod_(d.Name,a);if(c.ReturnValue==0){return c.sValue}else{return""}};