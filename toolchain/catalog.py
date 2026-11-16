from dataclasses import dataclass

@dataclass(frozen=True)
class Tool:
    name: str
    group: str
    command: str
    owner: str
    spec: str = ''
    pin: str = ''
    platforms: tuple = ('darwin', 'linux')
    note: str = ''
    requires_verification: bool = False

def mise(group, lines):
    return [Tool(name, group, cmd, 'mise', spec, pin) for name, cmd, spec, pin in (line.split('|') for line in lines.strip().splitlines())]

TOOLS = mise('Runtimes', '''Node.js|node|node|26
pnpm|pnpm|pnpm|10
Bun|bun|bun|1
Python|python|python|3.14
Ruby|ruby|ruby|3.4
Rust|rustc|rust|stable
uv|uv|uv|0.13
Go|go|go|1.27
Deno|deno|deno|2''')
TOOLS += mise('AI and agents', '''Codex|codex|npm:@openai/codex|latest
Claude Code|claude|claude|latest
Grok|grok|grok|latest
OpenSpec|openspec|npm:@fission-ai/openspec|1
Herdr CLI|herdr|github:herdrdev/herdr|latest
Agent Desktop|agent-desktop|github:vercel-labs/agent-desktop|latest
Agent Browser|agent-browser|agent-browser|latest
OpenClaw|openclaw|npm:openclaw|latest
Skillshare|skillshare|github:runkids/skillshare|latest
nano-pdf|nano-pdf|pipx:nano-pdf|latest''')
TOOLS += [Tool('OpenCode','AI and agents','opencode','vendor',note='Use the OpenCode vendor installer and updater; mise npm:opencode-ai skips the postinstall that fetches the binary.')]
TOOLS += [Tool('treg','AI and agents','treg','manual',note='Verify pipx:tools-registry[proxy] extras syntax.'), Tool('T3 CLI','AI and agents','t3','mise','npm:t3','latest',('linux',)), Tool('T3 Code app','AI and agents','t3','vendor',platforms=('darwin',),note='Provided by T3 Code desktop app.')]
TOOLS += mise('Developer tools', '''GitHub CLI|gh|gh|2
ripgrep|rg|ripgrep|15
fd|fd|fd|10
fzf|fzf|fzf|latest
lazygit|lazygit|lazygit|latest
Neovim|nvim|neovim|0.12
tmux|tmux|tmux|3
jq|jq|jq|1
direnv|direnv|direnv|2
Worktrunk|wt|worktrunk|latest
Turborepo|turbo|npm:turbo|2
Portless|portless|npm:portless|latest
Playwright CLI|playwright-cli|npm:@playwright/cli|latest
Obsidian headless|ob|npm:obsidian-headless|latest''')
TOOLS += [Tool('playwright-cli','Developer tools','','mise','npm:playwright-cli','latest',
               note='Deprecated package has no CLI executable. Manually reconcile the referenced standard and verify the intended replacement before installation.',
               requires_verification=True)]
TOOLS += [Tool('Defuddle','Developer tools','defuddle','manual',note='Verify npm package is the intended CLI.')]
TOOLS += mise('Cloud and services', '''Supabase|supabase|supabase|3
Stripe|stripe|stripe|1
AWS CLI|aws|aws-cli|2
kubectl|kubectl|kubectl|latest
gcloud|gcloud|gcloud|latest
Vercel|vercel|npm:vercel|latest
rclone|rclone|rclone|1
dotenvx|dotenvx|dotenvx|2
yt-dlp|yt-dlp|yt-dlp|latest''')
for name, cmd, mac, linux, note in [
 ('Git','git','','git','Apple Git on macOS; retain system copy.'),
 ('Docker','docker','docker','docker','Engine is separate.'),
 ('Docker Compose','docker-compose','docker-compose','docker-compose','Engine is separate.'),
 ('PostgreSQL','psql','postgresql@15','postgresql','Existing clusters require a separate migration decision.'),
 ('ffmpeg','ffmpeg','ffmpeg','ffmpeg',''), ('ImageMagick','magick','imagemagick','imagemagick',''),
 ('GnuPG','gpg','gnupg','gnupg',''), ('SQLite','sqlite3','sqlite','sqlite',''), ('tree','tree','tree','tree',''),
 ('autojump','autojump','autojump','','Verify Arch source.'), ('ngrok','ngrok','ngrok','','Verify Arch source.'),
 ('CocoaPods','pod','cocoapods','','macOS only.'), ('Tailscale','tailscale','','tailscale','macOS uses vendor app.')]:
    if mac: TOOLS.append(Tool(name,'System utilities',cmd,'brew',mac,platforms=('darwin',),note=note))
    elif name in ('Git','Tailscale'): TOOLS.append(Tool(name,'System utilities',cmd,'vendor',platforms=('darwin',),note=note))
    if linux: TOOLS.append(Tool(name,'System utilities',cmd,'pacman',linux,platforms=('linux',),note=note))
    elif name in ('autojump','ngrok'): TOOLS.append(Tool(name,'System utilities',cmd,'manual',platforms=('linux',),note=note))
TOOLS += [Tool(name,'Vendor apps',cmd,'vendor',note=note) for name,cmd,note in [
 ('mise','mise','Install from mise.run; version 2026.11 or newer required.'),
 ('Cursor Agent','cursor-agent','Use Cursor vendor installer and updater.'),
 ('Cursor CLI','cursor','Provided by the Cursor app.'),
 ('Herdr app','herdr-app','Use the Herdr app installer; separate from Herdr CLI.'),
 ('browse','browse','Use browse’s installer; mise fx is unrelated.')]]
