import sys, os, json, importlib.util, io, contextlib
root = sys.argv[1]; model = sys.argv[2]; out = sys.argv[3]
sys.path.insert(0, root); os.chdir(root)
spec = importlib.util.spec_from_file_location("GenSMBIOS", os.path.join(root, "GenSMBIOS.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    s = m.Smbios()
    s._get_macserial()
    mac = s._get_binary()
    res = s._get_smbios(mac, model, 1)
if not res: raise SystemExit("generation failed: " + buf.getvalue()[-300:])
r = res[0]
json.dump({"model": r[0], "serial": r[1], "mlb": r[2], "uuid": r[3], "rom": r[4], "macserial": mac}, open(out, "w"))
print("ok fields:", len(r), "macserial:", os.path.basename(mac))
