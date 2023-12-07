import logging
import subprocess
import os


class OpenFace:
    """Class for running OpenFace as an external process."""

    def __init__(self, port: int):
        try:
            self._logger = logging.getLogger("OpenFace")
            # Adjust environment variables for better performance
            env = os.environ.copy()
            env["OMP_NUM_THREADS"] = "1"
            env["VECLIB_MAXIMUM_THREADS"] = "1"

            self._openface_process = subprocess.Popen(
                [
                    os.path.join(
                        os.path.dirname(
                            os.path.dirname(
                                os.path.dirname(
                                    os.path.dirname(
                                        os.path.dirname(os.path.abspath(__file__))
                                    )
                                )
                            )
                        ),
                        "experimental-hub-openface",
                        "build",
                        "bin",
                        "AUExtractor",
                    ),
                    f"{port}",
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
        except Exception as error:
            self._logger.error(f"Error running OwnExtractor. Port: {port}. Exception: {error}")

    def __del__(self):
        try:
            self._openface_process.terminate()
        except Exception:
            self._openface_process.kill()
