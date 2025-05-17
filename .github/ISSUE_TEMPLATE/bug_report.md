name: Bug Report
description: File a bug report.
title: "[Bug]: "
labels: ["bug", "triage"]
projects: ["ArmoredTurtle/AFC-Klipper-Add-On"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for taking the time to fill out this bug report!
  - type: textarea
    id: what-happened
    attributes:
      label: What happened?
      description: Also tell us, what did you expect to happen?
      placeholder: Tell us what you see!
      value: "A bug happened!"
    validations:
      required: true
  - type: textarea
    id: version
    attributes:
      label: Version
      description: What version of our software are you running (if known)?
      default: main
      value: "version"
    validations:
      required: true
  - type: textarea
    id: logs
    attributes:
      label: Relevant log output
      description: Please copy and paste any relevant log output. This will be automatically formatted into code, so no need for backticks.
      render: shell
