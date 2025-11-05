#!/usr/bin/env python3
"""
Test suite to validate that all recipes comply with the style guide requirements
defined in CONTRIBUTING.md.

This validates:
1. Filename conventions (.fleet.direct. or .fleet.gitops.)
2. Identifier patterns (com.github.fleet.direct/gitops.<SoftwareName>)
3. Single processor stage (FleetImporter only)
4. NAME variable exists in Input section
5. SELF_SERVICE must be set to true
6. AUTOMATIC_INSTALL must be set to false
7. FLEET_GITOPS_SOFTWARE_DIR must be set to "lib/macos/software" (GitOps)
8. FLEET_GITOPS_TEAM_YAML_PATH must be set to "teams/workstations.yml" (GitOps)
9. Categories use only supported values
10. Process arguments reference Input variables correctly
11. Vendor folder structure
"""

import glob
import os
import sys
import yaml
from pathlib import Path


class StyleGuideValidator:
    """Validates recipe files against style guide requirements."""

    # Supported Fleet categories from style guide
    SUPPORTED_CATEGORIES = {
        "Browsers",
        "Communication",
        "Developer tools",
        "Productivity",
    }

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.recipe_count = 0
        self.direct_count = 0
        self.gitops_count = 0

    def validate_all_recipes(self):
        """Find and validate all recipe files."""
        recipe_files = glob.glob("**/*.recipe.yaml", recursive=True)
        # Exclude FleetImporter directory
        recipe_files = [f for f in recipe_files if "FleetImporter" not in f]

        print(f"=== Style Guide Compliance Validation ===")
        print(f"Found {len(recipe_files)} recipe files to validate\n")

        for recipe_file in sorted(recipe_files):
            self.validate_recipe(recipe_file)

        return self.report_results()

    def validate_recipe(self, recipe_path):
        """Validate a single recipe file."""
        self.recipe_count += 1
        print(f"📋 Validating: {recipe_path}")

        # Validate filename convention
        self.validate_filename(recipe_path)

        # Validate vendor folder structure
        self.validate_vendor_folder(recipe_path)

        # Parse YAML and validate syntax
        try:
            with open(recipe_path, "r") as f:
                data = yaml.safe_load(f)
            print(f"   ✅ YAML syntax: Valid")
        except yaml.YAMLError as e:
            self.errors.append(f"{recipe_path}: YAML syntax error - {e}")
            print(f"   ❌ YAML syntax: Invalid - {e}")
            return
        except Exception as e:
            self.errors.append(f"{recipe_path}: Failed to parse YAML - {e}")
            print(f"   ❌ YAML parsing: Failed - {e}")
            return

        # Validate required AutoPkg recipe fields
        self.validate_required_fields(recipe_path, data)

        # Determine recipe mode from filename
        is_gitops = ".gitops." in recipe_path
        is_direct = ".direct." in recipe_path

        if is_gitops:
            self.gitops_count += 1
        elif is_direct:
            self.direct_count += 1

        # Validate identifier pattern
        self.validate_identifier(recipe_path, data, is_gitops, is_direct)

        # Validate single processor stage
        self.validate_single_processor(recipe_path, data)

        # Validate Input section
        input_section = data.get("Input", {})
        if not input_section:
            self.errors.append(f"{recipe_path}: Missing Input section")
            return

        # Validate NAME exists
        self.validate_name(recipe_path, input_section)

        # Validate SELF_SERVICE requirement
        self.validate_self_service(recipe_path, input_section)

        # Validate AUTOMATIC_INSTALL requirement
        self.validate_automatic_install(recipe_path, input_section)

        # Validate GitOps-specific requirements
        if is_gitops:
            self.validate_gitops_software_dir(recipe_path, input_section)
            self.validate_gitops_team_yaml_path(recipe_path, input_section)

        # Validate categories (if present)
        self.validate_categories(recipe_path, input_section)

        # Validate Process section arguments
        process_list = data.get("Process", [])
        if process_list and len(process_list) > 0:
            args = process_list[0].get("Arguments", {})
            self.validate_process_arguments(recipe_path, args, is_gitops)

        print(f"   ✅ Validation complete\n")

    def validate_filename(self, recipe_path):
        """Validate filename follows convention: <SoftwareName>.fleet.(direct|gitops).recipe.yaml"""
        filename = os.path.basename(recipe_path)

        if not (filename.endswith(".fleet.direct.recipe.yaml") or filename.endswith(".fleet.gitops.recipe.yaml")):
            self.errors.append(
                f"{recipe_path}: Filename must end with .fleet.direct.recipe.yaml or .fleet.gitops.recipe.yaml"
            )
            print(f"   ❌ Filename convention: Invalid (must be .fleet.direct/gitops.recipe.yaml)")
        else:
            mode = "direct" if ".fleet.direct." in filename else "gitops"
            print(f"   ✅ Filename convention: {filename} ({mode} mode)")

    def validate_vendor_folder(self, recipe_path):
        """Validate recipe is in a vendor folder (not at root)."""
        path_parts = recipe_path.split(os.sep)
        
        # Should be VendorName/RecipeFile.yaml, so at least 2 parts
        if len(path_parts) < 2:
            self.errors.append(
                f"{recipe_path}: Recipe must be in a vendor folder (e.g., VendorName/Recipe.yaml)"
            )
            print(f"   ❌ Vendor folder: Recipe at root (must be in vendor subfolder)")
        else:
            vendor_folder = path_parts[-2]
            # Check for spaces in folder name
            if " " in vendor_folder:
                self.errors.append(
                    f"{recipe_path}: Vendor folder '{vendor_folder}' contains spaces"
                )
                print(f"   ❌ Vendor folder: '{vendor_folder}' (no spaces allowed)")
            else:
                print(f"   ✅ Vendor folder: {vendor_folder}")

    def validate_required_fields(self, recipe_path, data):
        """Validate required AutoPkg recipe fields exist."""
        required_fields = ["Description", "Identifier", "Input", "Process"]
        missing = [field for field in required_fields if field not in data]
        
        if missing:
            self.errors.append(
                f"{recipe_path}: Missing required AutoPkg fields: {missing}"
            )
            print(f"   ❌ Required fields: Missing {missing}")
        else:
            print(f"   ✅ Required fields: All present (Description, Identifier, Input, Process)")

    def validate_identifier(self, recipe_path, data, is_gitops, is_direct):
        """Validate identifier follows pattern: com.github.fleet.(direct|gitops).<SoftwareName>"""
        identifier = data.get("Identifier", "")
        
        if not identifier:
            self.errors.append(f"{recipe_path}: Missing Identifier field")
            print(f"   ❌ Identifier: Missing")
            return

        expected_prefix = "com.github.fleet."
        if not identifier.startswith(expected_prefix):
            self.errors.append(
                f"{recipe_path}: Identifier must start with '{expected_prefix}', got '{identifier}'"
            )
            print(f"   ❌ Identifier: '{identifier}' (must start with '{expected_prefix}')")
            return

        # Check mode matches filename
        has_direct_id = ".direct." in identifier
        has_gitops_id = ".gitops." in identifier

        if is_direct and not has_direct_id:
            self.errors.append(
                f"{recipe_path}: Direct recipe identifier must contain '.direct.', got '{identifier}'"
            )
            print(f"   ❌ Identifier: '{identifier}' (must contain '.direct.' for direct mode)")
        elif is_gitops and not has_gitops_id:
            self.errors.append(
                f"{recipe_path}: GitOps recipe identifier must contain '.gitops.', got '{identifier}'"
            )
            print(f"   ❌ Identifier: '{identifier}' (must contain '.gitops.' for gitops mode)")
        else:
            mode = "direct" if has_direct_id else "gitops"
            print(f"   ✅ Identifier: {identifier} ({mode} mode)")

    def validate_single_processor(self, recipe_path, data):
        """Validate recipe has single processor stage: FleetImporter."""
        process_list = data.get("Process", [])
        
        if not process_list:
            self.errors.append(f"{recipe_path}: Missing Process section")
            print(f"   ❌ Process section: Missing")
            return

        if len(process_list) != 1:
            self.warnings.append(
                f"{recipe_path}: Process has {len(process_list)} processors (style guide recommends single FleetImporter processor)"
            )
            print(f"   ⚠️  Process stages: {len(process_list)} (style guide recommends 1)")
        else:
            print(f"   ✅ Process stages: 1 (single processor)")

        # Check that FleetImporter is present
        has_fleet_importer = False
        for item in process_list:
            if isinstance(item, dict):
                processor = item.get("Processor", "")
                if "FleetImporter" in processor:
                    has_fleet_importer = True
                    print(f"   ✅ Processor type: {processor}")
                    break

        if not has_fleet_importer:
            self.errors.append(f"{recipe_path}: FleetImporter processor not found in Process")
            print(f"   ❌ Processor type: FleetImporter not found")

    def validate_name(self, recipe_path, input_section):
        """Validate NAME variable exists in Input section."""
        name = input_section.get("NAME")
        
        if name is None:
            self.errors.append(f"{recipe_path}: Missing NAME in Input section")
            print(f"   ❌ NAME: Missing (required)")
        else:
            print(f"   ✅ NAME: {name}")

    def validate_categories(self, recipe_path, input_section):
        """Validate categories use only supported values."""
        categories = input_section.get("CATEGORIES", [])
        
        if not categories:
            # Categories are optional, just note it
            print(f"   ℹ️  CATEGORIES: None specified (optional)")
            return

        invalid_categories = []
        for category in categories:
            if category not in self.SUPPORTED_CATEGORIES:
                invalid_categories.append(category)

        if invalid_categories:
            self.errors.append(
                f"{recipe_path}: Invalid categories {invalid_categories}. "
                f"Must be one of: {sorted(self.SUPPORTED_CATEGORIES)}"
            )
            print(f"   ❌ CATEGORIES: {categories} (invalid: {invalid_categories})")
        else:
            print(f"   ✅ CATEGORIES: {categories}")

    def validate_self_service(self, recipe_path, input_section):
        """Validate SELF_SERVICE is set to true."""
        self_service = input_section.get("SELF_SERVICE")

        if self_service is None:
            self.errors.append(
                f"{recipe_path}: Missing SELF_SERVICE in Input section"
            )
            print(f"   ❌ SELF_SERVICE: Missing (required)")
        elif self_service is not True:
            self.errors.append(
                f"{recipe_path}: SELF_SERVICE must be set to true, got {self_service}"
            )
            print(f"   ❌ SELF_SERVICE: {self_service} (must be true)")
        else:
            print(f"   ✅ SELF_SERVICE: true")

    def validate_automatic_install(self, recipe_path, input_section):
        """Validate AUTOMATIC_INSTALL is set to false."""
        automatic_install = input_section.get("AUTOMATIC_INSTALL")

        if automatic_install is None:
            self.errors.append(
                f"{recipe_path}: Missing AUTOMATIC_INSTALL in Input section"
            )
            print(f"   ❌ AUTOMATIC_INSTALL: Missing (required)")
        elif automatic_install is not False:
            self.errors.append(
                f"{recipe_path}: AUTOMATIC_INSTALL must be set to false, got {automatic_install}"
            )
            print(f"   ❌ AUTOMATIC_INSTALL: {automatic_install} (must be false)")
        else:
            print(f"   ✅ AUTOMATIC_INSTALL: false")

    def validate_gitops_software_dir(self, recipe_path, input_section):
        """Validate FLEET_GITOPS_SOFTWARE_DIR is set to 'lib/macos/software'."""
        software_dir = input_section.get("FLEET_GITOPS_SOFTWARE_DIR")
        expected = "lib/macos/software"

        if software_dir is None:
            self.errors.append(
                f"{recipe_path}: Missing FLEET_GITOPS_SOFTWARE_DIR in Input section"
            )
            print(f"   ❌ FLEET_GITOPS_SOFTWARE_DIR: Missing (required for GitOps)")
        elif software_dir != expected:
            self.errors.append(
                f"{recipe_path}: FLEET_GITOPS_SOFTWARE_DIR must be '{expected}', got '{software_dir}'"
            )
            print(
                f"   ❌ FLEET_GITOPS_SOFTWARE_DIR: '{software_dir}' (must be '{expected}')"
            )
        else:
            print(f"   ✅ FLEET_GITOPS_SOFTWARE_DIR: '{expected}'")

    def validate_gitops_team_yaml_path(self, recipe_path, input_section):
        """Validate FLEET_GITOPS_TEAM_YAML_PATH is set to 'teams/workstations.yml'."""
        team_yaml_path = input_section.get("FLEET_GITOPS_TEAM_YAML_PATH")
        expected = "teams/workstations.yml"

        if team_yaml_path is None:
            self.errors.append(
                f"{recipe_path}: Missing FLEET_GITOPS_TEAM_YAML_PATH in Input section"
            )
            print(f"   ❌ FLEET_GITOPS_TEAM_YAML_PATH: Missing (required for GitOps)")
        elif team_yaml_path != expected:
            self.errors.append(
                f"{recipe_path}: FLEET_GITOPS_TEAM_YAML_PATH must be '{expected}', got '{team_yaml_path}'"
            )
            print(
                f"   ❌ FLEET_GITOPS_TEAM_YAML_PATH: '{team_yaml_path}' (must be '{expected}')"
            )
        else:
            print(f"   ✅ FLEET_GITOPS_TEAM_YAML_PATH: '{expected}'")

    def validate_process_arguments(self, recipe_path, args, is_gitops):
        """Validate Process section arguments reference Input variables correctly."""
        # Check self_service argument
        self_service_arg = args.get("self_service")
        if self_service_arg != "%SELF_SERVICE%":
            self.errors.append(
                f"{recipe_path}: Process argument 'self_service' must be '%SELF_SERVICE%', got '{self_service_arg}'"
            )
            print(
                f"   ❌ Process self_service: '{self_service_arg}' (must be '%SELF_SERVICE%')"
            )
        else:
            print(f"   ✅ Process self_service: '%SELF_SERVICE%'")

        # Check automatic_install argument
        automatic_install_arg = args.get("automatic_install")
        if automatic_install_arg != "%AUTOMATIC_INSTALL%":
            self.errors.append(
                f"{recipe_path}: Process argument 'automatic_install' must be '%AUTOMATIC_INSTALL%', got '{automatic_install_arg}'"
            )
            print(
                f"   ❌ Process automatic_install: '{automatic_install_arg}' (must be '%AUTOMATIC_INSTALL%')"
            )
        else:
            print(f"   ✅ Process automatic_install: '%AUTOMATIC_INSTALL%'")

        # Check GitOps-specific Process arguments
        if is_gitops:
            software_dir_arg = args.get("gitops_software_dir")
            if software_dir_arg != "%FLEET_GITOPS_SOFTWARE_DIR%":
                self.errors.append(
                    f"{recipe_path}: Process argument 'gitops_software_dir' must be '%FLEET_GITOPS_SOFTWARE_DIR%', got '{software_dir_arg}'"
                )
                print(
                    f"   ❌ Process gitops_software_dir: '{software_dir_arg}' (must be '%FLEET_GITOPS_SOFTWARE_DIR%')"
                )
            else:
                print(
                    f"   ✅ Process gitops_software_dir: '%FLEET_GITOPS_SOFTWARE_DIR%'"
                )

            team_yaml_path_arg = args.get("gitops_team_yaml_path")
            if team_yaml_path_arg != "%FLEET_GITOPS_TEAM_YAML_PATH%":
                self.errors.append(
                    f"{recipe_path}: Process argument 'gitops_team_yaml_path' must be '%FLEET_GITOPS_TEAM_YAML_PATH%', got '{team_yaml_path_arg}'"
                )
                print(
                    f"   ❌ Process gitops_team_yaml_path: '{team_yaml_path_arg}' (must be '%FLEET_GITOPS_TEAM_YAML_PATH%')"
                )
            else:
                print(
                    f"   ✅ Process gitops_team_yaml_path: '%FLEET_GITOPS_TEAM_YAML_PATH%'"
                )

    def report_results(self):
        """Print final validation report and return exit code."""
        print("\n" + "=" * 70)
        print("Style Guide Compliance Report")
        print("=" * 70)
        print(f"\n📊 Statistics:")
        print(f"   Total recipes validated: {self.recipe_count}")
        print(f"   Direct mode recipes: {self.direct_count}")
        print(f"   GitOps mode recipes: {self.gitops_count}")
        print(f"\n🔍 Validation Results:")
        print(f"   Errors: {len(self.errors)}")
        print(f"   Warnings: {len(self.warnings)}")

        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   • {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ All recipes comply with the style guide!")
            print("\nValidated requirements:")
            print("   ✅ YAML syntax is valid")
            print("   ✅ Required AutoPkg fields present (Description, Identifier, Input, Process)")
            print("   ✅ Filename conventions (.fleet.direct/gitops.recipe.yaml)")
            print("   ✅ Vendor folder structure (no spaces, proper organization)")
            print("   ✅ Identifier patterns (com.github.fleet.direct/gitops.<Name>)")
            print("   ✅ Single processor stage (FleetImporter)")
            print("   ✅ NAME variable exists in all recipes")
            print("   ✅ SELF_SERVICE set to true in all recipes")
            print("   ✅ AUTOMATIC_INSTALL set to false in all recipes")
            print(
                "   ✅ FLEET_GITOPS_SOFTWARE_DIR set to 'lib/macos/software' in GitOps recipes"
            )
            print(
                "   ✅ FLEET_GITOPS_TEAM_YAML_PATH set to 'teams/workstations.yml' in GitOps recipes"
            )
            print("   ✅ Categories use only supported values (when specified)")
            print("   ✅ All Process arguments reference Input variables correctly")
            return 0
        elif self.errors:
            print("\n❌ Style guide compliance validation FAILED")
            print("\nPlease fix the errors listed above.")
            return 1
        else:
            print("\n⚠️  Style guide compliance validation completed with warnings")
            return 0


def main():
    """Main entry point."""
    validator = StyleGuideValidator()
    exit_code = validator.validate_all_recipes()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
