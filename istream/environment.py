"""Local capability diagnostics; never sends media or calls model services."""
import importlib.util
import json
import shutil
import subprocess
import sys


def inspect_environment(render=False, slicing=False):
    checks = []

    def add(name, ok, detail, required=True):
        checks.append(dict(name=name, ok=bool(ok), required=required, detail=detail))

    add("python", sys.version_info >= (3, 10), sys.version.split()[0])
    numpy = importlib.util.find_spec("numpy") is not None
    add("numpy", numpy, "available" if numpy else "install: python -m pip install -r requirements.txt", slicing)
    if render:
        for binary in ("ffmpeg", "ffprobe"):
            path = shutil.which(binary)
            add(binary, path, path or "missing from PATH")
            if not path or binary != "ffmpeg":
                continue
            for option, features in (("-filters", ("drawtext", "subtitles")), ("-encoders", ("libx264",))):
                try:
                    result = subprocess.run([path, "-hide_banner", option], capture_output=True, text=True, timeout=15, check=True)
                    names = {parts[1] for line in result.stdout.splitlines() if len(parts := line.split()) >= 2}
                    for feature in features:
                        add(feature, feature in names, "available" if feature in names else f"FFmpeg missing {feature}")
                except (OSError, subprocess.SubprocessError) as exc:
                    add(binary + option, False, str(exc))
        from .render import FONT
        add("cjk_font", FONT, FONT or "install Noto CJK or set ISTREAM_FONT to a font file")
    return {"ok": all(c["ok"] for c in checks if c["required"]), "checks": checks}


def command(args):
    report = inspect_environment(render=args.render, slicing=args.slicing)
    if args.as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for check in report["checks"]:
            status = "OK" if check["ok"] else ("ERROR" if check["required"] else "OPTIONAL")
            print(f"{status:8} {check['name']}: {check['detail']}")
        if not report["ok"]:
            print("See docs/QUICKSTART.md for setup and troubleshooting.")
    raise SystemExit(0 if report["ok"] else 1)
