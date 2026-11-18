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
TOOLS += [Tool('OpenCode','AI and agents','opencode','vendor',note='Install with curl -fsSL https://opencode.ai/install | bash (to ~/.opencode/bin); update with opencode upgrade. mise npm:opencode-ai skips the postinstall that fetches the binary.')]
TOOLS += [Tool('treg','AI and agents','treg','mise','pipx:tools-registry[proxy]','latest',note='Extras syntax verified 2026-11-17.'), Tool('T3 CLI','AI and agents','t3','mise','npm:t3','latest',('linux',)),
          Tool('T3 CLI and service','AI and agents','t3','vendor',platforms=('darwin',),note='t3 launcher in ~/.local/bin, versions in ~/.t3/runtime; update with t3 update. t3 service install runs the server headless; the T3 Code desktop app (own updater, same version as t3) attaches as a client with Local environment off.')]
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
TOOLS += [Tool('Defuddle','Developer tools','defuddle','mise','npm:defuddle','latest',note='Verify npm package is the intended CLI.',requires_verification=True)]
TOOLS += mise('Cloud and services', '''Supabase|supabase|supabase|3
Stripe|stripe|stripe|1
AWS CLI|aws|aws-cli|2
kubectl|kubectl|kubectl|latest
gcloud|gcloud|gcloud|latest
Vercel|vercel|npm:vercel|latest
Notion CLI|ntn|npm:ntn|latest
rclone|rclone|rclone|1
dotenvx|dotenvx|dotenvx|2
yt-dlp|yt-dlp|yt-dlp|latest''')
for name, cmd, mac, linux, note in [
 ('Git','git','','git','Apple Git on macOS; retain system copy. Install Homebrew git only if a newer version is needed.'),
 ('Docker','docker','docker','docker','Engine is separate: a desktop engine on macOS, the Docker service on Omarchy.'),
 ('Docker Compose','docker-compose','docker-compose','docker-compose','Engine is separate: a desktop engine on macOS, the Docker service on Omarchy.'),
 ('PostgreSQL','psql','postgresql@15','postgresql','Existing clusters require a separate migration decision.'),
 ('ffmpeg','ffmpeg','ffmpeg','ffmpeg',''), ('ImageMagick','magick','imagemagick','imagemagick',''),
 ('GnuPG','gpg','gnupg','gnupg',''), ('SQLite','sqlite3','sqlite','sqlite',''), ('tree','tree','tree','tree',''),
 ('Powerlevel10k','','powerlevel10k','zsh-theme-powerlevel10k','Prompt; config in ~/.p10k.zsh. Source from the package share dir ($HOMEBREW_PREFIX/share on macOS, /usr/share on Omarchy), never a git clone into ~/.oh-my-zsh/custom.'),
 ('zsh-autosuggestions','','zsh-autosuggestions','zsh-autosuggestions','Source from the package share dir.'), ('zsh-syntax-highlighting','','zsh-syntax-highlighting','zsh-syntax-highlighting','Source from the package share dir; load last.'),
 ('Ghostty','ghostty','ghostty','ghostty','Terminal (libghostty). Homebrew cask on macOS, pacman on Omarchy.'), ('ngrok','ngrok','ngrok','','Verify Arch source.'),
 ('CocoaPods','pod','cocoapods','','macOS only.'), ('Tailscale','tailscale','','tailscale','macOS uses vendor app; keep the CLI paired with its service.')]:
    if mac: TOOLS.append(Tool(name,'System utilities',cmd,'brew',mac,platforms=('darwin',),note=note))
    elif name in ('Git','Tailscale'): TOOLS.append(Tool(name,'System utilities',cmd,'vendor',platforms=('darwin',),note=note))
    if linux: TOOLS.append(Tool(name,'System utilities',cmd,'pacman',linux,platforms=('linux',),note=note))
    elif name in ('ngrok',): TOOLS.append(Tool(name,'System utilities',cmd,'manual',platforms=('linux',),note=note))
TOOLS += [Tool(name,'Vendor apps',cmd,'vendor',note=note) for name,cmd,note in [
 ('mise','mise','Install from mise.run; version 2026.11 or newer required.'),
 ('Cursor Agent','cursor-agent','Install with curl https://cursor.com/install -fsS | bash; also provides agent. Grok’s own installer links an agent command over it, so Grok comes from mise only.'),
 ('Oh My Zsh','','Plugins (git) only, ZSH_THEME=""; updates through its own updater.'),
 ('cmux','cmux','Terminal layer on top of libghostty; vendor-owned.'),
 ('Cursor CLI','cursor','Provided by the Cursor app.'),
 ('Herdr app','herdr-app','Install Herdr app and Herdr Core (herdr-app, herdr-core, hc) with curl -fsSL https://releases.herdr.dev/app/install.sh | sh; updates through the app. Separate from the mise-managed Herdr CLI.'),
 ('browse','browse','Use browse’s installer; mise fx is unrelated.'),
 ('Paper','paper-desktop','Linux: run scripts/paper/update-paper.sh (installs the official AppImage to ~/.local/opt/paper, or $HOME/opt/paper if that already exists; links paper-desktop and update-paper into ~/.local/bin; writes a .desktop entry). Latest URLs are https://download.paper.design/linux/appImage/x64 and .../arm64; the script compares the ETag (the file MD5) and downloads only when it changes. Pass --install-timer for a daily systemd user timer. The AppImage has no AppImageUpdate metadata; ToDesktop may self-update only while the GUI AppImage is running. Do not name the binary paper: /usr/bin/paper is libpaper on Arch. macOS: install from https://paper.design/downloads and use the in-app updater. Remote MCP (no desktop required): add https://mcp.paper.design and complete Paper OAuth at login.paper.design. Local MCP still uses Paper Desktop or the Paper CLI (paper mcp).')]]
TOOLS += [Tool(name,'Built from our repos',cmd,'manual',note=note) for name,cmd,note in [
 ('lific','lific','Build from raphaelmans/lific (our fork; cargo install lific and upstream releases install the original): cd web && bun install --frozen-lockfile --ignore-scripts && bun run build && cd .. && cargo build --release --locked, then ln -sf "$PWD/target/release/lific" ~/.local/bin/lific. Update with git pull and rebuild.'),
 ('herdr-viz','herdr-viz','Link from raphaelmans/herdr-app cloned to ~/.config/herdr-app: ln -sf ~/.config/herdr-app/mods/viz/herdr-viz ~/.local/bin/herdr-viz. Runs on mise Node; update with git pull there.')]]
