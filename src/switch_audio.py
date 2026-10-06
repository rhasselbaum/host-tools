#!/usr/bin/env python3

"""
Toggles the default PipeWire output between analog speakers and USB headphones. If any other sink is
the default, switches to the speakers. Intended to be bound to a KDE Plasma global shortcut.
"""

import json
import subprocess
import sys

# Matched as prefixes of node.name so profile suffixes (e.g. .analog-stereo) can change.
SPEAKERS = "alsa_output.pci-0000_00_1f.3."
HEADPHONES = "alsa_output.usb-Razer_BlackShark_V3_X_USB"

ICONS = {SPEAKERS: "audio-speakers", HEADPHONES: "audio-headphones"}


def pw_dump():
    return json.loads(subprocess.run(["pw-dump"], capture_output=True, check=True, text=True).stdout)


def get_sinks(objects):
    """Return {node.name: (id, description)} for all audio sinks."""
    sinks = {}
    for obj in objects:
        props = obj.get("info", {}).get("props", {})
        if props.get("media.class") == "Audio/Sink":
            name = props.get("node.name", "")
            sinks[name] = (obj["id"], props.get("node.description") or name)
    return sinks


def get_default_sink_name(objects):
    for obj in objects:
        if obj.get("type") != "PipeWire:Interface:Metadata":
            continue
        if obj.get("props", {}).get("metadata.name") != "default":
            continue
        for entry in obj.get("metadata", []):
            if entry.get("key") == "default.audio.sink":
                value = entry.get("value")
                if isinstance(value, str):
                    value = json.loads(value)
                return value.get("name")
    return None


def find_sink(sinks, prefix):
    for name, info in sinks.items():
        if name.startswith(prefix):
            return info
    return None


def show_osd(icon, text):
    try:
        subprocess.run(
            ["qdbus", "org.kde.plasmashell", "/org/kde/osdService",
             "org.kde.osdService.showText", icon, text],
            capture_output=True, timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        pass


def main():
    objects = pw_dump()
    sinks = get_sinks(objects)
    current = get_default_sink_name(objects) or ""

    target, other = (HEADPHONES, SPEAKERS) if current.startswith(SPEAKERS) else (SPEAKERS, HEADPHONES)

    sink = find_sink(sinks, target)
    if sink is None:
        print(f"Target device not found ({target}*), falling back", file=sys.stderr)
        target = other
        sink = find_sink(sinks, target)
    if sink is None:
        print("Neither speakers nor headphones found", file=sys.stderr)
        show_osd("dialog-error", "No audio output found")
        return 1

    sink_id, description = sink
    subprocess.run(["wpctl", "set-default", str(sink_id)], check=True)
    print(f"Default output: {description}")
    show_osd(ICONS[target], description)
    return 0


if __name__ == "__main__":
    sys.exit(main())
