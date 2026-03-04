/*
    ThreatScan — Suspicious Indicator Rules
    Author: ThreatScan Team
    Version: 1.0
    Description: Rules for detecting suspicious but not necessarily malicious patterns
*/

rule Suspicious_Base64_Blob : medium
{
    meta:
        description = "Detects large Base64-encoded blobs (possible encoded payload)"
        author = "ThreatScan"
        severity = "medium"

    strings:
        $b64 = /[A-Za-z0-9+\/]{100,}={0,2}/ ascii

    condition:
        #b64 > 3
}

rule Suspicious_Script_Obfuscation : medium
{
    meta:
        description = "Detects common script obfuscation patterns"
        author = "ThreatScan"
        severity = "medium"

    strings:
        $chr1 = "chr(" ascii nocase
        $chr2 = "String.fromCharCode" ascii nocase
        $chr3 = "charCodeAt" ascii nocase
        $eval1 = "eval(" ascii nocase
        $eval2 = "Execute(" ascii nocase
        $eval3 = "ExecuteGlobal" ascii nocase
        $replace = ".replace(" ascii nocase
        $split = ".split(" ascii nocase
        $reverse = ".reverse()" ascii nocase
        $unescape = "unescape(" ascii nocase

    condition:
        3 of them
}

rule Suspicious_Network_Indicators : medium
{
    meta:
        description = "Detects network-related API calls and strings"
        author = "ThreatScan"
        severity = "medium"

    strings:
        $ws1 = "WSAStartup" ascii
        $ws2 = "InternetOpenUrl" ascii
        $ws3 = "HttpSendRequest" ascii
        $ws4 = "URLDownloadToFile" ascii
        $ws5 = "InternetOpen" ascii
        $ws6 = "InternetConnect" ascii
        $ws7 = "HttpOpenRequest" ascii

        $ua = "User-Agent:" ascii nocase

    condition:
        uint16(0) == 0x5A4D and
        (3 of ($ws*) or (2 of ($ws*) and $ua))
}

rule Suspicious_Anti_Analysis : high
{
    meta:
        description = "Detects anti-analysis / anti-debugging techniques"
        author = "ThreatScan"
        severity = "high"

    strings:
        $dbg1 = "IsDebuggerPresent" ascii
        $dbg2 = "CheckRemoteDebuggerPresent" ascii
        $dbg3 = "NtQueryInformationProcess" ascii
        $dbg4 = "OutputDebugString" ascii

        $vm1 = "VMware" ascii nocase
        $vm2 = "VirtualBox" ascii nocase
        $vm3 = "VBOX" ascii nocase
        $vm4 = "Sandboxie" ascii nocase
        $vm5 = "SbieDll" ascii

        $sleep = "Sleep" ascii
        $tick = "GetTickCount" ascii

    condition:
        uint16(0) == 0x5A4D and
        (2 of ($dbg*) or 2 of ($vm*) or (any of ($dbg*) and any of ($vm*)))
}

rule Suspicious_Persistence : medium
{
    meta:
        description = "Detects persistence mechanism indicators"
        author = "ThreatScan"
        severity = "medium"

    strings:
        $reg1 = "CurrentVersion\\Run" ascii nocase
        $reg2 = "CurrentVersion\\RunOnce" ascii nocase
        $reg3 = "CurrentVersion\\Policies\\Explorer\\Run" ascii nocase
        $reg4 = "CurrentVersion\\Windows\\Load" ascii nocase

        $sched1 = "schtasks" ascii nocase
        $sched2 = "at.exe" ascii nocase

        $startup = "\\Startup\\" ascii nocase
        $service = "CreateService" ascii

    condition:
        2 of them
}

rule Suspicious_Crypto_Mining : medium
{
    meta:
        description = "Detects potential cryptocurrency mining indicators"
        author = "ThreatScan"
        severity = "medium"

    strings:
        $pool1 = "stratum+tcp://" ascii nocase
        $pool2 = "pool.minergate" ascii nocase
        $pool3 = "xmrpool" ascii nocase
        $pool4 = "moneropool" ascii nocase
        $pool5 = "nicehash" ascii nocase
        $pool6 = "coinhive" ascii nocase

        $wallet1 = /4[0-9AB][0-9a-zA-Z]{93}/ ascii  // Monero address
        $wallet2 = /[13][a-km-zA-HJ-NP-Z1-9]{25,34}/ ascii  // Bitcoin address

        $miner1 = "cpuminer" ascii nocase
        $miner2 = "xmrig" ascii nocase
        $miner3 = "cgminer" ascii nocase

    condition:
        2 of them
}
