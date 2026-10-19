import re,sys,pathlib
def first(pat,s,after=None):
    if after: s=s[s.index(after):]
    m=re.search(pat,s); return m.group(1) if m else "-"
def slack_after(s,hdr,which=0):
    i=s.find(hdr); 
    if i<0: return "-"
    seg=s[i:]; m=re.findall(r'\s(-?\d+\.\d+) \((?:MET|VIOLATED)\)',seg); return m[which] if m else "-"
print("corner | CLK setup | CLK hold | hold WNS | hold TNS | viol | LUT | IO | MACC | D max | D min | G fall max | G fall min | sel rise min")
for tag in sys.argv[1:]:
    s=pathlib.Path(tag+".log").read_text()
    v=pathlib.Path(f"hold_violators_{tag}.txt")
    nv=len(re.findall(r'VIOLATED',v.read_text())) if v.exists() else "-"
    row=[tag,
      slack_after(s,"==== CLK register-to-register"),
      slack_after(s,"min_delay/hold group CLK"),
      first(r'wns min (\S+)',s), first(r'tns min (\S+)',s), str(nv),
      slack_after(s,"worst hold into LUT"), slack_after(s,"worst hold into IO"), slack_after(s,"worst hold into MACC")]
    for hdr,kind in [("FrameData into latch D","max"),("FrameData into latch D","min"),("FrameStrobe falling","max"),("FrameStrobe falling","min"),("glitch window","min")]:
        i=s.find(hdr); seg=s[i:]
        j=seg.find("min_delay/hold") if kind=="min" else seg.find("max_delay/setup")
        m=re.search(r'\s(\d+\.\d+)\s+(-?\d+\.\d+) \(',seg[j:]); row.append(m.group(1) if m else "-")
    print(" | ".join(row))
