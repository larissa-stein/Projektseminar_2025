import os
import sys
from src.main import main

if __name__ == "__main__":
    """
    Entry point to start the dashboard when running the project from the root directory.

    This script was created because the main application code was moved into the `src/` folder.
    After this change, the original `main.py` could no longer be executed directly from the project root
    without causing issues with relative paths and Python imports.

    Additionally, moving the code into `src/` was necessary to make automatic linking in the Sphinx
    documentation work correctly. Without this structure, Sphinx could not properly import and
    document modules like `src.main`.

    This script solves both problems:
    1. It allows the dashboard to be launched from the root folder.
    2. It supports clean module paths for documentation and development.

    When executed, it switches the working directory to `src/` and calls the `main()` function
    from `src/main.py`.
    """

    # Set working directory to src/ before execution
    os.chdir(os.path.join(os.path.dirname(__file__), "src"))
    main()