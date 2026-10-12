# agterm visuals

Explainers as HTML pages in agterm's right split pane: top-down flowcharts with short labels, details on click, and interactive walkthroughs where you press Yes/No on decisions and watch the actual payload at each step.

## Install

```bash
/plugin marketplace add ZhilinS/cc-plugins
/plugin install agterm-visuals@zhilin-cc-plugins
```

Needs agterm with `agtermctl` on `PATH`. Chrome is used for a headless screenshot check before a page is shown as done.

## How it grows

Your corrections to a page go to `~/.claude/agterm-visuals/feedback.md`, and the skill reads that file before every new page. Lessons that apply to everyone get folded into the skill by PR.
