import typer, os, tempfile, subprocess
from pathlib import Path

app = typer.Typer(help="Remedy CLI")

@app.command()
def scan(repo: str):
    """Clone and run Semgrep/OSV locally (quick smoke)."""
    tmp = tempfile.mkdtemp(prefix="remedy_cli_")
    subprocess.run(["git","clone","--depth","1",repo,tmp], check=True)
    print("Running Semgrep...")
    subprocess.run(["semgrep","--config","scanners/semgrep/profiles.yml","--json","--quiet"], cwd=tmp)
    print("Running OSV...")
    subprocess.run(["osv-scanner","-r",tmp], check=False)
    print("Done.")

if __name__ == "__main__":
    app()
