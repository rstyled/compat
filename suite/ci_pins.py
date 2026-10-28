"""Record the exact CI-selected checkouts and their source-pinned Rust compiler."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import tomllib


def output(argv, cwd=None):
    return subprocess.check_output(argv, cwd=cwd, text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gstyle', type=Path, required=True)
    parser.add_argument('--rstyle', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    toolchain = tomllib.loads((args.rstyle/'rust-toolchain.toml').read_text())['toolchain']['channel']
    compiler = output(['rustup','which','--toolchain',toolchain,'rustc'])
    version = output([compiler,'-vV'])
    commit, = [line.removeprefix('commit-hash: ') for line in version.splitlines() if line.startswith('commit-hash: ')]
    pins = {'rust_toolchain':toolchain, 'rustc_commit':commit,
            'upstream_checked_utc':datetime.now(timezone.utc).isoformat(),
            'revision_scope':'CI-selected refs resolved to immutable checkout revisions; baseline pins unchanged'}
    for name in ('gstyle','rstyle'):
        source = getattr(args, name)
        if output(['git','status','--porcelain'], source):
            raise RuntimeError('CI requires a clean producer checkout: ' + name)
        pins[name+'_revision'] = output(['git','rev-parse','HEAD'], source)
        pins[name+'_upstream'] = 'https://github.com/rstyled/' + name
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(pins, indent=2) + '\n')
    print(json.dumps(pins, indent=2))


if __name__ == '__main__':
    main()
