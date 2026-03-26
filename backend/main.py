import sys
import uvicorn


def _ensure_utf8_stdout() -> None:
    if sys.platform == "win32" and sys.stdout.encoding != "utf-8":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")


def main() -> None:
    _ensure_utf8_stdout()
    uvicorn.run("app.main:app", host="0.0.0.0", port=5001, reload=True)


if __name__ == "__main__":
    main()
