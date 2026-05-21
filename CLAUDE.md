# CLAUDE.md — AI Assistant Reference for undercover-wechat-game

## Project Overview

**谁是卧底** (Undercover) is a WeChat mini-program social deduction game. Players are split into civilians and undercover agents; each receives a word and must describe it without revealing their identity while trying to identify who the undercover agents are.

- **Repository:** https://github.com/mayuehit/Ai
- **Package name:** `undercover-wechat-game` (v0.1.0)
- **Status:** Early scaffold — application code not yet implemented. Only docs and config exist.
- **License:** MIT

---

## Repository Structure

```
Ai/
├── package.json          # NPM config, scripts, and dependencies
├── README.md             # Project overview (Chinese)
├── CONTRIBUTING.md       # Contribution guide and team roles (Chinese)
├── CLAUDE.md             # This file
├── miniprogram/          # WeChat mini-program frontend (planned, not yet created)
├── server/               # Node.js backend (planned, not yet created)
│   └── src/
│       └── index.js      # Main entry point (package.json "main" field)
├── docs/                 # Documentation (planned, not yet created)
└── tests/                # Test code (planned, not yet created)
```

All application directories (`miniprogram/`, `server/`, `docs/`, `tests/`) are **planned but not yet created**. When implementing, follow this structure exactly.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | WeChat mini-program (WXML, WXSS, JavaScript) |
| Backend | Node.js + Express (`^4.18.0`) |
| Database | MongoDB via Mongoose (`^7.0.0`) |
| Real-time | WebSocket via Socket.IO (`^4.7.0`) |
| WeChat UI | weui-miniprogram (`^1.0.0`) |
| Testing | Jest (`^29.0.0`) |
| Linting | ESLint (`^8.0.0`) |
| Formatting | Prettier (`^3.0.0`) |
| Dev server | nodemon (`^3.0.0`) |

---

## Development Commands

```bash
npm start          # Start production server (node server/src/index.js)
npm run dev        # Start dev server with auto-reload (nodemon)
npm test           # Run Jest test suite
npm run lint       # Run ESLint across the project
npm run format     # Auto-format all files with Prettier
```

> **Note:** `npm install` must be run first. The `server/src/index.js` entry point does not exist yet — create it when implementing the backend.

---

## Git Workflow

### Branch naming
```
feature/<feature-name>   # New features
fix/<bug-description>    # Bug fixes
docs/<topic>             # Documentation changes
refactor/<scope>         # Refactoring
```

### Conventional commits (required)
```
feat:      New feature
fix:       Bug fix
docs:      Documentation update
style:     Code formatting (no logic change)
refactor:  Code restructuring
test:      Test additions or changes
chore:     Build tooling or auxiliary changes
```

Example: `git commit -m "feat: 实现游戏房间创建功能"`

### PR process
1. Branch off from `main`
2. Implement changes on the feature branch
3. Open a Pull Request using the PR template in CONTRIBUTING.md
4. Requires **at least 2 reviewers**
5. Must pass all CI checks (once CI is configured)
6. Merge using **Squash Merge** to keep history clean
7. Delete the feature branch after merging

---

## Code Conventions

- Follow ESLint configuration (`.eslintrc` to be defined)
- Format with Prettier (`.prettierrc` to be defined)
- Keep functions single-responsibility
- Write meaningful comments only when the WHY is non-obvious
- Write unit tests alongside implementation code under `tests/`

---

## Planned Features (Implementation Checklist)

- [ ] User login and authentication (WeChat OAuth)
- [ ] Game room creation and joining
- [ ] Role assignment (civilian / undercover)
- [ ] Word library management
- [ ] Game round flow logic
- [ ] Voting and reasoning system
- [ ] Real-time chat (Socket.IO)
- [ ] Game result statistics

---

## Team Roles

| Role | Responsibility |
|---|---|
| Coordinator (协调者) | Project coordination, stand-ups, cross-role blockers |
| Product Manager (产品经理) | Requirements, PRD, feature prioritization, acceptance |
| Architect (架构师) | System design, coding standards, tech review |
| Developer (开发工程师) | Feature implementation, unit tests, bug fixes |
| Test Engineer (测试工程师) | Test cases, integration/performance testing, bug reports |

---

## AI Assistant Guidelines

- **Do not create files outside the planned structure** (`miniprogram/`, `server/`, `docs/`, `tests/`).
- **Use conventional commits** for all commits.
- **Write tests** in `tests/` for any server-side logic implemented.
- **Do not add dependencies** beyond those already in `package.json` without confirming with the user.
- **User-facing content** (README, CONTRIBUTING, in-app text) should remain in Chinese to match the existing codebase style.
- **Backend entry point** is `server/src/index.js` — always keep this as the main file.
- **No CI/CD** is configured yet; do not assume workflows exist.
- When the project grows, update this file to reflect actual implemented structure, real config file locations, and any environment variables required.
