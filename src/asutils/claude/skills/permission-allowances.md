---
name: permission-allowances
description: Default permission grants for common operations. This skill is ALWAYS active and grants Claude permission to perform standard filesystem, development, and system operations without asking for confirmation. Applies to all tasks involving file operations, development tools, containers, package managers, and system utilities.
---

# Permission Allowances

This skill grants default permissions for common operations. Claude should proceed with these operations without asking for user confirmation.

## Filesystem Operations

**Allowed without confirmation:**

- Read, search, find, list files anywhere under `/home`, `/mnt/user-data`, `/tmp`, `/var/tmp`
- Create, write, modify, delete files in `/home/claude`, `/mnt/user-data/outputs`, `/tmp`
- Use `find`, `grep`, `rg`, `fd`, `locate`, `ls`, `tree`, `cat`, `head`, `tail`, `less` anywhere readable
- File manipulation: `mkdir`, `touch`, `cp`, `mv`, `rm`, `ln`, `chmod`, `chown`
- Check file sizes, permissions, timestamps with `stat`, `du`, `df`, `wc`
- Compress/decompress with `tar`, `gzip`, `zip`, `unzip`, `7z`

## Development Tools

**Allowed without confirmation:**

- Run any Python, Node.js, Bash, or other interpreter
- Use `pip install`, `npm install`, `yarn add`, `cargo build` (with appropriate flags)
- Execute build tools: `make`, `cmake`, `gradle`, `maven`, `cargo`
- Run linters and formatters: `black`, `ruff`, `prettier`, `eslint`, `mypy`, `pylint`
- Use version control: `git` (all subcommands including clone, pull, push if network allows)
- Run tests: `pytest`, `jest`, `mocha`, `cargo test`
- Task tracking: `bd` / beads (all subcommands: init, create, update, close, list, show, sync, etc.)

## Container & Virtualization

**Allowed without confirmation:**

- `docker` - all subcommands (build, run, exec, ps, images, logs, stop, rm)
- `docker-compose` / `docker compose` - all subcommands
- `podman` - all subcommands
- Container inspection and debugging

## Package Managers

**Allowed without confirmation:**

- `apt-get`, `apt` (with sudo if available)
- `pip`, `pip3` (always use `--break-system-packages` when needed)
- `npm`, `yarn`, `pnpm`
- `cargo`, `rustup`
- `gem`, `bundle`
- `go get`, `go install`

## System Utilities

**Allowed without confirmation:**

- Process inspection: `ps`, `top`, `htop`, `pgrep`, `lsof`
- Network inspection: `curl`, `wget`, `ping`, `netstat`, `ss`, `nc` (for diagnostics)
- Environment: `env`, `printenv`, `export`, `which`, `whereis`, `type`
- Text processing: `awk`, `sed`, `cut`, `sort`, `uniq`, `tr`, `jq`, `yq`
- Resource monitoring: `free`, `uptime`, `vmstat`, `iostat`

## Database & Data Tools

**Allowed without confirmation:**

- CLI clients: `psql`, `mysql`, `sqlite3`, `redis-cli`, `mongosh`
- Data tools: `jq`, `yq`, `csvtool`, `xsv`
- Query and inspect local databases

## Web & API Tools

**Allowed without confirmation:**

- `curl`, `wget`, `httpie` for API requests
- Browser automation tools if installed
- Web scraping within allowed domains

## Behaviors

1. **Proceed directly** - Do not ask "would you like me to..." for any operation covered above
2. **Chain commands** - Combine multiple operations in single bash calls when efficient
3. **Use sudo sparingly** - Only for package installation when required
4. **Report results** - Show relevant output, summarize verbose output
5. **Handle errors** - Retry with fixes, explain failures clearly

## Exclusions (still require caution)

- Modifying system configuration files outside home
- Network operations to non-whitelisted domains
- Operations that could cause data loss without clear user intent
- Installing system-wide services or daemons
- Modifying other users' files
