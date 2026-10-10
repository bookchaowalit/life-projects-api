import { defineRailway, project, service } from "railway/iac";

// solo-projects: the Projects and portfolio cell. Variables stay unmanaged (secrets live in Railway only).
// projects-api sleeps when idle (Railway Serverless) and wakes on the next request.
// projects-publisher is a cron sweep of the outbox that exits after each run.
export default defineRailway(() => {
  const api = service("projects-api", {
    healthcheck: "/health",
    healthcheckTimeout: 60,
    deploy: { sleepApplication: true },
  });
  const publisher = service("projects-publisher", {
    startCommand: "projects-publish",
    deploy: { cronSchedule: "*/15 * * * *", restartPolicyType: "NEVER" },
  });

  return project("solo-projects", {
    variables: { managed: false },
    resources: [api, publisher],
  });
});
