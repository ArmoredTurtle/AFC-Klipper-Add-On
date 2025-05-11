name: Feature Request
description: Request a new feature.
title: "[Enhancement]: "
labels: ["enhancement", "triage"]
projects: ["ArmoredTurtle/AFC-Klipper-Add-On"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for taking the time to fill out this feature request!
  - type: textarea
    id: requested-feature
    attributes:
      label: What are you looking to see?
      description: Please give us a detailed explanation of what you would like to see!
      placeholder: Tell us what you see!
      value: "I have a feature request"
    validations:
      required: true
  - type: textarea
    id: why
    attributes:
      label: Why do you want this feature?
      description: What will this feature do or how will it improve the experience for all users?
      placeholder: I want this feature because...
      value: "I think it is a good idea because..."
    validations:
      required: true
  - type: textarea
    id: other
    attributes:
      label: Any other input or comments should go here.
      description: Please copy and paste any relevant log output. This will be automatically formatted into code, so no need for backticks.
