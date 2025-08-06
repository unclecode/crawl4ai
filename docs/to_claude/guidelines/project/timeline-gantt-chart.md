<!-- ---
!-- Timestamp: 2025-06-10 07:13:06
!-- Author: ywatanabe
!-- File: /home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/project/timeline-gantt-chart.md
!-- --- -->

Timeline Gantt charts are excellent tools for planning, directing, and communicating. Therefore, we encourage incorporating this technique into progress management.

Absolute time is not always important; instead, relative time or the visualization of project progression is most important. Therefore, timestamps are not necessarily accurate. You may check git history, but precision is not strictly required.

Embed `git commit hash` to each element. If embedding numbers will clutter output figure, just include comments in mermaid files.

Timeline should be saved as:
    `./project_management/timeline-<timestamp>.mmd`
    `./project_management/timeline-<timestamp>.png`

# Timeline Gantt Chart Format

``` mermaid
gantt
    dateFormat  YYYY-MM-DD
    title       Emacs Claude Code Project Timeline
    
    section Core Components
    Term Claude Mode            :done,    term_mode,     2025-04-01, 2025-04-15
    Auto Response System        :done,    auto_resp,     2025-04-10, 2025-04-30
    State Detection             :done,    state_det,     2025-04-15, 2025-05-05
    Visual Aids                 :done,    visual_aids,   2025-04-25, 2025-05-10
    Interaction Limits          :active,  inter_limits,  2025-05-10, 2025-05-30
    
    section Advanced Features
    Yank As File                :done,    yank_file,     2025-04-20, 2025-05-15
    Buffer Management           :done,    buffer_mgmt,   2025-05-01, 2025-05-18
    Templates                   :active,  templates,     2025-05-15, 2025-06-05
    Notifications               :active,  notifs,        2025-05-20, 2025-06-10
    
    section Infrastructure
    Variables & Configuration   :done,    vars_config,   2025-04-01, 2025-04-20
    Testing Framework           :done,    testing,       2025-04-05, 2025-05-10
    Documentation               :active,  docs,          2025-05-01, 2025-06-15
    
    section Bug Fixes
    Auto Response Timer         :done,    timer_fix,     2025-05-05, 2025-05-12
    Dashboard Buffer Visibility :done,    dash_fix,      2025-05-08, 2025-05-14
    Debug Message Control       :done,    debug_fix,     2025-05-12, 2025-05-18
    Initial Waiting Detection   :done,    waiting_fix,   2025-05-15, 2025-05-20
```

<!-- EOF -->