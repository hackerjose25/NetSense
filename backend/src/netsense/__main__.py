"""Start the React dashboard and API on the local computer."""

import sys

from netsense.config import FRONTEND_DIST


def main():
    if not (FRONTEND_DIST / "index.html").is_file():
        sys.exit("Frontend not built. Run: npm --prefix frontend ci && npm --prefix frontend run build")
    import uvicorn
    uvicorn.run("netsense.api:app", host="127.0.0.1", port=8000, workers=1)


if __name__ == "__main__":
    main()
