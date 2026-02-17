# SPDX-License-Identifier: Apache-2.0
from jcapy.core.base import CommandBase
import re

class GrepCommand(CommandBase):
    """Filters input based on a pattern."""
    name = "grep"
    description = "Filter piped text or lines from a file"

    def setup_parser(self, parser):
        parser.add_argument("pattern", help="Regex pattern to match")
        parser.add_argument("-i", "--ignore-case", action="store_true", help="Case-insensitive matching")

    def execute(self, args):
        pattern = args.pattern
        flags = re.IGNORECASE if args.ignore_case else 0

        # Priority: Piped data
        content = getattr(args, 'piped_data', None)

        if not content:
            return "No piped data provided to grep."

        lines = content.splitlines()
        matches = [line for line in lines if re.search(pattern, line, flags)]

        if not matches:
            return "" # Return empty so subsequent pipes get nothing

        return "\n".join(matches)
