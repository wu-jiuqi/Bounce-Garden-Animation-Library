"""Publish only the gallery and animation assets from committed HEAD to gh-pages."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def git(*args, input=None):
    # Feed Git raw LF bytes: Windows text mode would add CR to mktree filenames.
    return subprocess.check_output(
        ['git', '-C', str(ROOT), *args],
        input=input.encode('utf-8') if input is not None else None,
    ).decode('utf-8').strip()

files = ['index.html', 'style.css', 'app.js', 'catalog.js', 'catalog.json', 'assets']
entries = git('ls-tree', 'HEAD', '--', *files).splitlines()
if len(entries) != len(files):
    raise SystemExit('Gallery files must all exist in committed HEAD before publishing.')
empty = git('hash-object', '-w', '--stdin', input='')
entries.append(f'100644 blob {empty}\t.nojekyll')
tree = git('mktree', input='\n'.join(entries)+'\n')
assert git('ls-tree', '--name-only', tree).splitlines() == sorted([*files, '.nojekyll'])
parent = subprocess.run(['git','-C',str(ROOT),'rev-parse','--verify','refs/heads/gh-pages'],capture_output=True,text=True)
args = ['commit-tree', tree]
if parent.returncode == 0:
    args += ['-p', parent.stdout.strip()]
source = git('rev-parse', 'HEAD')
commit = git(*args, input=f'Publish animation gallery from {source}\n')
git('update-ref', 'refs/heads/gh-pages', commit)
subprocess.run(['git','-C',str(ROOT),'push','origin','gh-pages'],check=True)
print(f'Published gh-pages: {commit}')
