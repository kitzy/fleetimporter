#!/usr/bin/env python3
"""
Script to add auto-update policy inputs to all existing Fleet recipes.
This ensures backward compatibility while enabling the new feature.
"""

import os
import re
from pathlib import Path

# Define the recipe directories to update (exclude _templates)
RECIPE_DIRS = [
    "AgileBits",
    "Anthropic",
    "AutoPkg",
    "Caffeine",
    "Docker",
    "GitHub",
    "Google",
    "GPGSuite",
    "iTerm2",
    "Microsoft",
    "Mozilla",
    "NorthPoleSecurity",
    "Notion",
    "Postman",
    "RaycastTechnologies",
    "Signal",
    "Slack",
    "UTM",
    "Zoom",
]

# Patterns to find and update
INPUT_PATTERN = re.compile(
    r"(  # Mode selector\n  gitops_mode: false)",
    re.MULTILINE
)

INPUT_REPLACEMENT = r"""  # Optional: Auto-update policy automation
  AUTO_UPDATE_ENABLED: false
  AUTO_UPDATE_POLICY_NAME: "autopkg-auto-update-%NAME%"

\1"""

ARGS_PATTERN = re.compile(
    r"(    # GitOps-specific options\n    gitops_software_dir: \"%FLEET_GITOPS_SOFTWARE_DIR%\")",
    re.MULTILINE
)

ARGS_REPLACEMENT = r"""    # Optional: Auto-update policy automation
    auto_update_enabled: "%AUTO_UPDATE_ENABLED%"
    auto_update_policy_name: "%AUTO_UPDATE_POLICY_NAME%"

\1"""


def update_recipe(recipe_path):
    """Update a single recipe file with auto-update inputs."""
    with open(recipe_path, 'r') as f:
        content = f.read()
    
    # Check if already updated
    if "AUTO_UPDATE_ENABLED" in content:
        print(f"  ✓ Already updated: {recipe_path.name}")
        return False
    
    # Update Input section
    content = INPUT_PATTERN.sub(INPUT_REPLACEMENT, content)
    
    # Update Arguments section
    content = ARGS_PATTERN.sub(ARGS_REPLACEMENT, content)
    
    # Write back
    with open(recipe_path, 'w') as f:
        f.write(content)
    
    print(f"  ✓ Updated: {recipe_path.name}")
    return True


def main():
    """Update all recipe files."""
    repo_root = Path(__file__).parent
    updated_count = 0
    skipped_count = 0
    
    print("Updating Fleet recipes with auto-update policy inputs...\n")
    
    for recipe_dir in RECIPE_DIRS:
        dir_path = repo_root / recipe_dir
        if not dir_path.exists():
            print(f"⚠ Directory not found: {recipe_dir}")
            continue
        
        # Find all .fleet.recipe.yaml files in the directory
        recipe_files = list(dir_path.glob("*.fleet.recipe.yaml"))
        
        if not recipe_files:
            print(f"⚠ No recipes found in: {recipe_dir}")
            continue
        
        print(f"Processing {recipe_dir}/")
        for recipe_file in recipe_files:
            if update_recipe(recipe_file):
                updated_count += 1
            else:
                skipped_count += 1
    
    print(f"\n✅ Complete! Updated {updated_count} recipes, skipped {skipped_count}")


if __name__ == "__main__":
    main()
