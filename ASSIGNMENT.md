# Assignment: FDE Take-Home Exercise

## Title

Creative Automation for Social Campaigns

## Context

This take-home exercise is for the Adobe Forward Deployed AI Engineer interview process.

The goal is to build a proof-of-concept creative automation pipeline for scalable social ad campaigns.

## Scenario

A global consumer goods company launches hundreds of localized social ad campaigns every month.

The client wants to enable its creative team to generate variations of campaign assets more efficiently using GenAI.

## Objective

Design and implement a creative automation pipeline that enables the creative team to generate campaign asset variations.

The POC should focus on the GenAI content automation pipeline rather than building a complex dashboard or analytics product.

## Data Sources

The system may use the following data sources:

* User inputs: campaign briefs and manually uploaded assets
* Storage: local storage, cloud storage, or mock storage for generated and transient assets
* GenAI: suitable APIs or models for generating hero images, resized images, and localized creative variations

## Guidelines

* Build a simple POC centered on the GenAI content automation pipeline.
* A fancy dashboard, complex UI, and performance analytics are not required.
* Be prepared to explain how the solution could be scaled to an enterprise-level system.
* Evaluation will focus on:

  * problem solving
  * strategy
  * design patterns
  * core GenAI coding
  * quality of generated content and images
* There is no required model or service. The implementation can use any reasonable model, API, or mock service.

## Task 1: Build a Creative Automation Pipeline

### Time Expectation

Plan to spend approximately 3–4 hours maximum on the POC.

### Goal

Demonstrate a working proof-of-concept that automates creative asset generation for social ad campaigns using GenAI.

The implementation should show technical approach, problem solving, and the ability to integrate creative technologies.

## Minimum Requirements

The solution must:

1. Accept a campaign brief in JSON, YAML, or another reasonable format.

2. The campaign brief should include:

   * at least two products
   * target region or market
   * target audience
   * campaign message

3. Accept input assets.

   * Assets may be stored in a local folder or mock storage.
   * Existing assets should be reused when available.

4. Generate new assets when required.

   * If product assets are missing, generate new ones using a GenAI image model or a mock generator.

5. Produce creatives for at least three aspect ratios.

   * Example aspect ratios:

     * 1:1
     * 9:16
     * 16:9

6. Display the campaign message on the final campaign posts.

   * English is required.
   * Localized text is a plus.

7. Run locally.

   * A command-line tool or simple local app is acceptable.
   * Any language or framework may be used.

8. Save generated outputs to a clearly organized folder structure.

   * Outputs should be organized by product and aspect ratio.

9. Include basic documentation.

   * The README should explain:

     * how to run the project
     * example input and output
     * key design decisions
     * assumptions and limitations

## Nice-to-Have Features

The following are optional:

1. Brand compliance checks

   * Example: logo presence, brand color usage, required elements

2. Simple legal content checks

   * Example: flag prohibited words or risky claims

3. Logging or reporting of results

   * Example: output paths, generation status, warnings, and validation results

## Interview Structure

The interview includes:

1. Technical code presentation and live demo/edit with engineers

   * Approximately 30–35 minutes

2. Foundational technical questions

   * Approximately 10–15 minutes
   * These may or may not be directly related to the deliverable

3. Candidate questions

   * Approximately 5–10 minutes

## Submission

The deliverables should be submitted to the Talent Partner at least one day before the scheduled interview.

Expected deliverables:

* working code
* README
* generated output examples
* presentation material
* short demo recording showing how to run the app locally

## My Interpretation

The final campaign posts are interpreted as review-ready social creative outputs.

They are not necessarily automatically published to social media platforms. In a production environment, they would go through brand review, legal review, and approval workflow before being exported to downstream campaign management tools.

## Implementation Direction

For this POC, the recommended implementation is:

* Python CLI
* YAML campaign brief
* local input assets
* local output folder
* Pillow-based rendering layer
* mock image generator as the default mode
* optional real image generation provider
* simple rule-based compliance checks
* JSON report output

## Key Design Principles

* Keep the implementation simple and explainable.
* Prioritize a reliable end-to-end pipeline over a complex UI.
* Separate the image generation provider from the core pipeline logic.
* Make the demo reproducible without external API dependencies.
* Design the system so that Adobe Firefly Services or another enterprise-approved provider could be integrated later.
* Clearly document assumptions and limitations.
