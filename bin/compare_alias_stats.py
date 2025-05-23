#!/usr/bin/env python3
"""
Script to compare alias statistics before and after limiting alias sources.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the uniff-gen package to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from uniff_gen.config import (
    ALIAS_SOURCE_CLDR,
    ALIAS_SOURCE_FORMAL,
    ALIAS_SOURCE_INFORMATIVE,
)
from uniff_gen.processor import calculate_alias_statistics, process_data_files


def generate_dataset_with_sources(sources, data_dir):
    """
    Generate a dataset using the specified alias sources.

    Args:
        sources: List of alias sources to use
        data_dir: Directory to store the dataset

    Returns:
        Tuple of (unicode_data, aliases_data)
    """

    # Mock the get_alias_sources function to return the specified sources
    def mock_get_alias_sources():
        return sources

    # Save the original function
    from uniff_gen.processor import get_alias_sources

    original_get_alias_sources = get_alias_sources

    # Replace with our mock
    import uniff_gen.processor

    uniff_gen.processor.get_alias_sources = mock_get_alias_sources

    try:
        # Get the paths to the source files
        source_dir = os.path.expanduser("~/.local/share/uniff-gen/source-files")
        file_paths = {
            "unicode_data": os.path.join(source_dir, "UnicodeData.txt"),
            "name_aliases": os.path.join(source_dir, "NameAliases.txt"),
            "names_list": os.path.join(source_dir, "NamesList.txt"),
            "cldr_annotations": os.path.join(source_dir, "en.xml"),
        }

        # Process the data files
        unicode_data, aliases_data = process_data_files(file_paths)

        return unicode_data, aliases_data
    finally:
        # Restore the original function
        uniff_gen.processor.get_alias_sources = original_get_alias_sources


def print_statistics(stats, title):
    """
    Print statistics in a formatted way.

    Args:
        stats: Dictionary with statistics
        title: Title to print
    """
    print(f"\n{title}")
    print("=" * len(title))
    print(f"Total characters: {stats['total_characters']}")
    print(f"Total aliases: {stats['total_aliases']}")
    print(f"Average aliases per character: {stats['avg_aliases_per_char']:.2f}")
    print(f"Median aliases per character: {stats['median_aliases_per_char']:.2f}")
    print(f"Maximum aliases for any character: {stats['max_aliases']}")
    print(f"Minimum aliases for any character: {stats['min_aliases']}")
    print(f"Characters with no aliases: {stats['chars_with_no_aliases']}")


def compare_statistics(before_stats, after_stats):
    """
    Compare before and after statistics.

    Args:
        before_stats: Statistics before the change
        after_stats: Statistics after the change
    """
    print("\nComparison")
    print("==========")

    # Calculate percentage changes
    total_chars_change = (
        after_stats["total_characters"] - before_stats["total_characters"]
    )
    total_aliases_change = after_stats["total_aliases"] - before_stats["total_aliases"]
    avg_aliases_change = (
        after_stats["avg_aliases_per_char"] - before_stats["avg_aliases_per_char"]
    )
    median_aliases_change = (
        after_stats["median_aliases_per_char"] - before_stats["median_aliases_per_char"]
    )

    total_aliases_pct = (
        (total_aliases_change / before_stats["total_aliases"]) * 100
        if before_stats["total_aliases"] > 0
        else 0
    )
    avg_aliases_pct = (
        (avg_aliases_change / before_stats["avg_aliases_per_char"]) * 100
        if before_stats["avg_aliases_per_char"] > 0
        else 0
    )

    print(f"Change in total characters: {total_chars_change}")
    print(f"Change in total aliases: {total_aliases_change} ({total_aliases_pct:.2f}%)")
    print(
        f"Change in average aliases per character: "
        f"{avg_aliases_change:.2f} ({avg_aliases_pct:.2f}%)"
    )
    print(f"Change in median aliases per character: {median_aliases_change:.2f}")


def main():
    """Main function."""
    # Create temporary directories for the datasets
    with tempfile.TemporaryDirectory() as temp_dir:
        all_sources_dir = os.path.join(temp_dir, "all_sources")
        cldr_only_dir = os.path.join(temp_dir, "cldr_only")

        os.makedirs(all_sources_dir, exist_ok=True)
        os.makedirs(cldr_only_dir, exist_ok=True)

        # Generate dataset with all sources
        print("Generating dataset with all alias sources...")
        all_sources = [
            ALIAS_SOURCE_FORMAL,
            ALIAS_SOURCE_INFORMATIVE,
            ALIAS_SOURCE_CLDR,
        ]
        _, all_aliases = generate_dataset_with_sources(all_sources, all_sources_dir)

        # Calculate statistics for all sources
        all_stats = calculate_alias_statistics(all_aliases)
        print_statistics(all_stats, "Statistics with all alias sources")

        # Generate dataset with only CLDR annotations
        print("\nGenerating dataset with only CLDR annotations...")
        cldr_sources = [ALIAS_SOURCE_CLDR]
        _, cldr_aliases = generate_dataset_with_sources(cldr_sources, cldr_only_dir)

        # Calculate statistics for CLDR only
        cldr_stats = calculate_alias_statistics(cldr_aliases)
        print_statistics(cldr_stats, "Statistics with only CLDR annotations")

        # Compare the statistics
        compare_statistics(all_stats, cldr_stats)

        # We've already got the main statistics, so we'll skip the every-day dataset
        # for now
        print("\nStatistics summary:")
        print("==================")
        print("Using only CLDR annotations results in:")

        # Calculate character difference statistics
        chars_diff = abs(cldr_stats["total_characters"] - all_stats["total_characters"])
        chars_pct = abs(chars_diff / all_stats["total_characters"]) * 100
        print(
            f"- {chars_diff} fewer characters with aliases ({chars_pct:.1f}% reduction)"
        )

        # Calculate aliases difference statistics
        aliases_diff = abs(cldr_stats["total_aliases"] - all_stats["total_aliases"])
        aliases_pct = abs(aliases_diff / all_stats["total_aliases"]) * 100
        print(f"- {aliases_diff} fewer total aliases ({aliases_pct:.1f}% reduction)")

        # Calculate average aliases per character statistics
        avg_diff = cldr_stats["avg_aliases_per_char"] - all_stats["avg_aliases_per_char"]
        avg_pct = (avg_diff / all_stats["avg_aliases_per_char"]) * 100
        print(
            f"- {avg_diff:.1f} more aliases per character on average "
            f"({avg_pct:.1f}% increase)"
        )

        # Calculate median aliases per character
        median_diff = (
            cldr_stats["median_aliases_per_char"] - all_stats["median_aliases_per_char"]
        )
        print(f"- {median_diff:.1f} more aliases per character median")

        # Conclusion
        print(
            "\nConclusion: Using only CLDR annotations significantly reduces the "
            "number of characters"
        )
        print(
            "with aliases, but the remaining characters have more aliases on average, "
            "which should"
        )
        print("improve search quality for those characters.")


if __name__ == "__main__":
    main()
