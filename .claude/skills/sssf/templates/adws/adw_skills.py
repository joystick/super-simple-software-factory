#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pydantic", "python-dotenv", "pyyaml", "rich"]
# ///
"""ADW Skills — audit which skill_engineering files are vendored under
adws/adw_data/skill_engineering/ and which agents use them. Free: reads the
config and lists a directory, spawns nothing, costs nothing, writes no
trace — there is no run to record.

(Full dependency set, matching every other adws/adw_*.py entrypoint, even
though this script itself only needs pydantic+pyyaml: `adw_modules.agents`
unconditionally imports agent_cc/agent_pi/agent_agy at module load, and
those transitively require python-dotenv and rich through adw_modules.utils
regardless of which functions actually get called. Caught live — a leaner
deps list looked reasonable and failed the moment this actually ran.)

Usage:
    uv run adws/adw_skills.py [--config adws/adw_sssf_config/sssf.config.yaml]
"""

import argparse
import sys

from adw_modules import agents


def main(config: str = "adws/adw_sssf_config/sssf.config.yaml") -> int:
    cfg = agents.load_config(config)
    report = agents.audit_skills(cfg)

    if not report.vendored and not report.outside_vendor_dir:
        print("no skill_engineering usage found")
        return 0

    if report.vendored:
        print("vendored (adws/adw_data/skill_engineering/):")
        for item in report.vendored:
            used_by = ", ".join(item.agents) if item.agents else "(unused)"
            line = f"  {item.path}  ->  {used_by}"
            if item.ignored_by:
                # named it, but their coding_agent means it never applies —
                # surfaced here, not silently dropped, same reasoning as
                # agents.validate()'s own warning for the same mismatch.
                line += f"  [ignored by: {', '.join(item.ignored_by)} — not claude_code]"
            print(line)

    if report.outside_vendor_dir:
        print("\nnamed by an agent but NOT under the vendored dir (hand-authored, or check for a typo):")
        for path, names in sorted(report.outside_vendor_dir.items()):
            print(f"  {path}  ->  {', '.join(names)}")

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="adws/adw_sssf_config/sssf.config.yaml")
    args = parser.parse_args()
    sys.exit(main(args.config))
