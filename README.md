<div align="center">
  <img src="./assets/banner.svg" alt="Komsan Nipharat — full-stack engineer: Go, TypeScript, NestJS, MongoDB" width="100%" />
</div>

<br />

I'm a full-stack engineer in Thailand, currently at **GRAM Software Solution** building container and yard-operations software. Before that, at **AddTech Hub**, I owned payment-gateway and mobile value-added services that had to settle against real telecom networks: Go workers and schedulers on NSQ, MongoDB query work on live services, and SMS / USSD / IVR operator integrations. I started out as a research assistant at **NECTEC**.

Most of that work is private. This page shows the public side: small tools, a profiled performance fix, and how I work.

<p>
  <img src="https://img.shields.io/badge/Go-0B0F14?style=flat-square&logo=go&logoColor=34D399" alt="Go" />
  <img src="https://img.shields.io/badge/TypeScript-0B0F14?style=flat-square&logo=typescript&logoColor=34D399" alt="TypeScript" />
  <img src="https://img.shields.io/badge/Node.js-0B0F14?style=flat-square&logo=nodedotjs&logoColor=34D399" alt="Node.js" />
  <img src="https://img.shields.io/badge/NestJS-0B0F14?style=flat-square&logo=nestjs&logoColor=34D399" alt="NestJS" />
  <img src="https://img.shields.io/badge/MongoDB-0B0F14?style=flat-square&logo=mongodb&logoColor=34D399" alt="MongoDB" />
  <img src="https://img.shields.io/badge/Redis-0B0F14?style=flat-square&logo=redis&logoColor=34D399" alt="Redis" />
  <img src="https://img.shields.io/badge/Angular-0B0F14?style=flat-square&logo=angular&logoColor=34D399" alt="Angular" />
  <img src="https://img.shields.io/badge/React-0B0F14?style=flat-square&logo=react&logoColor=34D399" alt="React" />
  <img src="https://img.shields.io/badge/AWS-0B0F14?style=flat-square&logo=amazonwebservices&logoColor=34D399" alt="AWS" />
  <img src="https://img.shields.io/badge/Docker-0B0F14?style=flat-square&logo=docker&logoColor=34D399" alt="Docker" />
</p>

<p>
  <a href="https://my-portflio-navy.vercel.app"><img src="https://img.shields.io/badge/Portfolio_&_CV-34D399?style=for-the-badge&logo=vercel&logoColor=0B0F14" alt="Portfolio and CV" /></a>
  <a href="https://www.linkedin.com/in/komsan-nipharat-187573211"><img src="https://img.shields.io/badge/LinkedIn-0B0F14?style=for-the-badge&logo=linkedin&logoColor=34D399" alt="LinkedIn" /></a>
</p>

## Public projects

<table>
  <tr>
    <td width="50%" valign="top"><a href="https://github.com/qaz74107410/toms-storage-search-cache"><img src="./assets/project-01.svg" width="100%" alt="Tom's Storage Search Cache" /></a></td>
    <td width="50%" valign="top"><a href="https://github.com/qaz74107410/my-jira-webui"><img src="./assets/project-02.svg" width="100%" alt="Jira Issues Web UI" /></a></td>
  </tr>
  <tr>
    <td width="50%" valign="top"><a href="https://github.com/qaz74107410/random-container-no"><img src="./assets/project-03.svg" width="100%" alt="Container Number Generator" /></a></td>
    <td width="50%" valign="top"><a href="https://github.com/qaz74107410/phasmo-notebooklm-bot"><img src="./assets/project-04.svg" width="100%" alt="Phasmo NotebookLM Bot" /></a></td>
  </tr>
</table>

## Case study: a performance fix, measured first

**[toms-storage-search-cache](https://github.com/qaz74107410/toms-storage-search-cache)** is a Java client mod (Forge 1.20.1) for a storage-terminal search that froze on every keystroke in large modpacks.

- **Cause.** Each search rebuilt hundreds of item tooltips on the render thread, because the stock cache expired them after 5 seconds of inactivity.
- **Fix.** A mixin wraps those caches in longer-lived ones whose loader *is* the stock cache. Results stay identical; only the cache lifetime changes, and it is configurable back to stock.
- **Evidence.** Java Flight Recorder, about 4 s of continuous typing in a ~365-mod pack:

| Render-thread samples | Before | After |
| :--- | ---: | ---: |
| Search total | 175 | **43** |
| Tooltip building | 167 | **10** |

A second optimization (skipping an unchanged inventory snapshot) is shipped but marked *not yet tested in game* in the README rather than claimed.

## How I work

- **Measure before claiming.** Profiles and numbers first; untested work gets labelled as untested.
- **Keep the request thin.** Long-running work goes to a queue and a worker that can retry, not into the HTTP request.
- **Leave it operable.** Documented schemas, clear failure modes, and a deploy the next person can run.

<br />

<img src="./assets/langs.svg" alt="Language mix across public repositories" width="100%" />

<details>
<summary><b>🎮 Just for fun: my last 12 months, played back</b> (click to open)</summary>

<br />

Every active day is an invader; the ship clears the wave, then a new one spawns tomorrow.

<img src="./assets/shooter.svg" alt="Space shooter: every active day of the last 12 months is an invader, and a ship clears the wave" width="100%" />

The same year as a city, one building per day:

<img src="./profile-3d-contrib/profile-night-green.svg" alt="3D contribution graph, last 12 months" width="100%" />

</details>

<sub>Banner, language, project and shooter cards are generated from the GitHub API by scripts in <a href="./scripts"><code>scripts/</code></a> and refreshed daily by <a href="./.github/workflows/refresh-cards.yml">a workflow</a>.</sub>
