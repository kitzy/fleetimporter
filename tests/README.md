# FleetImporter Tests

This directory contains test scripts to validate that all recipes comply with the style guide requirements defined in [CONTRIBUTING.md](../CONTRIBUTING.md).

## Test Files

### `test_style_guide_compliance.py`

Validates that all recipe files comply with the style guide requirements:

- ✅ **YAML syntax** is valid (proper YAML formatting)
- ✅ **Required AutoPkg fields** present (`Description`, `Identifier`, `Input`, `Process`)
- ✅ Filename conventions (`.fleet.direct.recipe.yaml` or `.fleet.gitops.recipe.yaml`)
- ✅ Vendor folder structure (no spaces in folder names, proper organization)
- ✅ Identifier patterns (`com.github.fleet.direct.<Name>` or `com.github.fleet.gitops.<Name>`)
- ✅ Single processor stage (FleetImporter only)
- ✅ `NAME` variable exists in all recipes
- ✅ `SELF_SERVICE` must be set to `true` in all recipes
- ✅ `AUTOMATIC_INSTALL` must be set to `false` in all recipes  
- ✅ `FLEET_GITOPS_SOFTWARE_DIR` must be set to `lib/macos/software` in GitOps recipes
- ✅ `FLEET_GITOPS_TEAM_YAML_PATH` must be set to `teams/workstations.yml` in GitOps recipes
- ✅ Categories use only supported Fleet values: `Browsers`, `Communication`, `Developer tools`, `Productivity`
- ✅ All Process arguments properly reference Input variables (`%VARIABLE%` format)

## Running Tests Locally

### Prerequisites

```bash
python3 -m pip install PyYAML
```

### Run Style Guide Compliance Test

```bash
python3 tests/test_style_guide_compliance.py
```

### Expected Output

When all recipes comply with the style guide:

```
=== Style Guide Compliance Validation ===
Found 38 recipe files to validate

📋 Validating: AgileBits/1Password8.fleet.direct.recipe.yaml
   ✅ Filename convention: 1Password8.fleet.direct.recipe.yaml (direct mode)
   ✅ Vendor folder: AgileBits
   ✅ YAML syntax: Valid
   ✅ Required fields: All present (Description, Identifier, Input, Process)
   ✅ Identifier: com.github.fleet.direct.1Password8 (direct mode)
   ✅ Process stages: 1 (single processor)
   ✅ Processor type: com.github.fleet.FleetImporter/FleetImporter
   ✅ NAME: 1Password 8
   ✅ SELF_SERVICE: true
   ✅ AUTOMATIC_INSTALL: false
   ✅ CATEGORIES: ['Productivity']
   ✅ Process self_service: '%SELF_SERVICE%'
   ✅ Process automatic_install: '%AUTOMATIC_INSTALL%'
   ✅ Validation complete

[... more recipes ...]

======================================================================
Style Guide Compliance Report
======================================================================

📊 Statistics:
   Total recipes validated: 38
   Direct mode recipes: 19
   GitOps mode recipes: 19

🔍 Validation Results:
   Errors: 0
   Warnings: 0

✅ All recipes comply with the style guide!

Validated requirements:
   ✅ Filename conventions (.fleet.direct/gitops.recipe.yaml)
   ✅ Vendor folder structure (no spaces, proper organization)
   ✅ Identifier patterns (com.github.fleet.direct/gitops.<Name>)
   ✅ Single processor stage (FleetImporter)
   ✅ NAME variable exists in all recipes
   ✅ SELF_SERVICE set to true in all recipes
   ✅ AUTOMATIC_INSTALL set to false in all recipes
   ✅ FLEET_GITOPS_SOFTWARE_DIR set to 'lib/macos/software' in GitOps recipes
   ✅ FLEET_GITOPS_TEAM_YAML_PATH set to 'teams/workstations.yml' in GitOps recipes
   ✅ Categories use only supported values (when specified)
   ✅ All Process arguments reference Input variables correctly
```

## CI/CD Integration

These tests are automatically run in GitHub Actions on every pull request via the `.github/workflows/validate.yml` workflow.

The style guide compliance test is one of several validation checks that must pass before a PR can be merged:

- Python processor validation
- Environment variable validation
- Recipe structure validation
- Security and best practices check
- Integration test
- **Style guide compliance (includes YAML validation)** ← This test

## Adding New Style Guide Requirements

When adding new requirements to the style guide:

1. Update `CONTRIBUTING.md` with the new requirement
2. Add validation logic to `test_style_guide_compliance.py`
3. Update all existing recipes to comply with the new requirement
4. Run the test locally to verify: `python3 tests/test_style_guide_compliance.py`
5. Commit all changes together

## Troubleshooting

### Test Fails with "Missing SELF_SERVICE"

Ensure the recipe has `SELF_SERVICE: true` in the `Input` section and `self_service: "%SELF_SERVICE%"` in the Process arguments.

### Test Fails with "Missing AUTOMATIC_INSTALL"

Ensure the recipe has `AUTOMATIC_INSTALL: false` in the `Input` section and `automatic_install: "%AUTOMATIC_INSTALL%"` in the Process arguments.

### Test Fails with GitOps Path Errors

For GitOps recipes (`.gitops.` in filename), ensure:
- `FLEET_GITOPS_SOFTWARE_DIR: lib/macos/software` in Input section
- `FLEET_GITOPS_TEAM_YAML_PATH: teams/workstations.yml` in Input section
- Both values referenced in Process arguments

### Test Fails with Invalid Categories

Ensure categories use only Fleet-supported values:
- `Browsers`
- `Communication`
- `Developer tools`
- `Productivity`

Categories are case-sensitive and must match exactly.

## Exit Codes

- `0`: All tests passed
- `1`: One or more tests failed (see error output for details)
